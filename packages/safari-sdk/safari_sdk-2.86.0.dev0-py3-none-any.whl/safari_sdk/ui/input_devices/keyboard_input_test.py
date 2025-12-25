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

import atexit
import select
import sys
import termios
from unittest import mock
from absl.testing import absltest
from safari_sdk.ui.input_devices import keyboard_input

MOCK_TERMIOS_GETATTR = [0, 0, 0, 0, 0, 0, 0]
MOCK_KEYBOARD_HIT_CHAR = 'd'


class KeyboardUtilsTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.enter_context(
        mock.patch.object(
            termios,
            'tcgetattr',
            return_value=MOCK_TERMIOS_GETATTR,
            autospec=True))
    self.enter_context(mock.patch.object(termios, 'tcsetattr', autospec=True))
    self.enter_context(mock.patch.object(atexit, 'register', autospec=True))

  @mock.patch.object(sys, 'stdin')
  def test_is_keyboard_hit(self, mock_stdin):
    mock_stdin.fileno.return_value = 0
    mock_select = self.enter_context(
        mock.patch.object(select, 'select', autospec=True))
    keyboard = keyboard_input.KeyboardInput()

    mock_select.return_value = (True, None, None)
    self.assertEqual(keyboard.is_keyboard_hit(), True)
    mock_select.return_value = (False, None, None)
    self.assertEqual(keyboard.is_keyboard_hit(), False)

  @mock.patch.object(sys, 'stdin')
  def test_get_input_character(self, mock_stdin):
    mock_stdin.read.return_value = MOCK_KEYBOARD_HIT_CHAR
    mock_stdin.fileno.return_value = 0
    keyboard = keyboard_input.KeyboardInput()

    kb_input = keyboard.get_input_character()
    self.assertEqual(kb_input, MOCK_KEYBOARD_HIT_CHAR)


if __name__ == '__main__':
  absltest.main()
