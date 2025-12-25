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

"""An interface to the Logitech F710 that uses the joystick_evdev library."""

import copy

from safari_sdk.ui.input_devices import joystick_evdev

_F710_DEVICE_NAME_FILTER = 'Logitech Gamepad F710'

# Without mapping or inversion, the axis and trigger order and values are:
# Axis 0: Left stick (moved to the left: -1.0, moved to the right: 1.0)
# Axis 1: Left stick (moved up: -1.0, moved down: 1.0)
# Axis 2: Left trigger (pressed down: 1.0)
# Axis 3: Right stick (moved to the left: -1.0, moved to the right: 1.0)
# Axis 4: Right stick (moved up: -1.0, moved down: 1.0)
# Axis 5: Right trigger (pressed down: 1.0)

# The desired order for the axis array to have is:
# Axis 0: Left stick left-right (originally axis 0)
# Axis 1: Left stick up-down (originally axis 1)
# Axis 2: Right stick left-right (originally axis 3)
# Axis 3: Right stick up-down (originally axis 4)
# Axis 4: Left trigger (originally axis 2)
# Axis 5: Right trigger (originally axis 5)

# The way to interpret the remapping is as follows:
# 0 -> 0 (no change)
# 1 -> 1 (no change)
# 2 -> 4 (map left trigger to axis 4)
# 3 -> 2 (map right stick left/right to axis 2)
# 4 -> 3 (map right stick up/down to axis 3)
# 5 -> 5 (no change)
_AXIS_REMAPPING = [0, 1, 4, 2, 3, 5]

# Moving sticks to the right and down returns positive values.
# Moving sticks to the left and up returns negative values.
# Inversion of axes applied to match the right-hand rule coordinate system.
# This means moving the sticks to the left and up returns positive values.
_AXIS_INVERT = [-1, -1, -1, -1, 1, 1]

_DEFAULT_TIMEOUT_SECONDS = 50.0 / 1000.0  # 50ms

_MAX_AXIS_VALUE = 32767.0
_MAX_TRIGGER_VALUE = 255.0

# The maximum values for the joystick axes and triggers *after* remapping.
# This is used to convert the raw values to the range [-1, 1] for the axis
# position and [0, 1] for the trigger.
_MAX_JOYSTICK_VALUES = [
    _MAX_AXIS_VALUE,
    _MAX_AXIS_VALUE,
    _MAX_AXIS_VALUE,
    _MAX_AXIS_VALUE,
    _MAX_TRIGGER_VALUE,
    _MAX_TRIGGER_VALUE,
]

_BUTTON_X = 307
_BUTTON_Y = 308
_BUTTON_B = 305
_BUTTON_A = 304
_BUTTON_LB = 310
_BUTTON_RB = 311

INDEX_BUTTON_X = 0
INDEX_BUTTON_Y = 1
INDEX_BUTTON_B = 2
INDEX_BUTTON_A = 3
INDEX_BUTTON_LB = 4
INDEX_BUTTON_RB = 5

_KEY_INDICES = {
    _BUTTON_X: INDEX_BUTTON_X,
    _BUTTON_Y: INDEX_BUTTON_Y,
    _BUTTON_B: INDEX_BUTTON_B,
    _BUTTON_A: INDEX_BUTTON_A,
    _BUTTON_RB: INDEX_BUTTON_RB,
    _BUTTON_LB: INDEX_BUTTON_LB,
}


def connected_devices() -> list[joystick_evdev.InputDevice]:
  return joystick_evdev.connected_devices(_F710_DEVICE_NAME_FILTER)


class LogitechF710State:
  """The current state of the joystick buttons and axes."""

  def __init__(self, joystick_state: joystick_evdev.JoystickState):
    self._buttons = copy.deepcopy(joystick_state.buttons)
    raw_axis_position = copy.deepcopy(joystick_state.axis_position)

    self._axis_position = [0.0] * len(_AXIS_REMAPPING)
    # Convert the axis position to the range [-1, 1].
    for index, raw_value in enumerate(raw_axis_position):
      value = raw_value / _MAX_JOYSTICK_VALUES[index]
      self._axis_position[index] = _AXIS_INVERT[index] * value

  @classmethod
  def make_zero_state(cls) -> 'LogitechF710State':
    return cls(
        joystick_evdev.JoystickState(
            [0] * len(_KEY_INDICES), [0.0] * len(_AXIS_REMAPPING)
        )
    )

  @property
  def buttons(self) -> list[int]:
    return self._buttons

  @property
  def axis_position(self) -> list[float]:
    return self._axis_position

  @axis_position.setter
  def axis_position(self, value: list[float]):
    self._axis_position = value

  def __str__(self):
    axis_str = '\n  '.join(
        [f'Axis {i}: {x}' for i, x in enumerate(self.axis_position)]
    )
    return 'pos:\n  {}\nbuttons: {}'.format(
        axis_str,
        ','.join([str(x) for x in self.buttons]),
    )


class LogitechF710Interface:
  """An interface to a Logitech F710 device."""

  def __init__(
      self,
      device: joystick_evdev.InputDevice,
      enable_double_click: bool = False,
      timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
  ):
    init_state = joystick_evdev.JoystickState(
        [0] * len(_KEY_INDICES), [0.0] * len(_AXIS_REMAPPING)
    )
    self._joystick = joystick_evdev.JoystickEvdev(
        device=device,
        button_indices=_KEY_INDICES,
        axis_remapping=_AXIS_REMAPPING,
        enable_double_click=enable_double_click,
        timeout_seconds=timeout_seconds,
        init_state=init_state,
    )

  def close(self) -> None:
    self._joystick.close()

  def state(self) -> LogitechF710State:
    return LogitechF710State(self._joystick.state())

  def is_update_thread_alive(self) -> bool:
    return self._joystick.is_update_thread_alive()

  def get_update_thread_exception(self) -> Exception | None:
    return self._joystick.get_update_thread_exception()
