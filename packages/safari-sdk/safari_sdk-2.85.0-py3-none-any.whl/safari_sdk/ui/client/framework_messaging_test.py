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

"""Unit tests for framework messaging."""

from __future__ import annotations

import queue
import time
from unittest import mock
import uuid

from absl.testing import absltest
from absl.testing import parameterized
from safari_sdk.protos.ui import robot_state_pb2
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui import client
from safari_sdk.ui.client import _internal

FAKE_NSEC_VALUE = 98765
UiClientInterface = _internal.UiClientInterface


class UiTest(parameterized.TestCase):
  fake_uuid = 0
  queued_messages: queue.Queue[
      robotics_ui_pb2.RuiMessage | robotics_ui_pb2.RuiMessageList | None
  ]
  queue_enabled: bool
  kill_connections: bool
  mock_callbacks: client.UiCallbacks

  def _generate_fake_uuid(self) -> uuid.UUID:
    self.fake_uuid += 1
    return uuid.UUID(int=self.fake_uuid)

  def _respond_to_wait_for_message(
      self, *args, **kwargs
  ) -> robotics_ui_pb2.RuiMessage | robotics_ui_pb2.RuiMessageList | None:
    """Returns a queued message, or a pong if the queue is empty.

    Used as the side_effect for mock_client.wait_for_message.

    Args:
      *args: Positional arguments to pass to the mock.
      **kwargs: Keyword arguments to pass to the mock.
    """
    del args, kwargs
    try:
      return self.queued_messages.get(block=True, timeout=0.01)
    except queue.Empty:
      if self.kill_connections:
        return None
      return robotics_ui_pb2.RuiMessage(
          message_id="",
          ui_message=robotics_ui_pb2.UIMessage(pong=robotics_ui_pb2.Pong()),
      )

  def _await_messages_processed(self, timeout: float) -> None:
    """Waits for the queue to be empty, or for the timeout to elapse."""
    while not self.queued_messages.empty() and timeout > 0:
      time.sleep(0.01)
      timeout -= 0.01
    self.assertTrue(
        self.queued_messages.empty(),
        "Queued messages not empty after timeout:"
        f" {self.queued_messages.qsize()} messages left",
    )

  def _disable_queue(self) -> None:
    """Disables the queue, so that the framework will not receive messages.

    Use when you replace the framework's receiver functionality with a mock,
    when you use your own wait_for_message mock, or when you explicitly shut
    down the framework during a test.
    """
    self.queue_enabled = False

  def _shutdown_framework(self, framework: client.Framework) -> None:
    """Shuts down the framework, and waits for it to finish.

    The shutdown is implemented by adding a None message to the queue, which
    will cause the framework to think the connection is dead.

    Args:
      framework: The framework to shut down.
    """
    self.kill_connections = True
    self._await_messages_processed(1.5)
    framework.stop_event.wait(timeout=1.5)
    self.queue_enabled = False

  class FakeClient(UiClientInterface):
    """A fake client for testing."""

    ui_test: UiTest
    is_connected: bool
    host: str
    port: int
    first_connect_error: bool
    always_fail_connect: bool

    def __init__(self, ui_test: UiTest):
      print("FakeClient created")
      self.ui_test = ui_test
      self.is_connected = False
      self.host = ""
      self.port = 0
      self.first_connect_error = False
      self.always_fail_connect = False

    def set_first_connect_error(self) -> None:
      self.first_connect_error = True

    def set_always_fail_connect(self) -> None:
      self.always_fail_connect = True

    def connect(self, host: str, port: int) -> None:
      print(f"Mock client connected to {host}:{port}")
      self.host = host
      self.port = port
      if self.always_fail_connect:
        raise OSError()
      if self.first_connect_error:
        self.first_connect_error = False
        raise OSError()
      self.is_connected = True

    def disconnect(self) -> None:
      self.is_connected = False

    def is_disconnected(self) -> bool:
      return not self.is_connected

    def wait_for_message(
        self,
    ) -> robotics_ui_pb2.RuiMessage | robotics_ui_pb2.RuiMessageList | None:
      return self.ui_test._respond_to_wait_for_message()

    def send_message(self, message: robotics_ui_pb2.RuiMessage) -> None:
      pass

    def report_stats(self, last_message_report_ns: int) -> None:
      pass

    def is_live(self) -> bool:
      return self.is_connected

    def get_version_report(self) -> robotics_ui_pb2.VersionReport:
      return robotics_ui_pb2.VersionReport(
          connection_ip=self.host, connection_port=self.port
      )

  def setUp(self):
    super().setUp()
    self.fake_uuid = 0
    self.fake_nsec = 0
    self.queued_messages = queue.Queue()
    self.queue_enabled = True
    self.kill_connections = False

    self.mock_start_pinger_thread_fn = self.enter_context(
        mock.patch.object(
            client.Framework,
            "_start_pinger_thread",
            autospec=True,
        )
    )
    self.mock_callbacks = mock.create_autospec(
        client.UiCallbacks, instance=True
    )

    self.enter_context(
        mock.patch.object(uuid, "uuid4", autospec=True)
    ).side_effect = self._generate_fake_uuid
    self.enter_context(
        mock.patch.object(time, "time_ns", autospec=True)
    ).return_value = FAKE_NSEC_VALUE

  def tearDown(self):
    super().tearDown()
    if self.queue_enabled:
      self.queued_messages.put(None)
      self._await_messages_processed(1.5)

  @parameterized.named_parameters(
      dict(
          testcase_name="single_host",
          additional_host_ports=[],
          expected_calls=[("host", 12345)],
      ),
      dict(
          testcase_name="additional_hosts",
          additional_host_ports=[("host2", 67890)],
          expected_calls=[("host", 12345), ("host2", 67890)],
      ),
  )
  def test_framework_starts_up(self, additional_host_ports, expected_calls):
    self._disable_queue()
    mock_start_receiver_thread_fn = self.enter_context(
        mock.patch.object(
            client.Framework, "_start_receiver_thread", autospec=True
        )
    )
    mock_clients = [
        self.FakeClient(self) for _ in range(len(additional_host_ports) + 1)
    ]
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=mock_clients
    )

    framework.connect(
        host="host", port=12345, additional_host_ports=additional_host_ports
    )

    self.assertTrue(
        framework.connected_event.wait(1),
        "connected_event was not set, but should have been",
    )
    self.assertTrue(
        framework.connections_live_event.wait(1),
        "connections_live_event was not set, but should have been",
    )

    for i, mock_client in enumerate(mock_clients):
      self.assertEqual(mock_client.host, expected_calls[i][0])
      self.assertEqual(mock_client.port, expected_calls[i][1])
    mock_start_receiver_thread_fn.assert_called_once()
    self.mock_start_pinger_thread_fn.assert_called_once()
    self.mock_callbacks.init_screen.assert_called_once()
    self.mock_callbacks.set_version_reports.assert_called_once()
    # We don't check the kwargs, just the args.
    versions = self.mock_callbacks.set_version_reports.call_args.args[0]
    got_versions = {(v.connection_ip, v.connection_port): v for v in versions}
    expected_versions = {
        (host, port): robotics_ui_pb2.VersionReport(
            connection_ip=host, connection_port=port
        )
        for host, port in expected_calls
    }
    self.assertLen(got_versions, len(expected_versions))
    for host, port in expected_versions:
      self.assertEqual(got_versions[host, port], expected_versions[host, port])

  @parameterized.named_parameters(
      dict(
          testcase_name="single_host",
          additional_host_ports=[],
      ),
      dict(
          testcase_name="additional_hosts",
          additional_host_ports=[("host", 67890)],
      ),
  )
  def test_framework_connection_died(self, additional_host_ports):
    mock_clients = [
        self.FakeClient(self) for _ in range(len(additional_host_ports) + 1)
    ]
    framework = client.Framework(
        callbacks=self.mock_callbacks,
        mock_clients=mock_clients,
    )

    framework.connect(
        "host", 12345, additional_host_ports=additional_host_ports
    )

    self._shutdown_framework(framework)

    self.assertTrue(
        framework.stop_event.wait(1),
        "stop_event was not set, but should have been",
    )
    self.assertFalse(framework.connected_event.is_set())
    self.mock_callbacks.ui_connection_died.assert_called_once()

  @parameterized.named_parameters(
      dict(
          testcase_name="single_host",
          additional_host_ports=[],
          expected_calls=[("host", 12345)],
      ),
      dict(
          testcase_name="additional_hosts",
          additional_host_ports=[("host2", 67890)],
          expected_calls=[
              ("host", 12345),
              ("host2", 67890),
          ],
      ),
  )
  def test_framework_starts_in_background(
      self, additional_host_ports, expected_calls
  ):
    self._disable_queue()
    mock_start_receiver_thread_fn = self.enter_context(
        mock.patch.object(
            client.Framework,
            "_start_receiver_thread",
            autospec=True,
        )
    )
    mock_clients = [
        self.FakeClient(self) for _ in range(len(additional_host_ports) + 1)
    ]
    for mock_client in mock_clients:
      mock_client.set_first_connect_error()
    framework = client.Framework(
        callbacks=self.mock_callbacks,
        mock_clients=mock_clients,
    )
    framework.connect(
        host="host",
        port=12345,
        additional_host_ports=additional_host_ports,
        block_until_connected=False,
        connect_retry_interval_secs=0.001,
    )
    self.assertTrue(
        framework.connected_event.wait(1),
        "connected_event was not set, but should have been",
    )
    self.assertTrue(
        framework.connections_live_event.wait(1),
        "connections_live_event was not set, but should have been",
    )
    for i, mock_client in enumerate(mock_clients):
      self.assertEqual(mock_client.host, expected_calls[i][0])
      self.assertEqual(mock_client.port, expected_calls[i][1])
    mock_start_receiver_thread_fn.assert_called_once()
    self.mock_start_pinger_thread_fn.assert_called_once()

  def test_framework_raises_if_send_message_when_not_connected(self):
    self._disable_queue()
    mock_client = self.FakeClient(self)
    mock_client.set_first_connect_error()
    framework = client.Framework(
        callbacks=self.mock_callbacks,
        mock_clients=[mock_client],
    )
    self.assertRaises(
        ValueError, framework.send_robot_state, robot_state_pb2.RobotState()
    )

  def test_framework_raises_if_send_message_when_shut_down(self):
    self._disable_queue()
    mock_client = self.FakeClient(self)
    framework = client.Framework(
        callbacks=self.mock_callbacks,
        mock_clients=[mock_client],
    )
    framework.shutdown()
    self.assertRaises(
        ValueError, framework.send_robot_state, robot_state_pb2.RobotState()
    )

  @parameterized.named_parameters(
      dict(
          testcase_name="single_host",
          additional_host_ports=[],
      ),
      dict(
          testcase_name="additional_hosts",
          additional_host_ports=[("host", 67890)],
      ),
  )
  def test_framework_stops_trying_to_connect_on_shut_down(
      self, additional_host_ports
  ):
    self._disable_queue()
    mock_clients = [
        self.FakeClient(self) for _ in range(len(additional_host_ports) + 1)
    ]
    for mock_client in mock_clients:
      mock_client.set_always_fail_connect()
    framework = client.Framework(
        callbacks=self.mock_callbacks,
        mock_clients=mock_clients,
    )
    framework.connect(
        block_until_connected=False,
        connect_retry_interval_secs=0.001,
        additional_host_ports=additional_host_ports,
    )
    framework.shutdown()
    self.assertFalse(
        framework.connected_event.wait(1),
        "connected_event was set, but should not have been",
    )
    self.assertFalse(
        framework.connections_live_event.wait(1),
        "connections_live_event was set, but should not have been",
    )

  @parameterized.named_parameters(
      dict(
          testcase_name="single_host",
          additional_host_ports=[],
          expect_ui_connection_died=True,
          shutdown_client_index=0,
          is_connected=False,
      ),
      dict(
          testcase_name="additional_hosts_main_client",
          additional_host_ports=[("host", 67890)],
          expect_ui_connection_died=False,
          shutdown_client_index=0,
          is_connected=True,
      ),
      dict(
          testcase_name="additional_hosts_additional_client",
          additional_host_ports=[("host", 67890)],
          expect_ui_connection_died=False,
          shutdown_client_index=1,
          is_connected=True,
      ),
  )
  def test_framework_on_shutdown_one_client(
      self,
      additional_host_ports,
      expect_ui_connection_died,
      shutdown_client_index,
      is_connected,
  ):
    self._disable_queue()
    mock_clients = [
        self.FakeClient(self) for _ in range(len(additional_host_ports) + 1)
    ]

    framework = client.Framework(
        callbacks=self.mock_callbacks,
        mock_clients=mock_clients,
    )
    # Note: if block_until_connected is False, then it is possible that no
    # connection is yet made when we call shutdown. And in that case the
    # connected_event may not be set.
    framework.connect(
        connect_retry_interval_secs=0.001,
        additional_host_ports=additional_host_ports,
    )

    framework.shutdown(mock_clients[shutdown_client_index])

    if expect_ui_connection_died:
      self.mock_callbacks.ui_connection_died.assert_called_once()
    else:
      self.mock_callbacks.ui_connection_died.assert_not_called()
    self.assertEqual(framework.stop_event.is_set(), not is_connected)
    self.assertEqual(framework.connected_event.is_set(), is_connected)


if __name__ == "__main__":
  absltest.main()
