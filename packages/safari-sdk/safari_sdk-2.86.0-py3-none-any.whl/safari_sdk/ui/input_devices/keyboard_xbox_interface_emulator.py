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

"""Class that emulates an Xbox controller with the keyboard."""

import numpy as np
from safari_sdk.ui.input_devices import keyboard_input
from safari_sdk.ui.input_devices import xbox_evdev

_LEFT_JOYSTICK_HORIZONTAL = 0
_LEFT_JOYSTICK_VERTICAL = 1
_RIGHT_JOYSTICK_HORIZONTAL = 2
_RIGHT_JOYSTICK_VERTICAL = 3


class KeyboardXboxInterfaceEmulator(xbox_evdev.XboxInterface):
  """Emulates an Xbox controller with the keyboard.

  Left joystick is controlled by the wasd keys (w up, s down, a left, d right).
  Right joystick horizontal motion is controlled by q and e keys. Vertical is
  not implemented.
  Pressing a key multiple times is equivalent to pushing the joystick farther.
  Space resets both joysticks to zero.
  A button -> u
  B button -> i
  X button -> o
  Y button -> p
  LB button -> j
  RB button -> l (lowercase L)
  Only one button can be pressed at a time, and pressing any button resets the
  joysticks to zero.
  """

  def __init__(self, joystick_steps: int = 10):
    """Constructor.

    Args:
      joystick_steps: Number of key presses to get from joystick neutral
        position to max/min.
    """
    self._keyboard_input = keyboard_input.KeyboardInput()
    self._cur_state = xbox_evdev.XboxState.make_zero_state()
    self._step = 1 / joystick_steps

  def help_string(self) -> str:
    return self.__doc__

  def update_state(self) -> None:
    for i in range(len(self._cur_state.buttons)):
      self._cur_state.buttons[i] = 0
    if not self._keyboard_input.is_keyboard_hit():
      return
    char = self._keyboard_input.get_input_character()
    if char == 'd':
      self._cur_state.axis_position[_LEFT_JOYSTICK_HORIZONTAL] += self._step
    if char == 'a':
      self._cur_state.axis_position[_LEFT_JOYSTICK_HORIZONTAL] -= self._step
    if char == 'w':
      self._cur_state.axis_position[_LEFT_JOYSTICK_VERTICAL] += self._step
    if char == 's':
      self._cur_state.axis_position[_LEFT_JOYSTICK_VERTICAL] -= self._step
    if char == 'e':
      self._cur_state.axis_position[_RIGHT_JOYSTICK_HORIZONTAL] += self._step
    if char == 'q':
      self._cur_state.axis_position[_RIGHT_JOYSTICK_HORIZONTAL] -= self._step
    if char == 'r':
      self._cur_state.axis_position[_RIGHT_JOYSTICK_VERTICAL] += self._step
    if char == 'f':
      self._cur_state.axis_position[_RIGHT_JOYSTICK_VERTICAL] -= self._step
    if char == 'u':
      self._cur_state.buttons[xbox_evdev.INDEX_BUTTON_A] = 1
    if char == 'i':
      self._cur_state.buttons[xbox_evdev.INDEX_BUTTON_B] = 1
    if char == 'o':
      self._cur_state.buttons[xbox_evdev.INDEX_BUTTON_X] = 1
    if char == 'p':
      self._cur_state.buttons[xbox_evdev.INDEX_BUTTON_Y] = 1
    if char == 'j':
      self._cur_state.buttons[xbox_evdev.INDEX_BUTTON_LB] = 1
    if char == 'l':
      self._cur_state.buttons[xbox_evdev.INDEX_BUTTON_RB] = 1
    if char == ' ':
      self._cur_state = xbox_evdev.XboxState.make_zero_state()

    if any(self._cur_state.buttons):
      self._cur_state.axis_position = [0] * len(self._cur_state.axis_position)
      button_index = self._cur_state.buttons.index(1)
    else:
      button_index = None
    self._cur_state.axis_position = list(np.clip(
        self._cur_state.axis_position, -1.0, 1.0
    ))
    print(
        f"Detected char '{char}',",
        'Joystick states:',
        ', '.join(
            ['{0:>4.1f}'.format(x) for x in self._cur_state.axis_position[:4]]
        ),
        f'Button: {button_index}'
    )

  def close(self) -> None:
    self._keyboard_input.set_normal_term()

  def is_update_thread_alive(self) -> bool:
    return True

  def get_update_thread_exception(self) -> None:
    return None

  def state(self) -> xbox_evdev.XboxState:
    self.update_state()
    return self._cur_state
