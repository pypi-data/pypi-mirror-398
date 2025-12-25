# Copyright 2025 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Manage starting and stopping of processes.

This is a simple wrapper around the Python subprocess module that allows
for starting and stopping of processes with Robotics UI.
"""

import dataclasses
import os
import re
import signal
import subprocess
import threading
import time
import types

import psutil

from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui import client
from safari_sdk.workcell import constants
from safari_sdk.workcell import process_watchdog_lib
from safari_sdk.workcell import workcell_errors_lib


def get_process_name(
    process_name: str,
    process_path: str,
) -> str:
  """Returns full path to the process."""
  home_directory = os.path.expanduser(process_path)
  return os.path.join(home_directory, process_name)


def get_y_position(height: float, idx: int) -> float:
  return (1 - height / 2) - height * idx


def to_linux_name(process_name: str) -> str:
  """Converts a process name to a Linux-friendly name (max 15 characters)."""
  return process_name[:15]


def to_local_command(process: str, args: list[str] | None = None) -> str:
  """Returns a bash command to run a process locally."""
  if args is None:
    args = []
  return f"""
  source "{os.path.expanduser("~/.bashrc")}"
  {process} {" ".join(args)};
  """.strip()


def to_citc_command(
    citc_client_name: str, process: str, args: list[str] | None = None
) -> str:
  """Returns a bash command to run a process in a CitC client."""
  if args is None:
    args = []
  return f"""
  hgd -f {citc_client_name};
  hg sync;
  source "{os.path.expanduser("~/.bashrc")}"
  {process} {" ".join(args)};
  bash
  """.strip()


def start_process(command: str) -> subprocess.Popen[str] | None:
  """Starts a process without blocking."""
  subprocess_env = os.environ.copy()
  print(f"subprocess_env: {subprocess_env}")
  try:
    return subprocess.Popen(
        ["bash", "-ic", command],
        executable="/bin/bash",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
  except FileNotFoundError:
    print(f"File not found: {command}")


def start_process_in_terminal(command: str) -> subprocess.Popen[str] | None:
  """Launches a new terminal window on Linux and executes the specified command."""
  return subprocess.Popen(
      [
          "gnome-terminal",
          "--display=:0",
          "-q",
          "--",
          "bash",
          "-ic",
          command,
      ],
      text=True,
  )


def stop_process(
    process_name: str, process_signal: int = signal.SIGINT
) -> None:
  """Stops a process with a given name."""
  print(f"stopping process: {process_name}")
  process_name = to_linux_name(process_name)
  for proc in psutil.process_iter():
    try:
      if process_name in proc.name():
        # Send signal to all child processes first, then to the parent.
        for child in proc.children(recursive=True):
          child.send_signal(process_signal)
          print(f"Sent {process_signal} to {child.name}")
        proc.send_signal(process_signal)
        print(f"Sent {process_signal} to {proc.name}")
    except psutil.NoSuchProcess:
      print("Process not found!")


def stop_process_by_pid(
    process_pid: int, process_signal: int = signal.SIGINT
) -> None:
  """Stops a process with a given PID."""
  print(f"stopping process: {process_pid}")
  try:
    proc = psutil.Process(pid=process_pid)
    # Send signal to all child processes first, then to the parent.
    for child in proc.children(recursive=True):
      child.send_signal(process_signal)
      print(
          f"Sent {process_signal} to child process: {child.name()} (PID:"
          f" {child.pid})"
      )
    proc.send_signal(process_signal)
    print(f"Sent {process_signal} to process: {proc.name()} (PID: {proc.pid})")
  except psutil.NoSuchProcess:
    print(f"Process with PID {process_pid} not found.")


def is_process_running(process_name: str) -> bool:
  """Returns true if the process is running."""
  process_name = to_linux_name(process_name)
  for proc in psutil.process_iter():
    try:
      if process_name in proc.name():
        return True
    except psutil.NoSuchProcess:
      print("Process not found!")
  return False


class ProcessLauncher:
  """Manage starting and stopping of processes."""

  @dataclasses.dataclass
  class ProcessParams:
    """Parameters for starting a process."""

    name: str
    path: str = ""
    args: list[str] | None = None
    start_warning_message: str | None = None
    stop_warning_message: str | None = None
    watchdog: process_watchdog_lib.ProcessWatchdog | None = None
    button_pressed_time: float = 0
    popen_process: subprocess.Popen[str] | None = None
    stdout_thread: threading.Thread | None = None
    stderr_thread: threading.Thread | None = None
    output_to_ui: bool = False
    citc: bool = False
    citc_client_name: str | None = None
    display_name: str | None = None
    is_watchdog_only: bool = False

    def get_button_id(self) -> str:
      return self.name

    def get_start_button_text(self) -> str:
      return f"Start {self.display_name or self.name}"

    def get_stop_button_text(self) -> str:
      return f"Stop {self.display_name or self.name}"

    def get_text_id(self) -> str:
      return f"{self.name}-status"

    def is_process_running(self) -> bool:
      """Returns true if the process is running."""
      if self.popen_process is not None:
        self.watchdog_only = False
        return self.popen_process.poll() is None
      else:
        self.watchdog_only = True
        return is_process_running(self.name)

    def stop_process(self, process_signal: int = signal.SIGINT) -> None:
      """Stops the process."""
      if self.popen_process is not None:
        stop_process_by_pid(self.popen_process.pid, process_signal)
      else:
        stop_process(self.name, process_signal)

  _process_thread: threading.Thread = None
  _process_thread_stop_event: threading.Event = None

  def __init__(
      self,
      robotics_platform: str,
      ui: client.Framework,
      workcell_errors_list: list[
          workcell_errors_lib.WorkcellErrors
      ] = workcell_errors_lib.EMPTY_ERRORS_LIST,
  ):
    self.processes: list[self.ProcessParams] = []
    self.ui: client.Framework = ui
    self.buttons_collapsed: bool = True
    self.buttons_removed: bool = False
    self.buffered_process: self.ProcessParams | None = None
    self.start_buffered_process: bool = False
    self._workcell_errors_list = workcell_errors_list
    self._robotics_platform = robotics_platform
    print(f"robotics_platform: {robotics_platform}")
    self._use_sigkill: bool = False

  def start(self) -> None:
    """Starts the process."""
    signal.signal(signal.SIGCHLD, self._handle_sigchld)
    self._process_thread = threading.Thread(target=self._run_update_process)
    self._process_thread_stop_event = threading.Event()
    self._process_thread.start()

  def stop(self) -> None:
    """Stops the process."""
    if self._process_thread is not None:
      self._process_thread_stop_event.set()
      self._process_thread.join()
      self._process_thread = None
    for process in self.processes:
      self.stop_output_threads(process)
      if process.watchdog:
        process.watchdog.stop()
      if process.citc_client_name:
        start_process(f"hg citc -d {process.citc_client_name}")
    print("Stopping process launcher.")

  def link_process_to_rui(
      self,
      process_name: str,
      process_path: str = "",
      process_args: list[str] | None = None,
      start_warning_message: str | None = None,
      stop_warning_message: str | None = None,
      process_watchdog: process_watchdog_lib.ProcessWatchdog | None = None,
      output_to_ui: bool = False,
      citc: bool = False,
      display_name: str | None = None,
  ) -> None:
    """Links a process to the Robotics UI."""
    process_params = self.ProcessParams(
        name=process_name,
        path=process_path,
        args=process_args,
        watchdog=process_watchdog,
        start_warning_message=start_warning_message,
        stop_warning_message=stop_warning_message,
        output_to_ui=output_to_ui,
        citc=citc,
        display_name=display_name,
    )
    self.processes.append(process_params)

    # Create a button to collapse/expand the process buttons.
    self.ui.create_button(
        constants.PROCESS_COLLAPSE_BUTTON_ID,
        constants.PROCESS_BUTTON_START_X,
        get_y_position(constants.PROCESS_BUTTON_HEIGHT, 0),
        constants.PROCESS_BUTTON_WIDTH,
        constants.PROCESS_BUTTON_HEIGHT,
        constants.OPERATOR_PROCESSES_BUTTON_LABEL,
        background_color=constants.STANDARD_BUTTON_COLOR,
    )

    # only start threading of watchdog if watchdog_only is true.
    if process_params.is_watchdog_only and process_watchdog is not None:
      process_watchdog.start()

  def dialog_pressed(self, dialog_id: str, choice: str) -> None:
    """Called when a dialog is submitted."""
    print(f"Dialog submitted: {dialog_id}, choice: {choice}")
    if dialog_id == constants.PROCESS_WARNING_DIALOG_ID and choice == "Yes":
      process = self.buffered_process
      if process is not None:
        if self.start_buffered_process:
          self.start_process(process)
        else:
          process_signal = (
              signal.SIGKILL if self._use_sigkill else signal.SIGINT
          )
          process.stop_process(process_signal)

  def button_pressed(self, button_id: str) -> None:
    """Called when a button is pressed."""
    print(f"\n\nButton pressed: {button_id}")
    for process in self.processes:
      if button_id != process.get_button_id():
        continue
      process.button_pressed_time = time.time()
      if process.is_process_running():
        if process.stop_warning_message is None:
          process_signal = (
              signal.SIGKILL if self._use_sigkill else signal.SIGINT
          )
          process.stop_process(process_signal)
        else:
          self.buffered_process = process
          self.start_buffered_process = False
          self.ui.create_dialog(
              dialog_id=constants.PROCESS_WARNING_DIALOG_ID,
              title="Warning",
              msg=process.stop_warning_message,
              buttons=["Yes", "No"],
              spec=robotics_ui_pb2.UISpec(
                  width=0.3,
                  height=0.3,
                  x=0.5,
                  y=0.5,
                  mode=robotics_ui_pb2.UIMode.UIMODE_MODAL,
              ),
          )
      else:
        if process.start_warning_message is None:
          self.start_process(process)
        else:
          self.buffered_process = process
          self.start_buffered_process = True
          self.ui.create_dialog(
              dialog_id=constants.PROCESS_WARNING_DIALOG_ID,
              title="Warning",
              msg=process.start_warning_message,
              buttons=["Yes", "No"],
              spec=robotics_ui_pb2.UISpec(
                  width=0.3,
                  height=0.3,
                  x=0.5,
                  y=0.5,
                  mode=robotics_ui_pb2.UIMode.UIMODE_MODAL,
              ),
          )

    if button_id == constants.PROCESS_COLLAPSE_BUTTON_ID:
      self.buttons_collapsed = not self.buttons_collapsed
      if self.buttons_collapsed:
        self.buttons_removed = False
      print(f"buttons set to collapsed: {self.buttons_collapsed}")

  def _handle_sigchld(self, signum: int, frame: types.FrameType) -> None:
    """Handles SIGCHLD signals to clean up zombie processes."""
    del signum
    del frame
    while True:
      try:
        pid = os.waitpid(-1, os.WNOHANG)
        if pid == 0:
          break  # No more zombies to reap
      except ChildProcessError:
        break

  def _run_update_process(self) -> None:
    """Updates the status of any processes."""
    while True:
      if self._process_thread_stop_event.is_set():
        return
      self._update_process_status()
      time.sleep(0.1)

  def _update_process_status(self) -> None:
    """Updates the status of any processes."""
    if self.buttons_collapsed:
      if not self.buttons_removed:
        for process in self.processes:
          self.ui.remove_element(process.get_button_id())
          # self.ui.remove_element(process.get_text_id())
        self.buttons_removed = True
      return
    for i, process in enumerate(self.processes):
      is_running = process.is_process_running()

      y = get_y_position(constants.PROCESS_BUTTON_HEIGHT, i + 1)
      # Update process running text in Robotics UI.
      # TODO: b/342435045 - restore process state text after improving the
      # accuracy of process state handling.
      # self.ui.create_or_update_text(
      #     text_id=process.get_text_id(),
      #     spec=robotics_ui_pb2.UISpec(
      #         x=_TEXT_START_X, y=y, width=_TEXT_WIDTH, height=_HEIGHT
      #     ),
      #     text=(
      #         "<color=green>Running</color>"
      #         if is_running
      #         else "<color=red>Stopped</color>"
      #     ),
      # )
      # Update button text in Robotics UI to start or stop process.
      button_id = process.get_button_id()
      hover_text = None
      if process.watchdog:
        process.watchdog.set_process_running(is_running)
        if is_running:
          state = (
              process.watchdog.get_state()
              if process.is_watchdog_only
              else process.watchdog.handle_startup()
          )
          button_text = process.get_stop_button_text()
        else:
          state = process.watchdog.set_state_offline()
          button_text = process.get_start_button_text()
        button_text = "<b>[" + state.value + "]</b>" + " " + button_text
        background_color = constants.PROCESS_STATE_TO_COLOR_MAP[state]
        if process.watchdog.is_crashed():
          hover_text = f"{process.watchdog.get_state_message()}"
      else:
        background_color = constants.STANDARD_SUB_BUTTON_COLOR
        button_text = (
            process.get_stop_button_text()
            if is_running
            else process.get_start_button_text()
        )
      disabled = time.time() - process.button_pressed_time < 3
      self.ui.create_button(
          button_id,
          constants.PROCESS_BUTTON_START_X,
          y,
          constants.PROCESS_BUTTON_WIDTH,
          constants.PROCESS_BUTTON_HEIGHT,
          button_text,
          disabled=disabled,
          background_color=background_color,
          hover_text=hover_text,
      )

  def start_process(self, process: ProcessParams) -> None:
    """Starts a process."""
    if process.citc:
      citc_client_name = (
          f"{constants.PROCESS_CITC_CLIENT_PREFIX}{os.urandom(8).hex()}"
      )
      process.citc_client_name = citc_client_name
      command = to_citc_command(
          process.citc_client_name,
          get_process_name(process.name, process.path),
          process.args,
      )
      process.popen_process = start_process_in_terminal(command)
    elif process.output_to_ui:
      command = to_local_command(
          get_process_name(process.name, process.path), process.args
      )
      process.popen_process = start_process(command)
      self.send_output_to_ui(process)
    else:
      command = to_local_command(
          get_process_name(process.name, process.path), process.args
      )
      command += " bash;"
      process.popen_process = start_process_in_terminal(command)
    print(command)

  def send_output_to_ui(self, process: ProcessParams) -> None:
    """Send the output of a process to the UI chat console."""
    chat_id = f"output-{process.name}"
    self.ui.create_chat(
        chat_id=chat_id,
        title=process.name,
        submit_label="Send",
        spec=robotics_ui_pb2.UISpec(width=0.5, height=0.4, x=0.5, y=0.75),
    )

    def read_stream(
        process: subprocess.Popen[str],
        is_stderr: bool,
        watchdog: process_watchdog_lib.ProcessWatchdog | None = None,
    ):
      stream = process.stderr if is_stderr else process.stdout
      while stream is not None and process.poll() is None:
        line = stream.readline()
        if not line:
          break
        text = line.strip()
        if watchdog is not None:
          watchdog.check_line_and_set_state(text)
        # Colorize error messages.
        if "[ERROR]" in text:
          text = f"<color=red>{text}</color>"
        self.ui.add_chat_line(chat_id=chat_id, text=text)
        # Check stderr against error regexes.
        if is_stderr:
          self.create_workcell_error_recovery_schema(line)

    self.stop_output_threads(process)
    process.stdout_thread = threading.Thread(
        target=read_stream,
        args=(process.popen_process, False, process.watchdog),
        daemon=True,
    )
    process.stderr_thread = threading.Thread(
        target=read_stream,
        args=(process.popen_process, True, process.watchdog),
        daemon=True,
    )
    print(f"starting {process.name} output threads")
    process.stdout_thread.start()
    process.stderr_thread.start()

  def create_workcell_error_recovery_schema(self, line: str) -> None:
    """Creates a workcell error recovery schema."""
    for workcell_error in self._workcell_errors_list:
      if re.fullmatch(workcell_error.error_identifier_regex, line):
        print(line)
        recovery_image_bytes = (
            workcell_error.error_recovery_scheme.get_recovery_image_bytes()
        )
        self.ui.create_dialog(
            dialog_id="fns:info",
            title="Alert",
            msg=workcell_error.error_recovery_scheme.recovery_initial_message,
            buttons=["OK"],
            spec=robotics_ui_pb2.UISpec(width=0.5, height=0.25, x=0.4, y=0.25),
        )
        image_window_spec = robotics_ui_pb2.UISpec(
            width=0.25,
            height=0.3,
            x=0.8,
            y=0.8,
        )
        self.ui.make_image_window(
            image=recovery_image_bytes,
            title="Recovery Image",
            spec=image_window_spec,
            window_id="rui:recovery_image",
        )

  def stop_output_threads(self, process: ProcessParams) -> None:
    """Stops the output thread of a process."""
    if process.stdout_thread is not None:
      process.stdout_thread.join()  # pytype: disable=attribute-error
      process.stdout_thread = None
      print(f"stopping {process.name} stdout thread")
    if process.stderr_thread is not None:
      process.stderr_thread.join()  # pytype: disable=attribute-error
      process.stderr_thread = None
      print(f"stopping {process.name} stderr thread")

  def enable_sigkill(self, enabled: bool) -> None:
    """Whether to use SIGKILL to stop processes."""
    self._use_sigkill = enabled
