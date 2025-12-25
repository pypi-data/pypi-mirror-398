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

"""A server that acts as a RoboticsUI."""

import abc
import socket
import threading

from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui.client import _internal


class TcpServer(_internal.TcpUiClient):
  """A TCP server that acts as a RoboticsUI.

  Users should subclass this and implement message_received(). Call
  send_message() to send a message to the connected client.
  """

  server_socket: socket.socket
  host: str
  port: int
  stop_signal: threading.Event
  connected: threading.Event

  def __init__(self, port):
    super().__init__()
    self.host = "0.0.0.0"  # Listen on all available interfaces
    self.port = port
    self.stop_signal = threading.Event()
    self.connected = threading.Event()

  def send_pong(self, message_id: str) -> None:
    """Sends a pong message."""
    self.send_message(
        robotics_ui_pb2.RuiMessage(
            message_id=message_id,
            ui_message=robotics_ui_pb2.UIMessage(pong=robotics_ui_pb2.Pong()),
        )
    )

  def accept_connection(self) -> None:
    """Accepts a new connection."""
    print("Waiting for connection...")
    self.ip_socket, addr = self.server_socket.accept()
    with self.ip_socket:
      print(f"Connection from {addr}")
      self.connected.set()

      while not self.stop_signal.is_set():
        msg = self.wait_for_message()
        if msg is None:
          break
        if isinstance(msg, robotics_ui_pb2.RuiMessage):
          messages = [msg]
        elif isinstance(msg, robotics_ui_pb2.RuiMessageList):
          messages = msg.messages
        else:
          raise ValueError(f"Unknown message type: {type(msg)}")

        for m in messages:
          if m.HasField("ui_message") and m.ui_message.HasField("ping"):
            self.send_pong(m.message_id)
          else:
            self.message_received(m)

    print(f"Disconnected from {addr}")

  def _serve(self) -> None:
    """Handles serving."""
    self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server_socket.bind((self.host, self.port))
    self.server_socket.listen()
    while not self.stop_signal.is_set():
      self.connected.clear()
      self.accept_connection()

  def start_serve(self) -> None:
    """Starts serving in a separate thread."""
    threading.Thread(target=self._serve, daemon=True).start()

  def stop_serve(self) -> None:
    """Stops serving."""
    self.server_socket.close()
    self.stop_signal.set()
    print("Server stop requested.")

  def send_message(self, message: robotics_ui_pb2.RuiMessage) -> str:
    """Sends a message to the connected client.

    Will silently drop the message if no client is connected.

    Args:
      message: The message to send.

    Returns:
      The message ID of the sent message.
    """
    if not self.connected.is_set():
      return ""
    return super().send_message(message)

  @abc.abstractmethod
  def message_received(self, message: robotics_ui_pb2.RuiMessage) -> None:
    """Called when a message is received."""
