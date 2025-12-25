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

"""A library for monitoring processes and persisting their state."""

import datetime
import logging
import os
import re
import signal
import threading
import time

from safari_sdk.workcell import process_state
from safari_sdk.workcell import workcell_messages_lib


ProcessState = process_state.ProcessState
_STARTING_UP_TIMEOUT_SECONDS = 60


class ProcessWatchdog(threading.Thread):
  """A class to monitor processes, track their state, and persist state changes to a file."""

  def __init__(
      self,
      state_conditions_list: (
          list[workcell_messages_lib.WorkcellMessage] | None
      ) = None,
      process_name: str = '',
      process_stdout_file_path: str | None = None,
      dir_to_dump_messages_in: str | None = None,
      catch_fatal: bool = True,
      process_startup_timeout_seconds: int = _STARTING_UP_TIMEOUT_SECONDS,
  ):
    """Initializes the ProcessWatchdog.

    Args:
      state_conditions_list: A list of state conditions.
      process_name: The name of the process to monitor.
      process_stdout_file_path: The path to the stdout/stderr file of the
        process.
      dir_to_dump_messages_in: The directory to dump messages to.
      catch_fatal: If true, the watchdog will catch fatal messages and set the
        state to crashed.
      process_startup_timeout_seconds: The timeout in seconds for the process to
        start up.
    """
    super().__init__()  # Call the constructor of the parent class
    self._last_position = 0
    self._process_name = process_name
    self._process_stdout_file_path = process_stdout_file_path
    self._state_conditions_list = state_conditions_list
    self._current_state = ProcessState.OFFLINE
    self._state_message = ''
    self._messages_to_dump = []
    self._should_run = True
    self._is_online = False
    self._start_time = None
    self._catch_fatal = catch_fatal
    self._process_startup_timeout_seconds = process_startup_timeout_seconds
    self._dir_to_dump_messages_in = dir_to_dump_messages_in
    self._messages_buffer = []
    self._is_process_running = False
    signal.signal(signal.SIGINT, self._handle_sigint)

  def _handle_sigint(self, signum, frame):
    """Handles SIGINT by stopping the thread."""
    del signum
    del frame
    logging.info(
        'Received SIGINT, stopping process watchdog for %s', self._process_name
    )
    self.stop()

  def run(self):
    """Main loop of the thread."""
    logging.info('Starting process watchdog for %s', self._process_name)
    self._run_stdout_check()

  def stop(self):
    """Stops the thread."""
    self._should_run = False

  def check_line_and_set_state(self, line: str) -> None:
    """Checks a line and sets the state if a state condition is met."""
    cleaned_message = self._clean_string(line)
    message_dict = workcell_messages_lib.get_workcell_messages_dict(
        self._state_conditions_list
    )
    if '[ERROR]' in cleaned_message:
      self._messages_to_dump.append(cleaned_message + '\n')
    if self._catch_fatal:
      if '[FATAL]' in cleaned_message:
        self._messages_to_dump.append(cleaned_message + '\n')
        self._update_state(ProcessState.CRASHED, cleaned_message)
    if cleaned_message in message_dict:
      new_process_state = message_dict[cleaned_message]
      if new_process_state == ProcessState.PARTIAL_SUCCESS:
        self._add_message_to_buffer(cleaned_message)
        if tuple(sorted(self._messages_buffer)) in message_dict:
          self._update_state(message_dict[tuple(sorted(self._messages_buffer))])
          self._clear_messages_buffer()
      elif (
          new_process_state == ProcessState.CRASHED
          or new_process_state == ProcessState.UNHEALTHY
      ):
        self._messages_to_dump.append(cleaned_message + '\n')
        self._update_state(new_process_state, cleaned_message)
      else:
        self._update_state(new_process_state)

  def get_state(self) -> ProcessState:
    """Get the current state of the process.

    Returns:
      The current state of the process.
    """
    return self._current_state

  def get_state_message(self) -> str:
    """Returns the current state message of the process.

    Returns:
      The current state message of the process.
    """
    return self._state_message

  def set_state_offline(self) -> ProcessState:
    """Sets the state to offline if it is not crashed and gets the current state.

    Returns:
      The current state of the process.
    """
    self._is_online = False
    self._clear_messages_buffer()
    if self._current_state != ProcessState.CRASHED:
      self._update_state(ProcessState.OFFLINE)
    return self.get_state()

  def handle_startup(self) -> ProcessState:
    """Handles the state of the process during startup.

    Sets the state to starting up if the state is not online and checks if the
    state is stuck in starting up state. Sets the state to crashed if it is.

    Returns:
      The current state of the process.
    """
    if not self._is_online:
      self._is_online = True
      self._current_state = ProcessState.STARTING_UP
      self._start_time = time.time()
    elif (
        self._current_state == ProcessState.STARTING_UP
        and self._start_time is not None
        and (time.time() - self._start_time)
        > self._process_startup_timeout_seconds
    ):
      self._update_state(
          ProcessState.CRASHED,
          'Timeout: Process did not start up after'
          f' {_STARTING_UP_TIMEOUT_SECONDS} seconds.',
      )
    return self.get_state()

  def is_crashed(self) -> bool:
    """Returns true if the process is crashed."""
    return self._current_state == ProcessState.CRASHED

  def set_process_running(self, is_running: bool) -> None:
    """Sets the process as running."""
    self._is_process_running = is_running

  def _run_stdout_check(self):
    """Runs the stdout check.

    Target of the threading functionality. It checks to see if the process is
    running and if it is not, it sets the state to offline. If the process is
    running, it checks the stdout/stderr for state conditions and updates the
    state accordingly. Set to run at 10 Hz.
    """
    while self._should_run:
      if not self._is_process_running:
        self._is_online = False
        # NOTE: last_position should be set according to how the logs are being
        # saved. ie: if the file is overwritten after every run, then the
        # last_position should be 0. Otherwise, it should be the size of the
        # file.
        self._last_position = 0
        if self._current_state != ProcessState.CRASHED:
          self._update_state(ProcessState.OFFLINE)
      else:
        if not self._is_online:
          self._update_state(ProcessState.STARTING_UP)
        self._is_online = True
        self._read_process_stdout_and_set_state()
      if not self._should_run:
        break
      time.sleep(0.1)

  def _read_process_stdout_and_set_state(self):
    """Reads the process stdout and sets the state if a state condition is met."""
    if self._process_stdout_file_path is None:
      raise ValueError(
          'Process stdout file path is None. Can not run threading'
          ' functionality without a set path.'
      )
    with open(self._process_stdout_file_path, 'r') as f:
      f.seek(self._last_position)
      logging.info('last_position: %s', self._last_position)
      for line in f:
        self.check_line_and_set_state(line)
      self._last_position = f.tell()
      logging.info('last_position: %s', self._last_position)
    f.close()

  def _add_message_to_buffer(self, line: str) -> None:
    """Buffers the message to check for full array of messages.

    The buffer is used to check for conditions that require an array of
    messages.

    Args:
      line: The message to add to the buffer.
    """
    self._messages_buffer.append(line)

  def _clear_messages_buffer(self) -> None:
    """clears the buffer."""
    self._messages_buffer = []

  def _clean_string(self, line: str) -> str:
    """Cleans the string by removing escape sequences and timestamps.

    The cleaning is intended for specific types of messages. It handles logging
    messages from from built par files and standard ros2 logging. If any further
    customization is needed, it will need to be modified.

    Args:
      line: The string to clean.

    Returns:
      The cleaned string.
    """
    return re.sub(
        r'\x1b\[[0-9;]*m|\[\d+\.\d+\]|.*?(\s+[a-zA-Z0-9_]+\.py:\d+\])',
        '',
        line,
    ).strip()  # remove escape sequences

  def _create_file_with_timestamp(self, directory: str) -> str:
    """Creates an empty file with a timestamped filename in the specified directory.

    Args:
      directory: The absolute or relative path to directory where log files
        should be made.

    Returns:
      A full path to the created log file.
    """

    # Create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = '%s_%s.log' % (self._process_name, timestamp)
    full_path = os.path.join(directory, filename)

    with open(full_path, 'w'):
      pass

    return full_path

  def _update_state(
      self, new_state: ProcessState, msg: str | None = None
  ):  # in
    """Updates the current state and writes it to the state file.

    The state is only updated if it is different from the current state. It also
    dumps messages that were tracked during the state. Refer to the
    _dump_messages function for more details.

    Args:
      new_state: The new state to set.
      msg: The message to set with the new state.
    """
    if self._current_state == new_state:
      return
    self._dump_messages()
    if msg is not None:
      self._state_message = msg
    self._current_state = new_state
    if self._current_state != ProcessState.STARTING_UP:
      self._start_time = None
      self._messages_to_dump = []

  def _dump_messages(self):
    """Dumps the messages to some specified directory and returns the current state.

    Messages that are dumped are:
    1. Messages that are logged with [ERROR] or [FATAL] in them.
    2. Messages that are logged with a state condition that is either CRASHED
    or UNHEALTHY.

    Returns:
      The current state of the process.
    """
    if self._messages_to_dump and self._dir_to_dump_messages_in:
      logging.info('Dumping messages to %s', self._dir_to_dump_messages_in)
      file_path = self._create_file_with_timestamp(
          self._dir_to_dump_messages_in
      )
      with open(file_path, 'w') as f:
        f.writelines(self._messages_to_dump)
      self._messages_to_dump = []
