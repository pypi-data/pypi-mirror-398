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

"""Unit tests for process_launcher_lib."""

from os import path
import signal
import subprocess
from unittest import mock

import psutil

from absl.testing import absltest
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui import client
from safari_sdk.workcell import constants
from safari_sdk.workcell import process_launcher_lib
from safari_sdk.workcell import process_watchdog_lib
from safari_sdk.workcell import workcell_errors_lib
from safari_sdk.workcell import workcell_recovery_schemes_lib


class ProcessLauncherTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    with mock.patch.object(client, 'Framework') as mock_roboticsui:
      self._mock_roboticsui = mock_roboticsui.return_value
      self._process_launcher = process_launcher_lib.ProcessLauncher(
          robotics_platform='aloha',
          ui=self._mock_roboticsui,
          workcell_errors_list=[workcell_errors_lib.test_error],
      )

  def test_start_process(self):
    with mock.patch.object(subprocess, 'Popen') as mock_popen:
      test_process = process_launcher_lib.ProcessLauncher.ProcessParams(
          name='test_process',
          path='~',
          args=['--alsologtostderr'],
          output_to_ui=True,
      )
      self._process_launcher.start_process(test_process)
      full_process_name = process_launcher_lib.get_process_name(
          'test_process', '~'
      )
      args = ['--alsologtostderr']
      bash_command = f"""
      source "{path.expanduser("~/.bashrc")}"
      {full_process_name} {" ".join(args)};
      """.strip().replace('   ', ' ')
      mock_popen.assert_called_once_with(
          [
              'bash',
              '-ic',
              bash_command,
          ],
          executable='/bin/bash',
          text=True,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE,
      )

      chat_id = f'output-{test_process.name}'
      self._mock_roboticsui.create_chat.assert_called_once_with(
          chat_id=chat_id,
          title=test_process.name,
          submit_label='Send',
          spec=robotics_ui_pb2.UISpec(width=0.5, height=0.4, x=0.5, y=0.75),
      )
      self.assertIsNotNone(test_process.stdout_thread)
      self.assertIsNotNone(test_process.stderr_thread)
      self._process_launcher.stop_output_threads(test_process)
      self.assertIsNone(test_process.stdout_thread)
      self.assertIsNone(test_process.stderr_thread)

  def test_start_process_in_terminal(self):
    with mock.patch.object(subprocess, 'Popen') as mock_popen:
      self._process_launcher.start_process(
          process_launcher_lib.ProcessLauncher.ProcessParams(
              name='test_process',
              path='~',
              args=['--alsologtostderr'],
              output_to_ui=False,
          )
      )
      command = process_launcher_lib.get_process_name('test_process', '~')
      bash_command = f"""
      source "{path.expanduser("~/.bashrc")}"
      {command} --alsologtostderr; bash;
      """.strip().replace('   ', ' ')
      mock_popen.assert_called_once_with(
          [
              'gnome-terminal',
              '--display=:0',
              '-q',
              '--',
              'bash',
              '-ic',
              bash_command,
          ],
          text=True,
      )

  def test_start_process_citc(self):
    with mock.patch.object(subprocess, 'Popen') as mock_popen:
      process_params = process_launcher_lib.ProcessLauncher.ProcessParams(
          name='test_process',
          path='~',
          args=['--alsologtostderr'],
          citc=True,
      )
      self._process_launcher.start_process(process_params)
      command = process_launcher_lib.get_process_name('test_process', '~')
      bash_command = f"""
      hgd -f {process_params.citc_client_name};
      hg sync;
      source "{path.expanduser("~/.bashrc")}"
      {command} --alsologtostderr;
      bash
      """.strip().replace('   ', ' ')
      mock_popen.assert_called_once_with(
          [
              'gnome-terminal',
              '--display=:0',
              '-q',
              '--',
              'bash',
              '-ic',
              bash_command,
          ],
          text=True,
      )

  def test_stop_process_by_pid(self):
    mock_process = mock.Mock(spec=psutil.Process)
    mock_child_process = mock.Mock(spec=psutil.Process)
    mock_process.pid = 1234
    mock_process.children.return_value = [mock_child_process]
    with mock.patch.object(psutil, 'Process') as mock_process_cls:
      mock_process_cls.return_value = mock_process
      process_launcher_lib.stop_process_by_pid(1234)
      mock_process_cls.assert_called_once_with(pid=1234)
    mock_child_process.send_signal.assert_called_once_with(signal.SIGINT)
    mock_process.send_signal.assert_called_once_with(signal.SIGINT)

  def test_stop_process_by_name(self):
    with mock.patch.object(psutil, 'process_iter') as mock_process_iter:
      test_process_0 = mock.MagicMock(spec=psutil.Process)
      test_process_1 = mock.MagicMock(spec=psutil.Process)
      test_process_0.name.return_value = 'test_process_0'
      test_process_1.name.return_value = 'test_process_1'
      mock_process_iter.return_value = [test_process_0, test_process_1]
      process_launcher_lib.stop_process('test_process')
      test_process_0.send_signal.assert_called_once_with(signal.SIGINT)

  def test_is_process_running(self):
    with mock.patch.object(psutil, 'process_iter') as mock_process_iter:
      test_process_0 = mock.MagicMock(spec=psutil.Process)
      test_process_1 = mock.MagicMock(spec=psutil.Process)
      test_process_0.name.return_value = 'test_process_0'
      test_process_1.name.return_value = 'test_process_1'
      mock_process_iter.return_value = [test_process_0, test_process_1]
      self.assertTrue(process_launcher_lib.is_process_running('test_process_0'))
      self.assertFalse(
          process_launcher_lib.is_process_running('test_process_2')
      )

  def test_start_process_launcher(self):
    self._process_launcher.start()
    self.assertIsNotNone(self._process_launcher._process_thread)
    self.assertFalse(
        self._process_launcher._process_thread_stop_event.wait(5.0),
        'Process launcher did not start.',
    )
    self._process_launcher.stop()
    self.assertTrue(
        self._process_launcher._process_thread_stop_event.wait(5.0),
        'Process launcher did not stop.',
    )
    self.assertIsNone(self._process_launcher._process_thread)

  def test_update_process_status(self):
    test_process_0 = mock.MagicMock(spec=subprocess.Popen[str])
    test_process_1 = mock.MagicMock(spec=subprocess.Popen[str])
    test_process_0.poll.return_value = None
    test_process_1.poll.return_value = 0
    process_watchdog = process_watchdog_lib.ProcessWatchdog()
    self._process_launcher.link_process_to_rui(
        process_name='test_process_0',
        process_path='~',
        process_args=['--alsologtostderr'],
    )
    self._process_launcher.link_process_to_rui(
        process_name='test_process_1',
        process_path='~',
        process_args=['--alsologtostderr'],
        process_watchdog=process_watchdog,
    )

    self._process_launcher.processes[0].popen_process = test_process_0
    self._process_launcher.processes[1].popen_process = test_process_1
    self.assertEqual(
        self._process_launcher.processes,
        [
            process_launcher_lib.ProcessLauncher.ProcessParams(
                name='test_process_0',
                path='~',
                args=['--alsologtostderr'],
                popen_process=test_process_0,
            ),
            process_launcher_lib.ProcessLauncher.ProcessParams(
                name='test_process_1',
                path='~',
                args=['--alsologtostderr'],
                popen_process=test_process_1,
                watchdog=process_watchdog,
            ),
        ],
    )
    self._process_launcher.buttons_collapsed = False
    self._process_launcher._update_process_status()

    self.assertTrue(self._process_launcher.processes[0].is_process_running())
    self.assertFalse(self._process_launcher.processes[1].is_process_running())
    self._mock_roboticsui.create_button.assert_has_calls([
        mock.call(
            'test_process_0',
            constants.PROCESS_BUTTON_START_X,
            process_launcher_lib.get_y_position(
                constants.PROCESS_BUTTON_HEIGHT, 1
            ),
            constants.PROCESS_BUTTON_WIDTH,
            constants.PROCESS_BUTTON_HEIGHT,
            'Stop test_process_0',
            disabled=False,
            background_color=constants.STANDARD_SUB_BUTTON_COLOR,
            hover_text=None,
        ),
        mock.call(
            'test_process_1',
            constants.PROCESS_BUTTON_START_X,
            process_launcher_lib.get_y_position(
                constants.PROCESS_BUTTON_HEIGHT, 2
            ),
            constants.PROCESS_BUTTON_WIDTH,
            constants.PROCESS_BUTTON_HEIGHT,
            '<b>[OFFLINE]</b> Start test_process_1',
            disabled=False,
            background_color=constants.PROCESS_STATE_TO_COLOR_MAP[
                constants.ProcessState.OFFLINE
            ],
            hover_text=None,
        ),
    ])

  def test_create_workcell_error_recovery_schema(self):
    with mock.patch.object(
        workcell_recovery_schemes_lib.RecoveryScheme,
        'get_recovery_image_bytes',
    ) as mock_get_recovery_image_bytes:
      mock_get_recovery_image_bytes.return_value = b'test_image_bytes'
      self._process_launcher.create_workcell_error_recovery_schema(
          'Testing Workcell Error Recovery'
      )
      self._mock_roboticsui.create_dialog.assert_called_once_with(
          dialog_id='fns:info',
          title='Alert',
          msg='Testing.',
          buttons=['OK'],
          spec=robotics_ui_pb2.UISpec(width=0.5, height=0.25, x=0.4, y=0.25),
      )
      self._mock_roboticsui.make_image_window.assert_called_once_with(
          image=b'test_image_bytes',
          title='Recovery Image',
          spec=robotics_ui_pb2.UISpec(width=0.25, height=0.3, x=0.8, y=0.8),
          window_id='rui:recovery_image',
      )

  def test_ui_callbacks(self):
    self._process_launcher.link_process_to_rui(
        process_name='test_process_0',
        process_path='~',
        process_args=['--alsologtostderr'],
    )
    self._process_launcher.link_process_to_rui(
        process_name='test_process_1',
        process_path='~',
        process_args=['--alsologtostderr'],
        start_warning_message='test_start_warning_message',
        stop_warning_message='test_stop_warning_message',
    )
    self._process_launcher.button_pressed(constants.PROCESS_COLLAPSE_BUTTON_ID)
    self.assertFalse(self._process_launcher.buttons_collapsed)
    with mock.patch.object(subprocess, 'Popen') as mock_popen:
      # Process 0 should start without warning.
      self._process_launcher.button_pressed('test_process_0')
      mock_popen.assert_called_once()

      # Process 0 should stop without warning.
      mock_popen.reset_mock()
      self._process_launcher.button_pressed('test_process_0')
      mock_popen.assert_called_once()

      with mock.patch.object(
          process_launcher_lib.ProcessLauncher.ProcessParams,
          'is_process_running',
      ) as mock_is_process_running:
        # Process 1 should start with warning.
        mock_is_process_running.return_value = False
        mock_popen.reset_mock()
        self._process_launcher.button_pressed('test_process_1')
        self._mock_roboticsui.create_dialog.assert_called_once_with(
            dialog_id=constants.PROCESS_WARNING_DIALOG_ID,
            title='Warning',
            msg='test_start_warning_message',
            buttons=['Yes', 'No'],
            spec=robotics_ui_pb2.UISpec(
                width=0.3,
                height=0.3,
                x=0.5,
                y=0.5,
                mode=robotics_ui_pb2.UIMode.UIMODE_MODAL,
            ),
        )
        self._process_launcher.dialog_pressed(
            constants.PROCESS_WARNING_DIALOG_ID, 'Yes'
        )
        mock_popen.assert_called_once()

        with mock.patch.object(
            process_launcher_lib.ProcessLauncher.ProcessParams, 'stop_process'
        ):
          mock_is_process_running.return_value = True
          self._mock_roboticsui.create_dialog.reset_mock()
          self._process_launcher.button_pressed('test_process_1')
          self._mock_roboticsui.create_dialog.assert_called_once_with(
              dialog_id=constants.PROCESS_WARNING_DIALOG_ID,
              title='Warning',
              msg='test_stop_warning_message',
              buttons=['Yes', 'No'],
              spec=robotics_ui_pb2.UISpec(
                  width=0.3,
                  height=0.3,
                  x=0.5,
                  y=0.5,
                  mode=robotics_ui_pb2.UIMODE_MODAL,
              ),
          )
          self._process_launcher.dialog_pressed(
              constants.PROCESS_WARNING_DIALOG_ID, 'Yes'
          )
          mock_popen.assert_called_once()


if __name__ == '__main__':
  absltest.main()
