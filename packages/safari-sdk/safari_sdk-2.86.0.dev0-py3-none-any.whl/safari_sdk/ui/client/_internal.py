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

"""Internals for the Robotics UI."""

import abc
import dataclasses
import enum
import logging
import socket
import statistics
import struct
import threading
import time
from typing import Callable

from google.protobuf import message as message_lib

from safari_sdk.protos.ui import robotics_ui_pb2

CallbackReturnValue = str | list[str] | bool


@enum.unique
class ElementType(enum.IntEnum):
  UNKNOWN = 0
  BUTTON = 1
  DIALOG = 2
  PROMPT = 3
  DROPDOWN = 4
  FORM = 5
  TOGGLE = 6


@dataclasses.dataclass
class CallbackData:
  element_id: str
  element_type: ElementType
  return_value: CallbackReturnValue


class UiClientInterface(abc.ABC):
  """An interface for a Robotics UI client."""

  @abc.abstractmethod
  def connect(self, host: str, port: int) -> None:
    """Connects to the given host and port."""

  @abc.abstractmethod
  def disconnect(self) -> None:
    """Disconnects from the server."""

  @abc.abstractmethod
  def is_disconnected(self) -> bool:
    """Returns whether the client has been disconnected.

    Note that is_disconnected() will return False if the client has not been
    connected to yet.
    """

  @abc.abstractmethod
  def wait_for_message(
      self,
  ) -> robotics_ui_pb2.RuiMessage | robotics_ui_pb2.RuiMessageList | None:
    """Blocking receives an RuiMessage or RuiMessageList."""

  @abc.abstractmethod
  def send_message(self, msg: robotics_ui_pb2.RuiMessage) -> str:
    """Sends an RuiMessage, returning the message ID."""

  @abc.abstractmethod
  def report_stats(self, last_message_report_ns: int) -> None:
    """Reports stats on the received message.

    Args:
      last_message_report_ns: The time the last message report was sent, in
        nanoseconds since the epoch.

    Returns:
      Nothing.
    """

  @abc.abstractmethod
  def is_live(self) -> bool:
    """Returns whether the connection is live.

    Liveness means that the connection is up, and at least one message has been
    received.
    """

  @abc.abstractmethod
  def get_version_report(self) -> robotics_ui_pb2.VersionReport:
    """Returns the latest version report for the connection.

    This is guaranteed to be up to date when the connection is live, if the
    connection supports version reporting, as it is the first message sent by
    the server. Otherwise the version report is the default instance, with
    connection_ip and connection_port set to the host and port that the client
    connected to.
    """


