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

"""Unit tests for _internal.TCPUiClient."""

import socket
import struct
import time
from unittest import mock
import uuid

from absl.testing import absltest
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui.client import _internal

FAKE_NSEC_VALUE = 98765


class InternalTcpUiClientTest(absltest.TestCase):

  def test_connect(self):
    mock_socket = mock.create_autospec(socket.socket, instance=True)
    tcp_client = _internal.TcpUiClient(socket_provider=lambda: mock_socket)

    tcp_client.connect("host", 12345)

    mock_socket.connect.assert_called_once_with(("host", 12345))

  def test_disconnect(self):
    mock_socket = mock.create_autospec(socket.socket, instance=True)
    tcp_client = _internal.TcpUiClient(socket_provider=lambda: mock_socket)
    tcp_client.connect("host", 12345)

    tcp_client.disconnect()

    self.assertTrue(
        tcp_client.disconnected.wait(1),
        "disconnected was not set, but should have been",
    )
    mock_socket.close.assert_called_once()
    self.assertTrue(
        tcp_client.is_disconnected(),
        "is_disconnected() returned False, but should have been True",
    )

  def test_wait_for_message(self):
    message = robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.UUID(int=1)),
        ui_message=robotics_ui_pb2.UIMessage(console_data="console_data"),
    )
    message_data = message.SerializeToString()
    message_len = len(message_data)

    mock_socket = mock.create_autospec(socket.socket, instance=True)
    mock_socket.recv.side_effect = [
        struct.pack("<i", message_len),
        message_data,
    ]

    tcp_client = _internal.TcpUiClient(socket_provider=lambda: mock_socket)
    tcp_client.connect("host", 12345)

    self.assertEqual(tcp_client.wait_for_message(), message)
    self.assertTrue(
        tcp_client.is_live(),
        "is_live() returned False, but should have been True",
    )

  def test_wait_for_message_list(self):
    message = robotics_ui_pb2.RuiMessageList(
        messages=[
            robotics_ui_pb2.RuiMessage(
                message_id=str(uuid.UUID(int=1)),
                ui_message=robotics_ui_pb2.UIMessage(
                    console_data="console_data"
                ),
            ),
            robotics_ui_pb2.RuiMessage(
                message_id=str(uuid.UUID(int=2)),
                ui_message=robotics_ui_pb2.UIMessage(
                    console_data="console_data2"
                ),
            ),
        ]
    )
    message_data = message.SerializeToString()
    message_len = len(message_data)

    mock_socket = mock.create_autospec(socket.socket, instance=True)
    mock_socket.recv.side_effect = [
        struct.pack("<i", -message_len),  # Negative len indicates message list
        message_data,
    ]

    tcp_client = _internal.TcpUiClient(socket_provider=lambda: mock_socket)
    tcp_client.connect("host", 12345)

    self.assertEqual(tcp_client.wait_for_message(), message)

  def test_wait_for_message_ignores_undecodable_message(self):
    message = robotics_ui_pb2.RuiMessage(
        message_id=str(uuid.UUID(int=1)),
        ui_message=robotics_ui_pb2.UIMessage(console_data="console_data"),
    )
    message_data = message.SerializeToString()
    message_len = len(message_data)

    mock_socket = mock.create_autospec(socket.socket, instance=True)
    mock_socket.recv.side_effect = [
        struct.pack("<i", 1),
        b"1",  # Undecodable message
        struct.pack("<i", -1),
        b"1",  # Undecodable message
        struct.pack("<i", message_len),
        message_data,
    ]

    tcp_client = _internal.TcpUiClient(socket_provider=lambda: mock_socket)
    tcp_client.connect("host", 12345)

    self.assertEqual(tcp_client.wait_for_message(), message)
    self.assertTrue(
        tcp_client.is_live(),
        "is_live() returned False, but should have been True",
    )

  def test_wait_for_message_disconnected_without_exception(self):
    mock_socket = mock.create_autospec(socket.socket, instance=True)
    mock_socket.recv.side_effect = [
        b"",  # Disconnects
    ]

    tcp_client = _internal.TcpUiClient(socket_provider=lambda: mock_socket)
    tcp_client.connect("host", 12345)

    self.assertIsNone(tcp_client.wait_for_message())

  def test_wait_for_message_disconnected_with_exception(self):
    mock_socket = mock.create_autospec(socket.socket, instance=True)
    mock_socket.recv.side_effect = [
        OSError(),
    ]

    tcp_client = _internal.TcpUiClient(socket_provider=lambda: mock_socket)
    tcp_client.connect("host", 12345)

    self.assertIsNone(tcp_client.wait_for_message())

  def test_send_message(self):
    self.enter_context(
        mock.patch.object(time, "time_ns", autospec=True)
    ).return_value = FAKE_NSEC_VALUE

    mock_socket = mock.create_autospec(socket.socket, instance=True)
    message_id = str(uuid.UUID(int=1))
    message = robotics_ui_pb2.RuiMessage(
        message_id=message_id,
        ui_message=robotics_ui_pb2.UIMessage(console_data="console_data"),
    )

    tcp_client = _internal.TcpUiClient(socket_provider=lambda: mock_socket)
    tcp_client.connect("host", 12345)

    self.assertEqual(tcp_client.send_message(message), message_id)

    expected_message = robotics_ui_pb2.RuiMessage()
    expected_message.CopyFrom(message)
    expected_message.sent_timestamp_nsec = FAKE_NSEC_VALUE
    expected_message_data = expected_message.SerializeToString()
    expected_buf = (
        struct.pack("<i", len(expected_message_data)) + expected_message_data
    )
    mock_socket.sendall.assert_called_once_with(expected_buf)

  def test_send_message_exception(self):
    self.enter_context(
        mock.patch.object(time, "time_ns", autospec=True)
    ).return_value = FAKE_NSEC_VALUE

    mock_socket = mock.create_autospec(socket.socket, instance=True)
    mock_socket.sendall.side_effect = [
        OSError(),
    ]
    message_id = str(uuid.UUID(int=1))
    message = robotics_ui_pb2.RuiMessage(
        message_id=message_id,
        ui_message=robotics_ui_pb2.UIMessage(console_data="console_data"),
    )

    tcp_client = _internal.TcpUiClient(socket_provider=lambda: mock_socket)
    tcp_client.connect("host", 12345)

    self.assertEqual(tcp_client.send_message(message), "")


if __name__ == "__main__":
  absltest.main()
