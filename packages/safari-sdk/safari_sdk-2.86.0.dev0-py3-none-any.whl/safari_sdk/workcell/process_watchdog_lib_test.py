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

import time
from unittest import mock

from absl.testing import absltest
from safari_sdk.workcell import process_state
from safari_sdk.workcell import process_watchdog_lib
from safari_sdk.workcell import workcell_messages_lib

ProcessState = process_state.ProcessState


class ProcessWatchdogLibTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.mock_open = self.enter_context(
        mock.patch(
            'builtins.open',
            new_callable=mock.mock_open,
            read_data='online message',
        )
    )
    self.state_conditions_list = [
        workcell_messages_lib.WorkcellMessage(
            message_identifier_regex='online message',
            process_state=ProcessState.ONLINE,
        ),
        workcell_messages_lib.WorkcellMessage(
            message_identifier_regex='Partial Online1',
            process_state=ProcessState.PARTIAL_SUCCESS,
        ),
        workcell_messages_lib.WorkcellMessage(
            message_identifier_regex='Partial Online2',
            process_state=ProcessState.PARTIAL_SUCCESS,
        ),
        workcell_messages_lib.WorkcellMessage(
            message_identifier_regex=('Partial Online1', 'Partial Online2'),
            process_state=ProcessState.ONLINE,
        ),
    ]

  def test_initial_state(self):
    watchdog = process_watchdog_lib.ProcessWatchdog()
    self.assertEqual(watchdog.get_state(), ProcessState.OFFLINE)

  def test_check_line_and_set_state(self):
    watchdog = process_watchdog_lib.ProcessWatchdog(
        state_conditions_list=self.state_conditions_list,
        process_stdout_file_path='test_file.log',
    )
    file_mock = self.mock_open()
    content = file_mock.read()
    watchdog.check_line_and_set_state(content)
    self.assertEqual(watchdog.get_state(), ProcessState.ONLINE)

    watchdog.check_line_and_set_state('[FATAL]')
    self.assertEqual(watchdog.get_state(), ProcessState.CRASHED)

  def test_string_cleaning(self):
    watchdog = process_watchdog_lib.ProcessWatchdog()
    self.assertEqual(
        watchdog._clean_string(
            '[INFO] [1748476485.592594711] [rosbag2_recorder]: Test message'
        ),
        '[INFO]  [rosbag2_recorder]: Test message',
    )
    self.assertEqual(
        watchdog._clean_string(
            'I0528 16:54:44.974653  848366 pipe_to_rosout_patched.py:50]'
            ' Created publisher to /rosout'
        ),
        'Created publisher to /rosout',
    )

  def test_handle_startup(self):
    watchdog = process_watchdog_lib.ProcessWatchdog(
        process_startup_timeout_seconds=1
    )
    self.assertEqual(watchdog.handle_startup(), ProcessState.STARTING_UP)
    time.sleep(1)
    self.assertEqual(watchdog.handle_startup(), ProcessState.CRASHED)

  # test for the threading functionality

  def test_threading_functionality(self):
    with mock.patch.object(
        process_watchdog_lib.ProcessWatchdog,
        '_read_process_stdout_and_set_state',
        autospec=True,
    ) as mock_read_process_stdout_and_set_state:
      mock_read_process_stdout_and_set_state.return_value = None
      watchdog = process_watchdog_lib.ProcessWatchdog()
      watchdog.start()
      self.assertEqual(watchdog.get_state(), ProcessState.OFFLINE)
      watchdog.set_process_running(True)
      time.sleep(0.1)
      start_time = time.time()
      while watchdog.get_state() == ProcessState.OFFLINE:
        if time.time() - start_time > 2:  # Timeout after 2 seconds
          raise TimeoutError('Timeout waiting for state to change')
        time.sleep(0.1)
      self.assertEqual(watchdog.get_state(), ProcessState.STARTING_UP)
      watchdog.stop()

  # TODO: Re-enable this test once the bug is fixed.
  # Currently failing due to mock_open failing to open the file in kokoro tests.
  # def test_threading_functionality_with_file(self):
  #   fake_log_content = 'online message'
  #   mock_file = mock.mock_open(read_data=fake_log_content)
  #   with mock.patch('builtins.open', mock_file):
  #     watchdog = process_watchdog_lib.ProcessWatchdog(
  #         process_stdout_file_path='test_threading_functionality.log',
  #         state_conditions_list=self.state_conditions_list,
  #     )
  #     self.assertEqual(watchdog.get_state(), ProcessState.OFFLINE)
  #     watchdog.set_process_running(True)
  #     watchdog.start()
  #     time.sleep(0.1)
  #     start_time = time.time()
  #     while watchdog.get_state() == ProcessState.OFFLINE:
  #       if time.time() - start_time > 2:  # Timeout after 2 seconds
  #         raise TimeoutError('Timeout waiting for state to change')
  #       time.sleep(0.1)
  #     mock_file.assert_called_with('test_threading_functionality.log', 'r')
  #     self.assertEqual(watchdog.get_state(), ProcessState.ONLINE)

  def test_partial_success(self):
    watchdog = process_watchdog_lib.ProcessWatchdog(
        state_conditions_list=self.state_conditions_list,
        process_stdout_file_path='test_partial_success.log',
    )
    self.assertEqual(watchdog.get_state(), ProcessState.OFFLINE)
    watchdog.check_line_and_set_state('Partial Online1')
    watchdog.check_line_and_set_state('Partial Online2')
    self.assertEqual(watchdog.get_state(), ProcessState.ONLINE)

  def test_set_state_offline(self):
    watchdog = process_watchdog_lib.ProcessWatchdog(
        state_conditions_list=self.state_conditions_list,
        process_stdout_file_path='test_set_state_offline.log',
    )
    self.assertEqual(watchdog.get_state(), ProcessState.OFFLINE)
    watchdog.check_line_and_set_state('online message')
    self.assertEqual(watchdog.get_state(), ProcessState.ONLINE)
    watchdog.set_state_offline()
    self.assertEqual(watchdog.get_state(), ProcessState.OFFLINE)

  @mock.patch('os.makedirs')
  @mock.patch('builtins.open', new_callable=mock.mock_open)
  def test_dump_messages(self, mock_open, mock_makedirs):
    watchdog = process_watchdog_lib.ProcessWatchdog(
        state_conditions_list=self.state_conditions_list,
        process_stdout_file_path='test_dump_messages.log',
        dir_to_dump_messages_in='test_dir',
        process_name='test_process',
    )
    watchdog.check_line_and_set_state('[ERROR] message to be dumped')
    watchdog.check_line_and_set_state('[FATAL] message to be dumped')
    mock_makedirs.assert_called_once_with('test_dir', exist_ok=True)
    mock_open.assert_called()
    self.assertEqual(watchdog.get_state(), ProcessState.CRASHED)
    mock_open().writelines.assert_has_calls([
        mock.call(
            ['[ERROR] message to be dumped\n', '[FATAL] message to be dumped\n']
        )
    ])


if __name__ == '__main__':
  absltest.main()