class TcpUiClient(UiClientInterface):
  """A TCP UI client."""

  send_mutex: threading.Lock
  disconnected: threading.Event
  ip_socket: socket.socket
  collect_stats: bool
  last_message_latencies_10s: list[int]
  num_messages_sent: int
  num_messages_received: int
  socket_provider: Callable[[], socket.socket] | None
  _latest_version_report: robotics_ui_pb2.VersionReport
  _latest_version_report_mutex: threading.Lock
  _connection_ip: str
  _connection_port: int

  # Event for when a message was received on the connection. Used to signal
  # that at least one message was received from the RoboticsUI, meaning that
  # the connection is alive.
  _received_event: threading.Event

  def __init__(
      self,
      collect_stats: bool = False,
      socket_provider: Callable[[], socket.socket] | None = None,
  ):
    self.send_mutex = threading.Lock()
    self.disconnected = threading.Event()
    self.collect_stats = collect_stats
    self.last_message_latencies_10s = []
    self.last_avg_message_latency_ns = 0
    self.num_messages_sent = 0
    self.num_messages_received = 0
    if socket_provider is None:
      self.socket_provider = lambda: socket.socket(
          socket.AF_INET, socket.SOCK_STREAM
      )
    else:
      self.socket_provider = socket_provider
    self._received_event = threading.Event()
    self._latest_version_report = robotics_ui_pb2.VersionReport()
    self._latest_version_report_mutex = threading.Lock()

  def connect(self, host: str, port: int) -> None:
    self.ip_socket = self.socket_provider()
    self.ip_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    self.ip_socket.connect((host, port))
    self._connection_ip = host
    self._connection_port = port
    with self._latest_version_report_mutex:
      self._latest_version_report = robotics_ui_pb2.VersionReport(
          connection_ip=host,
          connection_port=port,
      )

  def disconnect(self) -> None:
    self.disconnected.set()
    self.ip_socket.close()

  def is_disconnected(self) -> bool:
    return self.disconnected.is_set()

  def recvall(self, nbytes: int) -> bytes | None:
    """Receive exactly nbytes from the socket.

    Args:
      nbytes: The number of bytes to receive.

    Returns:
      The bytes received, or None if the socket disconnected.
    """
    bytes_received = 0
    chunks = []
    while bytes_received < nbytes:
      chunk = self.ip_socket.recv(nbytes - bytes_received)
      if not chunk:  # Server disconnected
        return None
      chunks.append(chunk)
      bytes_received += len(chunk)
    return b"".join(chunks)

  def _report_latencies(self) -> None:
    """Reports the message latencies."""
    if len(self.last_message_latencies_10s) < 2:
      logging.debug("No message latency data.")
      return

    avg_ns = statistics.mean(self.last_message_latencies_10s)
    avg = (avg_ns - self.last_avg_message_latency_ns) // 1000
    stddev = statistics.stdev(self.last_message_latencies_10s) // 1000
    minimum = (
        min(self.last_message_latencies_10s)
        - self.last_avg_message_latency_ns
    ) // 1000
    maximum = (
        max(self.last_message_latencies_10s)
        - self.last_avg_message_latency_ns
    ) // 1000
    logging.debug(
        "Message latency (usec) DELTA avg: %d stddev: %d DELTA min:"
        " %d DELTA max: %d",
        avg,
        stddev,
        minimum,
        maximum,
    )

    self.last_avg_message_latency_ns = avg_ns
    self.last_message_latencies_10s = []

  def report_stats(self, last_message_report_ns: int) -> None:
    """Reports stats on the received message.

    Args:
      last_message_report_ns: The time the last message report was sent, in
        nanoseconds since the epoch.

    Returns:
      Nothing.
    """
    with self.send_mutex:
      self._report_latencies()
      stat_interval_ns = time.time_ns() - last_message_report_ns
      avg_sent = self.num_messages_sent // (stat_interval_ns / 1e9)
      avg_rcvd = self.num_messages_received // (stat_interval_ns / 1e9)
      logging.debug(
          "Sent %d msgs/sec, received %d msgs/sec", avg_sent, avg_rcvd
      )

      self.num_messages_sent = 0
      self.num_messages_received = 0

  def _receive_encoded_message(self) -> tuple[bytes | None, bool]:
    """Receives an encoded message from the socket.

    Returns:
      A tuple of (bytes, bool) where the bytes are the encoded message, and the
      bool is True if the message is a list of encoded messages, False
      otherwise.

      If the server disconnected, returns (None, False).
    """
    try:
      data = self.recvall(4)  # Receive a response
      if not data:  # Server disconnected
        return None, False
      size_value = struct.unpack("<i", data[:4])[0]
      is_list = False
      if size_value < 0:
        is_list = True
        size_value = -size_value

      received_proto_data = self.recvall(size_value)
      return received_proto_data, is_list

    except OSError:
      if not self.disconnected.is_set():
        logging.error(
            "Exception in wait_for_message", stack_info=True, exc_info=True
        )
      return None, False

  def _decode_received_message(
      self, received_proto_data: bytes, is_list: bool
  ) -> tuple[
      robotics_ui_pb2.RuiMessage | robotics_ui_pb2.RuiMessageList | None, int
  ]:
    """Decodes a received message.

    Args:
      received_proto_data: The encoded message.
      is_list: Whether the message is a list of encoded messages.

    Returns:
      A tuple of (RuiMessage, int) where the RuiMessage is the decoded message,
      and the int is the timestamp of the message in nanoseconds since the
      epoch.

      If the message couldn't be decoded, returns (None, 0).
    """
    try:
      if is_list:
        received_rui_message = robotics_ui_pb2.RuiMessageList()
        received_rui_message.ParseFromString(received_proto_data)
        if received_rui_message.messages:
          sent_timestamp_nsec = received_rui_message.messages[
              0
          ].sent_timestamp_nsec
        else:
          sent_timestamp_nsec = time.time_ns()

        return received_rui_message, sent_timestamp_nsec

      received_rui_message = robotics_ui_pb2.RuiMessage()
      received_rui_message.ParseFromString(received_proto_data)
      sent_timestamp_nsec = received_rui_message.sent_timestamp_nsec
      if received_rui_message.HasField(
          "ui_message"
      ) and received_rui_message.ui_message.HasField("version_report"):
        with self._latest_version_report_mutex:
          self._latest_version_report = (
              received_rui_message.ui_message.version_report
          )
          self._latest_version_report.connection_ip = self._connection_ip
          self._latest_version_report.connection_port = self._connection_port
      return received_rui_message, sent_timestamp_nsec

    except message_lib.DecodeError:
      logging.error(
          "Message decode error in wait_for_message (ignoring)",
          stack_info=True,
          exc_info=True,
      )
      return None, 0

  def wait_for_message(
      self,
  ) -> robotics_ui_pb2.RuiMessage | robotics_ui_pb2.RuiMessageList | None:
    while True:
      received_proto_data, is_list = self._receive_encoded_message()
      if received_proto_data is None:
        return None  # Server disconnected, return immediately.

      received_rui_message, sent_timestamp_nsec = self._decode_received_message(
          received_proto_data, is_list
      )

      # If we get a valid encoded message, but the message cannot be decoded,
      # it's likely that we got sent a newer message that we were compiled for.
      # In that case, we just report it, drop the message, and keep going.
      if received_rui_message is not None:
        break

    if self.collect_stats:
      with self.send_mutex:
        self.num_messages_received += 1
        self.last_message_latencies_10s.append(
            time.time_ns() - sent_timestamp_nsec
        )

    self._received_event.set()
    return received_rui_message

  def send_message(self, msg: robotics_ui_pb2.RuiMessage) -> str:
    msg.sent_timestamp_nsec = time.time_ns()
    messagelength = len(msg.SerializeToString())

    # If we ever send a message list, negate the messagelength so the server
    # knows it's a list.

    buf = struct.pack("<i", messagelength) + msg.SerializeToString()
    try:
      with self.send_mutex:
        self.ip_socket.sendall(buf)  # Send the message
        self.num_messages_sent += 1
      return msg.message_id

    except OSError:
      if not self.disconnected.is_set():
        logging.error(
            "Exception in send_message", stack_info=True, exc_info=True
        )
      return ""

  def is_live(self) -> bool:
    return self._received_event.is_set()

  def get_version_report(self) -> robotics_ui_pb2.VersionReport:
    with self._latest_version_report_mutex:
      return self._latest_version_report
