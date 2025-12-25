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

"""RoboticsUI framework."""

import datetime
import logging
import queue
import statistics
import sys
import threading
import time
import traceback
from typing import Callable
import uuid

import imageio

from safari_sdk.protos.ui import robot_frames_pb2
from safari_sdk.protos.ui import robot_state_pb2
from safari_sdk.protos.ui import robot_types_pb2
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.protos.ui import xemb_pb2
from safari_sdk.ui.client import _internal
from safari_sdk.ui.client import exceptions
from safari_sdk.ui.client import functions
from safari_sdk.ui.client import iframework
from safari_sdk.ui.client import images
from safari_sdk.ui.client import kinematic_tree_robot
from safari_sdk.ui.client import stl_parser
from safari_sdk.ui.client import types
from safari_sdk.ui.client import ui_callbacks
from safari_sdk.ui.client import upload_engine


JpegCameraImageData = images.JpegCameraImageData
UiCallbacks = ui_callbacks.UiCallbacks


class Framework(iframework.IFramework):
  """The RoboticsUI framework."""

  clients: list[_internal.UiClientInterface]
  mock_clients: list[_internal.UiClientInterface] | None
  _client_is_connected: list[threading.Event]
  disconnect_mutex: threading.Lock

  callbacks: UiCallbacks
  callback_lock: threading.Lock
  incoming_msg_queue: queue.Queue[robotics_ui_pb2.RuiMessage]
  is_synchronous: bool
  time_last: int
  handlers: dict[str, Callable[[str, robotics_ui_pb2.UIMessage], None]]

  report_stats: bool
  ping_lock: threading.Lock
  last_pong_time: int
  last_ping_latency: int
  last_ping_latencies_10s: list[int]
  ping_report_interval_sec: int
  last_ping_report_time_ns: int
  pings: dict[str, int]
  last_message_report_ns: int
  message_report_interval_sec: int

  # The rate beyond which image sends will drop images. Set to zero to disable
  # throttling.
  image_send_min_interval: int
  last_image_send_time: int

  blocking_callback_data: _internal.CallbackData | None
  blocking_event: threading.Event

  # This is here specifically so that tests can know when the framework is in
  # its blocking state, and can now send the message to unblock it.
  is_blocking_on: threading.Event

  # Set when shutdown() is called.
  stop_event: threading.Event

  # Set when ALL connections are made, but this does not necessarily mean all
  # connections are live. Liveness means that at least one message has been
  # received on the connection.
  connected_event: threading.Event

  # Set when ALL connections are live. This also means that the init_screen
  # callback has been called.
  connections_live_event: threading.Event

  # The engine that handles uploads for the framework.
  _upload_engine: upload_engine.UploadEngine

  # The parser for STL files.
  _stl_parser: Callable[[types.PathLike], robotics_ui_pb2.WireTriangleFormat]
  _stl_parser_from_locator: Callable[
      [robotics_ui_pb2.ResourceLocator], robotics_ui_pb2.WireTriangleFormat
  ]

  def __init__(
      self,
      callbacks: UiCallbacks | None = None,
      mock_clients: list[_internal.UiClientInterface] | None = None,
      report_stats: bool = False,
      object_data_supplier: Callable[[types.PathLike], bytes] | None = None,
      mock_upload_engine: upload_engine.UploadEngine | None = None,
      mock_stl_parser: (
          Callable[[types.PathLike], robotics_ui_pb2.WireTriangleFormat] | None
      ) = None,
      mock_stl_parser_from_locator: (
          Callable[
              [robotics_ui_pb2.ResourceLocator],
              robotics_ui_pb2.WireTriangleFormat,
          ]
          | None
      ) = None,
  ):
    """Initializes the framework, connecting to the RoboticsUI.

    Args:
      callbacks: An instance of a UiCallbacks object which will handle all
        callbacks. Defaults to an instance that just prints out messages.
      mock_clients: For testing only.
      report_stats: Whether to report stats to the console.
      object_data_supplier: A function that takes a filename and returns the
        data of the object. Used for testing. If None, the framework will read
        the file from the client's local disk.
      mock_upload_engine: For testing only.
      mock_stl_parser: For testing only.
      mock_stl_parser_from_locator: For testing only.
    """
    if callbacks is None:
      self.callbacks = UiCallbacks()
    else:
      self.callbacks = callbacks
    self.callback_lock = threading.Lock()

    self.clients = []
    self.mock_clients = mock_clients
    self._client_is_connected = []
    self.disconnect_mutex = threading.Lock()

    self.incoming_msg_queue = queue.Queue()
    self.is_synchronous = False
    self.time_last = time.time_ns()

    self.image_send_min_interval = 0
    self.last_image_send_time = 0

    self.ping_lock = threading.Lock()
    self.last_ping_latency = 0xFFFFFFFFFFFFFFFF
    self.last_ping_latencies_10s = []
    self.last_pong_time = 0
    self.pings = {}

    self.report_stats = report_stats
    now = time.time_ns()
    self.last_ping_report_time_ns = now
    self.ping_report_interval_sec = 10
    self.last_message_report_ns = now
    self.message_report_interval_sec = 10

    if mock_upload_engine is None:
      self._upload_engine = upload_engine.UploadEngine(
          self, object_data_supplier
      )
    else:
      self._upload_engine = mock_upload_engine

    if mock_stl_parser is None:
      self._stl_parser = stl_parser.parse_stl
    else:
      self._stl_parser = mock_stl_parser

    if mock_stl_parser_from_locator is None:
      self._stl_parser_from_locator = stl_parser.parse_stl_from_locator
    else:
      self._stl_parser_from_locator = mock_stl_parser_from_locator

    # Handlers for each oneof in a UIMessage.
    self.handlers = {
        "console_data": self._handle_console_data,
        "button_pressed_event": self._handle_button_pressed,
        "button_released_event": self._handle_button_released,
        "dialog_pressed_event": self._handle_dialog_pressed,
        "prompt_pressed_event": self._handle_prompt_pressed,
        "dropdown_pressed_event": self._handle_dropdown_pressed,
        "pong": self._handle_pong,
        "embody_response": self._handle_embody_response,
        "check_file_cache_response": (
            self._upload_engine.handle_check_resource_cache_response
        ),
        "gui_element_value_response": self._handle_gui_element_value_response,
        "upload_kinematic_tree_robot_response": (
            self._handle_upload_kinematic_tree_robot_response
        ),
        "form_pressed_event": self._handle_form_pressed,
        "hover_received_event": self._handle_hover_received,
        "get_resource_request": self._handle_get_resource_request,
        "version_report": lambda *args, **kwargs: None,  # ignore.
        "chat_pressed_event": self._handle_chat_received,
        "toggle_pressed_event": self._handle_toggle_pressed,
    }

    self.blocking_callback_data = None
    self.blocking_event = threading.Event()
    self.is_blocking_on = threading.Event()

    self.stop_event = threading.Event()
    self.connected_event = threading.Event()
    self.connections_live_event = threading.Event()

    logging.info("RoboticsUI framework initialized.")

  def get_callbacks(self) -> UiCallbacks:
    return self.callbacks

  def add_resource_upload_listener(
      self, receiver: Callable[[types.ResourceLocator, bytes], None]
  ) -> None:
    self._upload_engine.add_resource_upload_listener(receiver)

  def remove_resource_upload_listener(
      self, receiver: Callable[[types.ResourceLocator, bytes], None]
  ) -> None:
    self._upload_engine.remove_resource_upload_listener(receiver)

  def connect(
      self,
      host: str = "localhost",
      port: int = 50011,
      additional_host_ports: list[tuple[str, int]] | None = None,
      block_until_connected: bool = True,
      connect_retry_interval_secs: float = 2,
  ) -> None:
    """Connects to RoboticsUI via TCP host and port.

    Args:
      host: The default host to connect to.
      port: The default port to connect to.
      additional_host_ports: A list of (host, port) for multi-host connection.
      block_until_connected: Whether to block until connected.
      connect_retry_interval_secs: The interval to retry connecting.
    """
    host_ports = [(host, port)]
    if additional_host_ports:
      host_ports += additional_host_ports
    self._client_is_connected = [threading.Event() for _ in host_ports]

    for i, (host, port) in enumerate(host_ports):
      logging.info("Connecting to RoboticsUI at %s:%d", host, port)
      if self.mock_clients:
        client = self.mock_clients[i]
      else:
        client = _internal.TcpUiClient(collect_stats=self.report_stats)
      self.clients.append(client)

      threading.Thread(
          target=self._start,
          args=(client, host, port, i, connect_retry_interval_secs),
          name=f"Framework[{i}].start",
          daemon=True,
      ).start()

    threading.Thread(
        target=self._monitor_for_liveness,
        name="_monitor_for_liveness",
        daemon=True,
    ).start()

    while block_until_connected and not self.stop_event.is_set():
      if self.connections_live_event.wait(timeout=0.1):
        break

  def _monitor_for_liveness(self) -> None:
    """Monitors for liveness of all connections.

    Once all connections are up, the receiver thread and pinger thread are
    started, and the connected_event is set.

    Once all connections are live, the init_screen callback is called.

    If at any point the stop_event is set, then the shutdown() function is
    called and we just return.
    """
    while (
        not all(
            self._client_is_connected[i].is_set()
            for i in range(len(self.clients))
        )
        and not self.stop_event.is_set()
    ):
      time.sleep(0.2)
      continue

    if self.stop_event.is_set():
      self.shutdown()
      return

    # All connections are up, but not all are live at this point.
    logging.info("All UI connections are up, awaiting liveness")
    self._start_receiver_thread()
    self._start_pinger_thread()
    self.connected_event.set()

    while (
        not all(client.is_live() for client in self.clients)
        and not self.stop_event.is_set()
    ):
      time.sleep(0.2)
      continue

    if self.stop_event.is_set():
      self.shutdown()
      return

    # All connections are now live.
    logging.info("All UI client connections are live:")
    for client in self.clients:
      report = client.get_version_report()
      logging.info(
          "  %s:%d version '%s'=%s, capabilities: %s",
          report.connection_ip,
          report.connection_port,
          report.name,
          report.version or "(not reported)",
          str(report.capabilities),
      )
    self.callbacks.set_version_reports(
        [client.get_version_report() for client in self.clients]
    )
    try:
      self.callbacks.init_screen(self)
    except Exception:  # pylint: disable=broad-except
      logging.error(
          "init_screen callback failed after all connections were live"
      )
      traceback.print_exc()
      self.shutdown()
      return
    self.connections_live_event.set()

  def shutdown(self, client: _internal.UiClientInterface | None = None) -> None:
    with self.disconnect_mutex:
      already_disconnected = self.stop_event.is_set()

      # Makes sure we only shutdown once.
      if not already_disconnected:
        clients = [client] if client else self.clients
        for i, client in enumerate(clients):
          client.disconnect()
          self._client_is_connected[i].clear()
          logging.warning("RoboticsUI connection %d was shut down by client", i)

        # If all clients are disconnected, then we are done.
        if all(map(lambda client: client.is_disconnected(), self.clients)):
          logging.info(
              "All clients disconnected from RoboticsUI: setting stop_event"
          )
          self.blocking_event.set()
          self.connected_event.clear()
          self.callbacks.ui_connection_died()
          self.stop_event.set()

  def is_shutdown(self) -> bool:
    return self.stop_event.is_set()

  def _start_receiver_thread(self) -> None:
    for client in self.clients:
      thread = threading.Thread(
          target=self._receiver_loop,
          args=(client,),
          name="_receiver_loop",
          daemon=True,
      )
      thread.start()

  def _start_pinger_thread(self) -> None:
    thread = threading.Thread(
        target=self._pinger_loop, name="_pinger_loop", daemon=True
    )
    thread.start()

  def _enqueue_received_message(self, msg: robotics_ui_pb2.RuiMessage) -> None:
    self.incoming_msg_queue.put(msg)

  def _callback_for_message(self, msg: robotics_ui_pb2.RuiMessage) -> None:
    """Calls the appropriate callback for a message, in the current thread.

    Thread-safe.

    Args:
      msg: The message to call back for.
    """
    with self.callback_lock:
      if msg.HasField("teleop_message"):
        # Required to prevent tests from failing with
        # "assert.h assertion failed at third_party/python_runtime/
        #   v3_11/Modules/_io/textio.c".
        # See http://yaqs/11950591882297344.
        sys.stdout.flush()
        now_ns = time.time_ns()
        self.time_last = now_ns
        self.callbacks.teleop_received(teleop_message=msg.teleop_message)
        self.callbacks.teleop_received_ts(
            teleop_message=msg.teleop_message,
            origin_timestamp_nsec=msg.sent_timestamp_nsec,
            local_timestamp_nsec=now_ns,
        )

      elif msg.HasField("ui_message"):
        self._handle_ui_message(msg.message_id, msg.ui_message)

      elif msg.HasField("xemb_message") and msg.xemb_message.HasField(
          "robot_command"
      ):
        self.callbacks.command_received(msg.xemb_message.robot_command)

  def _dequeue_received_message(self) -> None:
    """Dequeues a received message and handles it."""
    try:
      msg = self.incoming_msg_queue.get(block=False)
      self._callback_for_message(msg)
    except queue.Empty:
      return

  def _send_message(self, msg: robotics_ui_pb2.RuiMessage) -> str:
    if self.stop_event.is_set() or not self.connected_event.is_set():
      raise exceptions.RoboticsUIConnectionError(
          "RoboticsUI is shut down or not connected."
      )
    for client in self.clients:
      client.send_message(msg)
    return ""

  def send_raw_message(self, msg: robotics_ui_pb2.RuiMessage) -> str:
    return self._send_message(msg)

  def _handle_console_data(
      self, _: str, ui_message: robotics_ui_pb2.UIMessage
  ) -> None:
    self.callbacks.console_data_received(ui_message.console_data)

  def _handle_button_pressed(
      self, _: str, ui_message: robotics_ui_pb2.UIMessage
  ) -> None:
    """Handles a button pressed event."""
    cb = self.blocking_callback_data
    if (
        cb is not None
        and cb.element_type == _internal.ElementType.BUTTON
        and cb.element_id == ui_message.button_pressed_event.button_id
    ):
      cb.return_value = ui_message.button_pressed_event.button_id
      self.blocking_event.set()
      return
    self.callbacks.button_pressed(ui_message.button_pressed_event.button_id)

  def _handle_button_released(
      self, _: str, ui_message: robotics_ui_pb2.UIMessage
  ) -> None:
    """Handles a button released event."""
    self.callbacks.button_released(ui_message.button_released_event.button_id)

  def _handle_dialog_pressed(
      self, _: str, ui_message: robotics_ui_pb2.UIMessage
  ) -> None:
    """Handles a dialog pressed event."""
    cb = self.blocking_callback_data
    if (
        cb is not None
        and cb.element_type == _internal.ElementType.DIALOG
        and cb.element_id == ui_message.dialog_pressed_event.dialog_id
    ):
      cb.return_value = ui_message.dialog_pressed_event.choice
      self.blocking_event.set()
      return
    self.callbacks.dialog_pressed(
        ui_message.dialog_pressed_event.dialog_id,
        ui_message.dialog_pressed_event.choice,
    )

  def _handle_prompt_pressed(
      self, _: str, ui_message: robotics_ui_pb2.UIMessage
  ) -> None:
    """Handles a prompt pressed event."""
    cb = self.blocking_callback_data
    if (
        cb is not None
        and cb.element_type == _internal.ElementType.PROMPT
        and cb.element_id == ui_message.prompt_pressed_event.prompt_id
    ):
      cb.return_value = ui_message.prompt_pressed_event.input
      self.blocking_event.set()
      return
    self.callbacks.prompt_pressed(
        ui_message.prompt_pressed_event.prompt_id,
        ui_message.prompt_pressed_event.input,
    )

  def _handle_dropdown_pressed(
      self, _: str, ui_message: robotics_ui_pb2.UIMessage
  ) -> None:
    """Handles a dropdown pressed event."""
    cb = self.blocking_callback_data
    multi_select = not ui_message.dropdown_pressed_event.choice
    if (
        cb is not None
        and cb.element_type == _internal.ElementType.DROPDOWN
        and cb.element_id == ui_message.dropdown_pressed_event.dropdown_id
    ):
      value = (
          list(ui_message.dropdown_pressed_event.choices)
          if multi_select
          else ui_message.dropdown_pressed_event.choice
      )
      cb.return_value = value
      self.blocking_event.set()
      return
    self.callbacks.dropdown_pressed(
        ui_message.dropdown_pressed_event.dropdown_id,
        list(ui_message.dropdown_pressed_event.choices)
        if multi_select
        else ui_message.dropdown_pressed_event.choice,
    )

  def _handle_form_pressed(
      self, _: str, ui_message: robotics_ui_pb2.UIMessage
  ) -> None:
    """Handles a form pressed event."""
    cb = self.blocking_callback_data
    if (
        cb is not None
        and cb.element_type == _internal.ElementType.FORM
        and cb.element_id == ui_message.form_pressed_event.form_id
    ):
      cb.return_value = ui_message.form_pressed_event.results
      self.blocking_event.set()
      return
    self.callbacks.form_pressed(
        ui_message.form_pressed_event.form_id,
        ui_message.form_pressed_event.results,
    )

  def _handle_toggle_pressed(
      self, _: str, ui_message: robotics_ui_pb2.UIMessage
  ) -> None:
    """Handles a toggle pressed event."""
    cb = self.blocking_callback_data
    if (
        cb is not None
        and cb.element_type == _internal.ElementType.TOGGLE
        and cb.element_id == ui_message.toggle_pressed_event.toggle_id
    ):
      cb.return_value = ui_message.toggle_pressed_event.selected
      self.blocking_event.set()
      return
    self.callbacks.toggle_pressed(
        ui_message.toggle_pressed_event.toggle_id,
        ui_message.toggle_pressed_event.selected,
    )

  def _handle_hover_received(
      self, _: str, ui_message: robotics_ui_pb2.UIMessage
  ) -> None:
    """Handles a hover received event."""
    self.callbacks.hover_received(
        ui_message.hover_received_event.element_id,
        ui_message.hover_received_event.text,
    )

  def _report_message_stats(self) -> None:
    """Reports the message stats."""
    if (
        time.time_ns() - self.last_message_report_ns
        < 1_000_000_000 * self.message_report_interval_sec
    ):
      return
    for client in self.clients:
      client.report_stats(self.last_message_report_ns)
    self.last_message_report_ns = time.time_ns()

  def _report_ping_latency(self) -> None:
    """Reports the ping latency."""
    if (
        time.time_ns() - self.last_ping_report_time_ns
        < 1_000_000_000 * self.ping_report_interval_sec
    ):
      return

    with self.ping_lock:
      self.last_ping_report_time_ns = time.time_ns()

      if len(self.last_ping_latencies_10s) < 2:
        logging.debug("No ping latency data.")
        return

      # All stats in usec
      avg = statistics.mean(self.last_ping_latencies_10s) // 1000
      stddev = statistics.stdev(self.last_ping_latencies_10s) // 1000
      minimum = min(self.last_ping_latencies_10s) // 1000
      maximum = max(self.last_ping_latencies_10s) // 1000
      logging.debug(
          "Ping latency (usec) avg: %d stddev: %d min: %d max: %d",
          avg,
          stddev,
          minimum,
          maximum,
      )

      self.last_ping_latencies_10s = []

  def _handle_pong(self, message_id: str, _: robotics_ui_pb2.UIMessage) -> None:
    """Handles a pong reply.

    Args:
      message_id: The message ID of the pong.
    """
    if message_id not in self.pings:
      return
    now = time.time_ns()

    with self.ping_lock:
      if self.report_stats:
        self.last_pong_time = now
        self.last_ping_latency = now - self.pings[message_id]
        self.last_ping_latencies_10s.append(self.last_ping_latency)
      del self.pings[message_id]

      # If any pings are overdue (>10 seconds), delete them.
      to_delete = []
      for ping_msg_id, ping_time in self.pings.items():
        if now - ping_time > 10_000_000_000:
          to_delete.append(ping_msg_id)
      for ping_msg_id in to_delete:
        del self.pings[ping_msg_id]

  def _handle_embody_response(
      self, _: str, ui_message: robotics_ui_pb2.UIMessage
  ) -> None:
    """Handles an embody response."""
    self.callbacks.embody_response(ui_message.embody_response)

  def _handle_gui_element_value_response(
      self, _: str, ui_message: robotics_ui_pb2.UIMessage
  ) -> None:
    """Handles a GUI element value response."""
    cb = self.blocking_callback_data
    if (
        cb is not None
        and cb.element_type == _internal.ElementType.UNKNOWN
        and cb.element_id == ui_message.gui_element_value_response.element_id
    ):
      cb.return_value = ui_message.gui_element_value_response.value
      self.blocking_event.set()
      return
    self.callbacks.gui_element_value_response(
        ui_message.gui_element_value_response
    )

  def _handle_ui_message(
      self, message_id: str, ui_message: robotics_ui_pb2.UIMessage
  ) -> None:
    """Handles UiMessages.

    Args:
      message_id: The message's ID.
      ui_message: The message's ui_message.
    """
    which = ui_message.WhichOneof("message")
    if which not in self.handlers:
      logging.warning("Unhandled UIMessage received: %s", str(which))
      return
    self.handlers[which](message_id, ui_message)

  def _handle_chat_received(
      self,
      _: str,
      ui_message: robotics_ui_pb2.UIMessage,
  ) -> None:
    """Handles a chat line received event."""
    self.callbacks.chat_received(
        ui_message.chat_pressed_event.chat_id,
        ui_message.chat_pressed_event.input,
    )

  def _receiver_loop(self, client: _internal.UiClientInterface) -> None:
    """An infinite loop, waiting for messages from Robotics UI."""

    try:
      logging.debug("Starting receiver loop")
      while not self.stop_event.is_set():
        # This helps in testing, to not call wait_for_message() before the
        # connection is established.
        if not self.connected_event.is_set():
          self.connected_event.wait(timeout=0.1)
          continue

        msg = client.wait_for_message()
        if msg is None:  # Connection died
          logging.info("A connection to RUI died")
          break

        if isinstance(msg, robotics_ui_pb2.RuiMessage):
          messages = [msg]
        elif isinstance(msg, robotics_ui_pb2.RuiMessageList):
          messages = msg.messages
        else:
          logging.error("Unknown message type: %s", type(msg))
          raise ValueError(f"Unknown message type: {type(msg)}")

        for m in messages:
          self._enqueue_received_message(m)
          if not self.is_synchronous:
            self._dequeue_received_message()
    except Exception:  # pylint: disable=broad-exception-caught
      logging.error(
          "Exception in framework when handling message",
          stack_info=True,
          exc_info=True,
      )
    finally:
      if self.stop_event.is_set():
        logging.info("Stop event was set in receiver loop")
      logging.debug("Receiver loop finished, shutting down connection")
      self.shutdown(client)

  def _pinger_loop(self) -> None:
    """Sends ping requests every second, optionally reporting stats."""

    try:
      while not self.stop_event.is_set():
        # This helps in testing, to not call wait_for_message() before the
        # connection is established.
        if not self.connected_event.is_set():
          self.connected_event.wait(timeout=0.1)
          continue

        time.sleep(1)
        # This will fail if there's no connection. Or if there's an ssh tunnel,
        # this will eventually fail when the tunnel's send buffer fills up.
        self._ping()
        if self.report_stats:
          self._report_ping_latency()
          self._report_message_stats()
    finally:
      self.shutdown()

  def _start(
      self,
      client: _internal.UiClientInterface,
      host: str,
      port: int,
      client_index: int,
      connect_retry_interval_secs: float,
  ) -> None:
    """Establishes a connection and starts a receiver and a pinger thread."""
    while not self.stop_event.is_set():
      try:
        # For an ssh tunnel, this will immediately succeed.
        client.connect(host, port)
        self._client_is_connected[client_index].set()
        break
      except OSError:
        logging.warning(
            "Failed to connect to RoboticsUI at %s:%d, retrying...", host, port
        )
        time.sleep(connect_retry_interval_secs)

  def send_robot_state(
      self, robot_state: robot_state_pb2.RobotState, robot_id: str | None = None
  ) -> str:
    uimessage = robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        xemb_message=xemb_pb2.XembMessage(
            robot_state=robot_state, robot_id=robot_id
        ),
    )
    if robot_id is None:
      uimessage.xemb_message.client_id.CopyFrom(robot_state.header.client_id)
    return self._send_message(uimessage)

  def block_on_with_value(
      self, callback_data: _internal.CallbackData
  ) -> _internal.CallbackReturnValue:
    if self.stop_event.is_set() or not self.connected_event.is_set():
      raise exceptions.RoboticsUIConnectionError(
          "RoboticsUI is shut down or not connected."
      )
    if self.is_synchronous:
      raise exceptions.BlockOnNotSupportedError(
          "block_on is not supported in synchronous mode."
      )
    self.blocking_callback_data = callback_data
    self.is_blocking_on.set()
    self.blocking_event.wait()
    if self.stop_event.is_set():
      return ""
    response = self.blocking_callback_data.return_value
    self.blocking_callback_data = None
    self.blocking_event.clear()
    self.is_blocking_on.clear()
    return response

  def block_on(self, callback_data: _internal.CallbackData) -> str:
    result = self.block_on_with_value(callback_data)
    if not isinstance(result, str):
      raise TypeError(
          f"block_on() expected str return value but got {type(result)}. For"
          " non-str return values, use block_on_with_value() instead."
      )
    return result

  def ask_user_yes_no(self, question: str) -> bool:
    choice = self.block_on(
        self.create_dialog(
            dialog_id=str(uuid.uuid4()),
            spec=robotics_ui_pb2.UISpec(
                mode=robotics_ui_pb2.UIMODE_MODAL,
                width=0.3,
                height=0.3,
                x=0.3,
                y=0.3,
            ),
            title=question,
            msg=question,
            buttons=["Yes", "No"],
        )
    )
    return choice == "Yes"

  def create_button(
      self,
      button_id: str,
      x: float,
      y: float,
      w: float,
      h: float,
      label: str,
      font_size: int = 0,  # defaults to Unity value
      disabled: bool = False,
      background_color: robotics_ui_pb2.Color | None = None,
      shortcuts: list[str] | None = None,
      transform: robotics_ui_pb2.UITransform | None = None,
      hover_text: str | None = None,
  ) -> _internal.CallbackData:
    spec = robotics_ui_pb2.UISpec(
        mode=robotics_ui_pb2.UIMode.UIMODE_PERSISTENT,
        x=x,
        y=y,
        width=w,
        height=h,
        font_size=font_size,
        disabled=disabled,
        background_color=background_color,
        transform=transform,
        hover_text=hover_text,
    )
    return self.create_button_spec(button_id, label, spec, shortcuts)

  def create_button_spec(
      self,
      button_id: str,
      label: str,
      spec: robotics_ui_pb2.UISpec | None = None,
      shortcuts: list[str] | None = None,
  ) -> _internal.CallbackData:
    uimessage = self.create_button_message(
        button_id=button_id,
        label=label,
        spec=spec,
        shortcuts=shortcuts,
    )
    self._send_message(uimessage)
    return _internal.CallbackData(button_id, _internal.ElementType.BUTTON, "")

  def create_dialog(
      self,
      dialog_id: str,
      title: str,
      msg: str,
      buttons: list[str] | None = None,
      spec: robotics_ui_pb2.UISpec | None = None,
  ) -> _internal.CallbackData:
    if buttons is None:
      buttons = ["Yes", "No"]
    if spec is None:
      spec = robotics_ui_pb2.UISpec(
          mode=robotics_ui_pb2.UIMODE_MODAL, width=0.2, height=0.2, x=0.5, y=0.5
      )
    uimessage = robotics_ui_pb2.RuiMessage(message_id=str(uuid.uuid4()))
    uimessage.ui_message.dialog_create_request.CopyFrom(
        robotics_ui_pb2.DialogCreateRequest(
            spec=spec,
            dialog_id=dialog_id,
            title=title,
            msg=msg,
            buttons=buttons,
        )
    )
    self._send_message(uimessage)
    return _internal.CallbackData(dialog_id, _internal.ElementType.DIALOG, "")

  def create_prompt(
      self,
      prompt_id: str,
      title: str,
      msg: str,
      submit_label: str,
      spec: robotics_ui_pb2.UISpec | None = None,
      multiline_input: bool = False,
      initial_value: str | None = None,
      autofill_values: list[str] | None = None,
  ) -> _internal.CallbackData:
    uimessage = self.create_prompt_message(
        prompt_id=prompt_id,
        title=title,
        msg=msg,
        submit_label=submit_label,
        spec=spec,
        multiline_input=multiline_input,
        initial_value=initial_value,
        autofill_values=autofill_values,
    )
    self._send_message(uimessage)
    return _internal.CallbackData(prompt_id, _internal.ElementType.PROMPT, "")

  def create_dropdown(
      self,
      dropdown_id: str,
      title: str,
      msg: str,
      choices: list[str],
      submit_label: str,
      spec: robotics_ui_pb2.UISpec | None = None,
      initial_value: str | None = None,
      multi_select: bool = False,
      initial_values: list[str] | None = None,
      shortcuts: dict[str, str] | None = None,
  ) -> _internal.CallbackData:
    uimessage = self.create_dropdown_message(
        dropdown_id=dropdown_id,
        title=title,
        msg=msg,
        choices=choices,
        submit_label=submit_label,
        spec=spec,
        initial_value=initial_value,
        multi_select=multi_select,
        initial_values=initial_values,
        shortcuts=shortcuts,
    )
    self._send_message(uimessage)
    return _internal.CallbackData(
        dropdown_id, _internal.ElementType.DROPDOWN, ""
    )

  def create_login(
      self,
      prompt_id: str | None = None,
      prompt_title: str | None = None,
      prompt_msg: str | None = None,
      submit_label: str | None = None,
      prompt_spec: robotics_ui_pb2.UISpec | None = None,
      text_id: str | None = None,
      text_spec: robotics_ui_pb2.UISpec | None = None,
      button_id: str | None = None,
      button_label: str | None = None,
      button_spec: robotics_ui_pb2.UISpec | None = None,
  ) -> _internal.CallbackData:
    prompt_id = prompt_id if prompt_id is not None else "login:prompt_userid"
    prompt_msg = prompt_msg if prompt_msg is not None else "Enter user id:"
    prompt_title = prompt_title if prompt_title is not None else "Login"
    submit_label = submit_label if submit_label is not None else "Log in"
    if prompt_spec is None:
      prompt_spec = robotics_ui_pb2.UISpec(
          x=0.5,
          y=0.5,
          height=0.2,
          width=0.2,
          mode=robotics_ui_pb2.UIMODE_MODAL,
      )

    text_id = text_id if text_id is not None else "login:text_userid"
    if text_spec is None:
      text_spec = robotics_ui_pb2.UISpec(
          x=0.5,
          y=0.95,
          height=0.05,
          width=0.2,
          mode=robotics_ui_pb2.UIMODE_PERSISTENT,
      )

    button_id = button_id if button_id is not None else "login:button_logout"
    button_label = button_label if button_label is not None else "Log out"
    if button_spec is None:
      button_spec = robotics_ui_pb2.UISpec(
          x=0.7,
          y=0.95,
          height=0.05,
          width=0.1,
          mode=robotics_ui_pb2.UIMODE_PERSISTENT,
      )

    uimessage = robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            login_create_request=robotics_ui_pb2.LoginCreateRequest(
                prompt_id=prompt_id,
                prompt_title=prompt_title,
                prompt_msg=prompt_msg,
                submit_label=submit_label,
                prompt_spec=prompt_spec,
                text_id=text_id,
                text_spec=text_spec,
                button_id=button_id,
                button_label=button_label,
                button_spec=button_spec,
            )
        ),
    )
    self._send_message(uimessage)
    return _internal.CallbackData(prompt_id, _internal.ElementType.PROMPT, "")

  def get_gui_element_value(self, element_id: str) -> _internal.CallbackData:
    uimessage = robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            gui_element_value_request=robotics_ui_pb2.GuiElementValueRequest(
                element_id=element_id
            )
        ),
    )
    self._send_message(uimessage)
    return _internal.CallbackData(element_id, _internal.ElementType.UNKNOWN, "")

  def make_image_window(
      self,
      image: bytes,
      title: str,
      spec: robotics_ui_pb2.UISpec,
      window_id: str | None = None,
  ) -> str:
    if not window_id:
      window_id = f"image_window:{title}"
    rows, cols, *_ = imageio.v2.imread(image).shape
    image_data = robotics_ui_pb2.BaseImage(
        cols=cols,
        rows=rows,
        image=image,
    )
    uimessage = robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            image_window_request=robotics_ui_pb2.ImageWindowRequest(
                sensor_id=-1,
                title=title,
                spec=spec,
                window_id=window_id,
                image=image_data,
            )
        ),
    )
    return self._send_message(uimessage)

  def make_camera_window(
      self,
      sensor_id: int,
      title: str,
      spec: robotics_ui_pb2.UISpec,
      window_id: str | None = None,
  ) -> str:
    if not window_id:
      window_id = f"image_window:{title}"
    uimessage = robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            image_window_request=robotics_ui_pb2.ImageWindowRequest(
                sensor_id=sensor_id,
                title=title,
                spec=spec,
                window_id=window_id,
            )
        ),
    )
    return self._send_message(uimessage)

  def make_stereo_image_quad(
      self,
      object_id: str,
      left_sensor_id: int,
      right_sensor_id: int,
      transform: robotics_ui_pb2.UITransform | None = None,
      transform_type: types.TransformType = types.TransformType.GLOBAL,
      parent_id: str | None = None,
      parent_part: str | None = None,
      params: dict[str, str] | None = None,
      robot_id: str | robot_types_pb2.ClientID | None = None,
  ) -> str:
    return self.create_or_update_object(
        object_id=object_id,
        object_type=robotics_ui_pb2.ObjectType.STEREO_IMAGE_QUAD,
        transform=transform,
        transform_type=transform_type,
        parent_id=parent_id,
        parent_part=parent_part,
        params=params,
        robot_id=robot_id,
        stereoscopic_image_sensors=robotics_ui_pb2.StereoscopicImageSensors(
            left_sensor_id=left_sensor_id,
            right_sensor_id=right_sensor_id,
        ),
    )

  def display_splash_screen(
      self,
      jpeg_image: bytes,
      cols: int = 0,
      rows: int = 0,
      timeout_seconds: float = 5.0,
      spec: robotics_ui_pb2.UISpec | None = None,
  ) -> str:
    pixel_type = robot_state_pb2.CameraImage.PixelType(
        compression=robot_state_pb2.CameraImage.PixelType.JPEG
    )
    if cols == 0 or rows == 0:
      rows, cols, *_ = imageio.v2.imread(jpeg_image).shape

    if spec is None:
      aspect_ratio = cols / rows
      # Retain aspect ratio.
      if rows >= cols:
        height = 0.5
        width = 0.5 * aspect_ratio
      else:
        height = 0.5 / aspect_ratio
        width = 0.5
      x = 0.5 - width / 2
      y = 0.5 - height / 2
      spec = robotics_ui_pb2.UISpec(
          mode=robotics_ui_pb2.UIMODE_PERSISTENT,
          width=width,
          height=height,
          x=x,
          y=y,
      )

    camera_image = robot_state_pb2.CameraImage(
        pixel_type=pixel_type,
        cols=cols,
        rows=rows,
        data=jpeg_image,
    )

    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                splash_screen_request=robotics_ui_pb2.SplashScreenRequest(
                    jpeg_image=camera_image,
                    timeout_seconds=timeout_seconds,
                    spec=spec,
                ),
            ),
        )
    )

  def create_or_update_object(
      self,
      object_id: str,
      object_type: robotics_ui_pb2.ObjectType,
      transform: robotics_ui_pb2.UITransform | None = None,
      transform_type: types.TransformType = types.TransformType.GLOBAL,
      parent_id: str | None = None,
      parent_part: str | None = None,
      params: dict[str, str] | None = None,
      robot_id: str | robot_types_pb2.ClientID | None = None,
      stereoscopic_image_sensors: (
          robotics_ui_pb2.StereoscopicImageSensors | None
      ) = None,
      monocular_image_sensor: (
          robotics_ui_pb2.MonocularImageSensor | None
      ) = None,
      manus_gloves_params: robotics_ui_pb2.ManusGlovesParams | None = None,
      vr_controller_params: robotics_ui_pb2.VRControllerParams | None = None,
      uploaded_object_params: (
          robotics_ui_pb2.UploadedObjectParams | None
      ) = None,
      material_specs: list[robotics_ui_pb2.MaterialSpec] | None = None,
      kinematic_tree_robot_params: (
          robotics_ui_pb2.KinematicTreeRobotParams | None
      ) = None,
      embodiable_robot_params: (
          robotics_ui_pb2.EmbodiableRobotParams | None
      ) = None,
  ) -> str:
    if transform is None:
      transform = functions.make_transform(
          functions.make_position(0, 0, 0),
          functions.make_quaternion_from_euler(0, 0, 0),
          functions.make_scale(1, 1, 1),
      )
    if params is None:
      params = {}
    uimessage = robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            object_create_or_update_request=robotics_ui_pb2.ObjectCreateOrUpdateRequest(
                object_id=object_id,
                object_type=object_type,
                global_transform=(
                    transform
                    if transform_type == types.TransformType.GLOBAL
                    else None
                ),
                local_transform=(
                    transform
                    if transform_type == types.TransformType.LOCAL
                    else None
                ),
                parent_id=parent_id,
                parent_part=parent_part,
                params=params,
            )
        ),
    )

    request = uimessage.ui_message.object_create_or_update_request

    if isinstance(robot_id, str):
      request.robot_id = robot_id
    elif isinstance(robot_id, robot_types_pb2.ClientID):
      request.client_id.CopyFrom(robot_id)

    if stereoscopic_image_sensors is not None:
      request.stereoscopic_image_sensors.CopyFrom(stereoscopic_image_sensors)
    if monocular_image_sensor is not None:
      request.mono_image_sensor.CopyFrom(monocular_image_sensor)
    if manus_gloves_params is not None:
      request.manus_gloves_params.CopyFrom(manus_gloves_params)
    if vr_controller_params is not None:
      request.vr_controller_params.CopyFrom(vr_controller_params)
    if uploaded_object_params is not None:
      request.uploaded_object_params.CopyFrom(uploaded_object_params)
    if material_specs is not None:
      for material_spec in material_specs:
        request.material_specs.append(material_spec)
    if kinematic_tree_robot_params is not None:
      request.kinematic_tree_robot_params.CopyFrom(kinematic_tree_robot_params)
    if embodiable_robot_params is not None:
      request.embodiable_robot_params.CopyFrom(embodiable_robot_params)
    return self._send_message(uimessage)

  def create_or_update_uploaded_object(
      self,
      object_id: str,
      object_hash: bytes,
      mime_type: str,
      transform: robotics_ui_pb2.UITransform | None = None,
      transform_type: types.TransformType = types.TransformType.GLOBAL,
      parent_id: str | None = None,
      parent_part: str | None = None,
  ) -> str:
    return self.create_or_update_object(
        object_id=object_id,
        object_type=robotics_ui_pb2.ObjectType.UPLOADED_OBJECT,
        transform=transform,
        transform_type=transform_type,
        parent_id=parent_id,
        parent_part=parent_part,
        uploaded_object_params=robotics_ui_pb2.UploadedObjectParams(
            hash=object_hash,
            mime_type=mime_type,
        ),
    )

  def clear_objects(self, prefix: str | None = None) -> str:
    uimessage = robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            clear_objects_request=robotics_ui_pb2.ClearObjectsRequest(
                prefix=prefix if prefix is not None else ""
            )
        ),
    )
    return self._send_message(uimessage)

  def clear_gui(self, prefix: str | None = None) -> str:
    uimessage = robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            clear_gui_request=robotics_ui_pb2.ClearGuiRequest(
                prefix=prefix if prefix is not None else ""
            )
        ),
    )
    return self._send_message(uimessage)

  def clear_all(self, prefix: str | None = None) -> None:
    self.clear_objects(prefix)
    self.clear_gui(prefix)

  def delete_object(self, object_id: str) -> str:
    uimessage = robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            object_delete_request=robotics_ui_pb2.ObjectDeleteRequest(
                object_id=object_id
            )
        ),
    )
    return self._send_message(uimessage)

  def reparent_object(
      self, object_id: str, parent_id: str, parent_part: str | None = None
  ) -> str:
    uimessage = robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            object_reparent_request=robotics_ui_pb2.ObjectReparentRequest(
                object_id=object_id,
                parent_id=parent_id,
                parent_part=parent_part,
            )
        ),
    )
    return self._send_message(uimessage)

  def _ping(self) -> None:
    """Sends a ping, which will update the last ping latency."""
    message_id = str(uuid.uuid4())
    ping_time = time.time_ns()
    self.pings[message_id] = ping_time
    for client in self.clients:
      client.send_message(
          robotics_ui_pb2.RuiMessage(
              message_id=message_id,
              ui_message=robotics_ui_pb2.UIMessage(ping=robotics_ui_pb2.Ping()),
          )
      )

  def get_last_ping_latency_nsec(self) -> int:
    now = time.time_ns()
    with self.ping_lock:
      if now - self.last_pong_time > 10_000_000_000:
        return 999999999999
      return self.last_ping_latency

  def set_image_rate_throttling(self, rate_hz: float) -> None:
    self.image_send_min_interval = int(1000000000 / rate_hz)

  def _should_throttle_image(self, now_nsec: int) -> bool:
    """Returns whether the image should be throttled."""
    return (
        self.image_send_min_interval != 0
        and now_nsec - self.last_image_send_time < self.image_send_min_interval
    )

  def send_jpeg_image(
      self,
      camera_index: int,
      jpeg_image: bytes,
      cols: int = 0,
      rows: int = 0,
      sample_timestamp_nsec: int = 0,
      seq: int = 0,
      sensor_id: int | None = None,
      publish_timestamp_nsec: int = 0,
      client_id: robot_types_pb2.ClientID | None = None,
  ) -> str:
    if self.stop_event.is_set() or not self.connected_event.is_set():
      logging.warning("send_jpeg_image: RoboticsUI not connected or stopped.")
      return "RoboticsUI not connected or stopped."
    jpeg_camera_image_data: list[JpegCameraImageData | None] = []
    for _ in range(camera_index):
      jpeg_camera_image_data.append(None)
    jpeg_camera_image_data.append(
        JpegCameraImageData(
            jpeg_image=jpeg_image,
            cols=cols,
            rows=rows,
            sample_timestamp_nsec=sample_timestamp_nsec,
            seq=seq,
            sensor_id=sensor_id,
        )
    )

    return self.send_jpeg_images(
        jpeg_camera_image_data,
        publish_timestamp_nsec=publish_timestamp_nsec,
        client_id=client_id,
    )

  def send_jpeg_images(
      self,
      jpeg_camera_image_data: list[JpegCameraImageData | None],
      publish_timestamp_nsec: int = 0,
      client_id: robot_types_pb2.ClientID | None = None,
  ) -> str:
    if self.stop_event.is_set() or not self.connected_event.is_set():
      logging.warning("send_jpeg_images: RoboticsUI not connected or stopped.")
      return "RoboticsUI not connected or stopped."
    now_nsec = time.time_ns()
    if self._should_throttle_image(now_nsec):
      return ""
    self.last_image_send_time = now_nsec

    message_id = str(uuid.uuid4())
    if client_id is None:
      client_id = robot_types_pb2.ClientID()
    if publish_timestamp_nsec == 0:
      publish_timestamp_nsec = now_nsec

    camera_images: list[robot_state_pb2.CameraImage] = []
    sample_timestamp_nsec = 0
    for camera_index, data in enumerate(jpeg_camera_image_data):
      if data is None:
        camera_images.append(robot_state_pb2.CameraImage())
        continue
      camera_image = data.construct_camera_data()
      if camera_image.header.sensor_id == -1:
        camera_image.header.sensor_id = camera_index
      if camera_image.header.sample_timestamp_nsec > sample_timestamp_nsec:
        sample_timestamp_nsec = camera_image.header.sample_timestamp_nsec
      camera_images.append(camera_image)

    if sample_timestamp_nsec == 0:
      sample_timestamp_nsec = now_nsec

    header = robot_types_pb2.MessageHeader(
        sample_timestamp_nsec=sample_timestamp_nsec,
        publish_timestamp_nsec=publish_timestamp_nsec,
        client_id=client_id,
    )

    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=message_id,
            xemb_message=xemb_pb2.XembMessage(
                robot_state=robot_state_pb2.RobotState(
                    header=header,
                    parts=robot_state_pb2.PartsState(
                        world=robot_state_pb2.PartState(cameras=camera_images)
                    ),
                ),
                client_id=client_id,
            ),
        )
    )

  def create_or_update_text(
      self,
      text_id: str,
      text: str,
      spec: robotics_ui_pb2.UISpec | None = None,
      scrollable: bool = False,
  ) -> str:
    return self._send_message(
        self.create_text_message(text_id, text, spec, scrollable)
    )

  def remove_element(self, element_id: str) -> str:
    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                remove_gui_element_request=robotics_ui_pb2.RemoveGuiElementRequest(
                    element_id=element_id,
                )
            ),
        )
    )

  def create_chat(
      self,
      chat_id: str,
      title: str,
      interactive: bool = False,
      submit_label: str | None = None,
      spec: robotics_ui_pb2.UISpec | None = None,
  ) -> str:
    if spec is None:
      spec = robotics_ui_pb2.UISpec(width=0.3, height=0.3, x=0.5, y=0.5)
    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                chat_create_request=robotics_ui_pb2.ChatCreateRequest(
                    chat_id=chat_id,
                    title=title,
                    interactive=interactive,
                    submit_label=submit_label,
                    spec=spec,
                )
            ),
        )
    )

  def add_chat_line(self, chat_id: str, text: str) -> str:
    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                add_chat_line=robotics_ui_pb2.AddChatLine(
                    chat_id=chat_id,
                    text=text,
                )
            ),
        )
    )

  def embody(self, robot_id: str) -> str:
    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                embody_request=robotics_ui_pb2.EmbodyRequest(
                    robot_id=robot_id,
                )
            ),
        )
    )

  def create_embodiable_pseudo_robot(
      self, robot_id: str, origin_object_id: str, head_object_id: str
  ) -> str:
    return self.create_or_update_object(
        object_id=robot_id,
        robot_id=robot_id,
        object_type=robotics_ui_pb2.ObjectType.ROBOT_PSEUDO_EMBODIABLE,
        embodiable_robot_params=robotics_ui_pb2.EmbodiableRobotParams(
            origin_object_id=origin_object_id,
            head_object_id=head_object_id,
        ),
    )

  def setup_header(
      self,
      height: float,
      visible: bool,
      collapsible: bool,
      expandable: bool,
      screen_scaling: bool = False,
      # TODO: Remove auto-assignment of screen_scaling once the other
      # test scripts are updated.
  ) -> str:
    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                setup_header_request=robotics_ui_pb2.SetupHeaderRequest(
                    height=height,
                    visible=visible,
                    collapsible=collapsible,
                    expandable=expandable,
                    screen_scaling=screen_scaling,
                )
            ),
        )
    )

  def create_toggle(
      self,
      toggle_id: str,
      label: str,
      msg: str | None = None,
      title: str | None = None,
      submit_label: str | None = None,
      initial_value: bool | None = None,
      spec: robotics_ui_pb2.UISpec | None = None,
  ) -> _internal.CallbackData:
    uimessage = self.create_toggle_message(
        toggle_id=toggle_id,
        label=label,
        msg=msg,
        title=title,
        submit_label=submit_label,
        initial_value=initial_value,
        spec=spec,
    )
    self._send_message(uimessage)
    return _internal.CallbackData(
        toggle_id, _internal.ElementType.TOGGLE, ""
    )

  def send_button_pressed_event(self, button_id: str) -> str:
    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                button_pressed_event=robotics_ui_pb2.ButtonPressedEvent(
                    button_id=button_id,
                )
            ),
        )
    )

  def send_prompt_pressed_event(self, prompt_id: str, text_input: str) -> str:
    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                prompt_pressed_event=robotics_ui_pb2.PromptPressedEvent(
                    prompt_id=prompt_id,
                    input=text_input,
                )
            ),
        )
    )

  def send_dialog_pressed_event(self, dialog_id: str, choice: str) -> str:
    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                dialog_pressed_event=robotics_ui_pb2.DialogPressedEvent(
                    dialog_id=dialog_id,
                    choice=choice,
                )
            ),
        )
    )

  def send_dropdown_pressed_event(
      self, dropdown_id: str, choice: str | list[str]
  ) -> str:
    if isinstance(choice, list):
      dropdown_pressed_event = robotics_ui_pb2.DropdownPressedEvent(
          dropdown_id=dropdown_id,
          choices=choice,
      )
    else:
      dropdown_pressed_event = robotics_ui_pb2.DropdownPressedEvent(
          dropdown_id=dropdown_id,
          choice=choice,
      )
    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                dropdown_pressed_event=dropdown_pressed_event
            ),
        )
    )

  def send_toggle_pressed_event(
      self, toggle_id: str, selected: bool
  ) -> str:
    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                toggle_pressed_event=robotics_ui_pb2.TogglePressedEvent(
                    toggle_id=toggle_id,
                    selected=selected,
                )
            ),
        )
    )

  def _handle_upload_kinematic_tree_robot_response(
      self,
      _: str,
      ui_message: robotics_ui_pb2.UIMessage,
  ) -> None:
    """Handles an UploadKinematicTreeRobotResponse."""
    response = ui_message.upload_kinematic_tree_robot_response
    self.callbacks.kinematic_tree_robot_uploaded(
        response.kinematic_tree_robot_id,
        response.success,
        response.error_message,
    )

  def upload_file(self, path: types.PathLike) -> str:
    return self._upload_engine.upload_file(path)

  def upload_resource(self, locator: types.ResourceLocator) -> str:
    return self._upload_engine.upload_resource(locator)

  def _handle_get_resource_request(
      self,
      _: str,
      ui_message: robotics_ui_pb2.UIMessage,
  ) -> None:
    """Handles a GetResourceRequest."""
    locator = ui_message.get_resource_request.locator
    logging.debug("Get resource request for %s", locator.uri)
    if locator.mime_type == types.MIME_TYPE_WTF:
      self._give_mesh_resource(locator)
    else:
      raise exceptions.FileUploadError(
          f"Unsupported mime type for GetResourceRequest: {locator.mime_type}"
      )

  def _give_mesh_resource(
      self, locator: robotics_ui_pb2.ResourceLocator
  ) -> None:
    """Gives the mesh resource to the client."""
    try:
      mesh = self._stl_parser_from_locator(locator)
    except FileNotFoundError as e:
      raise exceptions.FileUploadError(
          f"Failed to find STL file at {locator.uri}"
      ) from e
    except exceptions.StlParseError as e:
      raise exceptions.FileUploadError(
          f"Failed to parse STL file at {locator.uri}"
      ) from e

    logging.debug(
        "Sending mesh resource to client (%d verts, %d tris)",
        len(mesh.vertices),
        len(mesh.triangles),
    )
    self.send_raw_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                get_resource_response=robotics_ui_pb2.GetResourceResponse(
                    locator=locator,
                    wire_triangle_format=mesh,
                )
            ),
        )
    )

  def upload_stl_file(self, path: types.PathLike) -> str:
    try:
      mesh = self._stl_parser(path)
    except FileNotFoundError as e:
      raise exceptions.FileUploadError(
          f"Failed to find STL file at {path}"
      ) from e
    except exceptions.StlParseError as e:
      raise exceptions.FileUploadError(
          f"Failed to parse STL file at {path}"
      ) from e
    return self._upload_engine.upload_resource(
        types.ResourceLocator(
            scheme="mesh",
            path=path,
            data=mesh.SerializeToString(deterministic=True),
        )
    )

  def upload_zipped_kinematic_tree_robot(
      self,
      kinematic_tree_robot_id: str,
      zip_path: str,
      xml_path: str,
      timeout: datetime.timedelta,
  ) -> None:
    try:
      kinematic_tree = kinematic_tree_robot.KinematicTree.parse_from_zip(
          kinematic_tree_robot_id,
          zip_path,
          xml_path,
      )
    except ValueError as e:
      raise exceptions.KinematicTreeRobotUploadError(
          f"Failed to parse zip file at {zip_path}"
      ) from e

    job = kinematic_tree_robot.UploadRobotJob(self, timeout, kinematic_tree)
    job.start()

  def upload_kinematic_tree_robot(
      self,
      kinematic_tree_robot_id: str,
      xml_path: types.PathLike,
      joint_mapping: dict[robot_frames_pb2.Frame.Enum, list[str]],
      timeout: datetime.timedelta,
      origin_site: types.BodySiteSpec | None = None,
      embody_site: types.BodySiteSpec | None = None,
  ) -> None:
    try:
      kinematic_tree = kinematic_tree_robot.KinematicTree.parse(
          kinematic_tree_robot_id,
          xml_path,
          joint_mapping,
          origin_site=origin_site,
          embody_site=embody_site,
      )
    except ValueError as e:
      raise exceptions.KinematicTreeRobotUploadError(
          f"Failed to parse mujoco XML file at {xml_path}"
      ) from e

    job = kinematic_tree_robot.UploadRobotJob(self, timeout, kinematic_tree)
    job.start()

  def send_console_command(self, command: str) -> str:
    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(console_command=command),
        )
    )

  def create_form(
      self,
      form_id: str,
      title: str,
      submit_label: str | None,
      spec: robotics_ui_pb2.UISpec | None,
      create_requests: list[robotics_ui_pb2.RuiMessage],
  ) -> _internal.CallbackData:
    self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                form_create_request=robotics_ui_pb2.FormCreateRequest(
                    form_id=form_id,
                    title=title,
                    submit_label=submit_label,
                    spec=spec,
                    create_requests=create_requests,
                )
            ),
        )
    )
    return _internal.CallbackData(form_id, _internal.ElementType.FORM, "")

  def create_button_message(
      self,
      button_id: str,
      label: str,
      shortcuts: list[str] | None,
      spec: robotics_ui_pb2.UISpec | None = None,
  ) -> robotics_ui_pb2.RuiMessage:
    return robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            button_create_request=robotics_ui_pb2.ButtonCreateRequest(
                spec=spec,
                button_id=button_id,
                label=label,
                shortcut=shortcuts,
            )
        ),
    )

  def create_prompt_message(
      self,
      prompt_id: str,
      title: str,
      msg: str,
      submit_label: str,
      spec: robotics_ui_pb2.UISpec | None = None,
      multiline_input: bool = False,
      initial_value: str | None = None,
      autofill_values: list[str] | None = None,
  ) -> robotics_ui_pb2.RuiMessage:
    return robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            prompt_create_request=robotics_ui_pb2.PromptCreateRequest(
                prompt_id=prompt_id,
                title=title,
                msg=msg,
                submit_label=submit_label,
                multiline_input=multiline_input,
                spec=spec,
                initial_value=initial_value,
                autofill_values=autofill_values,
            )
        ),
    )

  def create_dropdown_message(
      self,
      dropdown_id: str,
      title: str,
      msg: str,
      choices: list[str],
      submit_label: str,
      spec: robotics_ui_pb2.UISpec | None = None,
      initial_value: str | None = None,
      multi_select: bool = False,
      initial_values: list[str] | None = None,
      shortcuts: dict[str, str] | None = None,
  ) -> robotics_ui_pb2.RuiMessage:
    return robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            dropdown_create_request=robotics_ui_pb2.DropdownCreateRequest(
                dropdown_id=dropdown_id,
                title=title,
                msg=msg,
                choices=choices,
                submit_label=submit_label,
                spec=spec,
                initial_value=initial_value,
                multi_select=multi_select,
                initial_values=initial_values,
                shortcuts=shortcuts,
            )
        ),
    )

  def create_text_message(
      self,
      text_id: str,
      text: str,
      spec: robotics_ui_pb2.UISpec | None = None,
      scrollable: bool = False,
  ) -> robotics_ui_pb2.RuiMessage:
    return robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            text_create_or_update_request=robotics_ui_pb2.TextCreateOrUpdateRequest(
                text_id=text_id,
                text=text,
                spec=spec,
                scrollable=scrollable,
            )
        ),
    )

  def create_row_message(
      self,
      create_requests: list[robotics_ui_pb2.RuiMessage],
      spec: robotics_ui_pb2.UISpec | None = None,
  ) -> robotics_ui_pb2.RuiMessage:
    return robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            row_create_request=robotics_ui_pb2.RowCreateRequest(
                create_requests=create_requests,
                spec=spec,
            )
        ),
    )

  def create_toggle_message(
      self,
      toggle_id: str,
      label: str,
      msg: str | None = None,
      title: str | None = None,
      submit_label: str | None = None,
      initial_value: bool | None = None,
      spec: robotics_ui_pb2.UISpec | None = None,
  ) -> robotics_ui_pb2.RuiMessage:
    return robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.uuid4()),
        ui_message=robotics_ui_pb2.UIMessage(
            toggle_create_request=robotics_ui_pb2.ToggleCreateRequest(
                toggle_id=toggle_id,
                label=label,
                msg=msg,
                submit_label=submit_label,
                initial_value=initial_value,
                title=title,
                spec=spec,
            )
        ),
    )

  def register_remote_command(self, command: str, desc: str):
    self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                register_remote_command=robotics_ui_pb2.RegisterRemoteCommand(
                    command=command,
                    description=desc,
                )
            ),
        )
    )

  def unregister_remote_command(self, command: str):
    self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                unregister_remote_command=robotics_ui_pb2.UnregisterRemoteCommand(
                    command=command
                )
            ),
        )
    )

  def register_client_name(self, client_name: str) -> None:
    """Sends the client name to the server."""
    for client in self.clients:
      if not isinstance(client, _internal.TcpUiClient):
        logging.error(
            "Register client name %s is only for TCP clients.", client_name
        )
        return

      try:
        client_ip = client.ip_socket.getsockname()[0]
        client_port = client.ip_socket.getsockname()[1]
      except OSError as e:
        logging.error("Failed to get client socket name: %s", e)
        return
      logging.debug(
          "Registered client %s with %s:%s.",
          client_name,
          client_ip,
          str(client_port),
      )
      self._send_message(
          robotics_ui_pb2.RuiMessage(
              message_id=str(uuid.uuid4()),
              ui_message=robotics_ui_pb2.UIMessage(
                  register_client_name=robotics_ui_pb2.RegisterClientName(
                      client_name=client_name,
                      client_ip=client_ip,
                      client_port=client_port,
                  )
              ),
          )
      )

  def add_alert(self, alert_id: str, text: str, show: bool = False) -> str:
    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                alert_create_request=robotics_ui_pb2.AlertCreateRequest(
                    alert_id=alert_id,
                    text=text,
                    show=show,
                )
            ),
        )
    )

  def remove_alert(self, alert_id: str) -> str:
    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                alert_remove_request=robotics_ui_pb2.AlertRemoveRequest(
                    alert_id=alert_id
                )
            ),
        )
    )

  def clear_alerts(self) -> str:
    return self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                alert_clear_request=robotics_ui_pb2.AlertClearRequest()
            ),
        )
    )

  def set_minimized(self, element_id: str, minimized: bool) -> None:
    self._send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                set_minimized_request=robotics_ui_pb2.SetMinimizedRequest(
                    element_id=element_id,
                    minimized=minimized,
                )
            ),
        )
    )
