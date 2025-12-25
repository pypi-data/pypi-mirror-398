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

from unittest import mock
from absl.testing import absltest
from absl.testing import parameterized
from safari_sdk.ui.input_devices import keyboard_input
from safari_sdk.ui.input_devices import keyboard_xbox_interface_emulator
from safari_sdk.ui.input_devices import xbox_evdev


class KeyboardXboxInterfaceEmulatorTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()
    self.enter_context(
        mock.patch.object(keyboard_input, 'KeyboardInput', autospec=True)
    )

  def test_single_axis(self):
    kb_device = keyboard_xbox_interface_emulator.KeyboardXboxInterfaceEmulator(
        joystick_steps=10
    )
    mock_keyboard_input = kb_device._keyboard_input
    mock_keyboard_input.is_keyboard_hit.return_value = True
    mock_keyboard_input.get_input_character.return_value = 'w'
    with self.subTest('single_axis_step'):
      self.assertAlmostEqual(0.1, kb_device.state().axis_position[1])
    with self.subTest('axis_values_accumulate'):
      self.assertAlmostEqual(0.2, kb_device.state().axis_position[1])

  def test_multi_axis(self):
    kb_device = keyboard_xbox_interface_emulator.KeyboardXboxInterfaceEmulator(
        joystick_steps=10
    )
    mock_keyboard_input = kb_device._keyboard_input
    mock_keyboard_input.is_keyboard_hit.return_value = True
    mock_keyboard_input.get_input_character.side_effect = ['w', 'a', 'q', ' ']
    for _ in range(3):
      state = kb_device.state()
    self.assertNotEqual(
        state.axis_position[
            keyboard_xbox_interface_emulator._LEFT_JOYSTICK_HORIZONTAL
        ],
        0,
    )
    self.assertNotEqual(
        state.axis_position[
            keyboard_xbox_interface_emulator._LEFT_JOYSTICK_VERTICAL
        ],
        0,
    )
    self.assertNotEqual(
        state.axis_position[
            keyboard_xbox_interface_emulator._RIGHT_JOYSTICK_HORIZONTAL
        ],
        0,
    )
    with self.subTest('space_clears_axes'):
      # Now it will receive a space
      self.assertListEqual([0] * 6, kb_device.state().axis_position)

  def test_buttons(self):
    kb_device = keyboard_xbox_interface_emulator.KeyboardXboxInterfaceEmulator(
        joystick_steps=10
    )
    mock_keyboard_input = kb_device._keyboard_input
    mock_keyboard_input.is_keyboard_hit.return_value = True
    mock_keyboard_input.get_input_character.return_value = 'j'
    self.assertEqual(1, kb_device.state().buttons[xbox_evdev.INDEX_BUTTON_LB])
    with self.subTest('button_presses_last_one_step'):
      mock_keyboard_input.is_keyboard_hit.return_value = False
      self.assertEqual(0, kb_device.state().buttons[xbox_evdev.INDEX_BUTTON_LB])


if __name__ == '__main__':
  absltest.main()
