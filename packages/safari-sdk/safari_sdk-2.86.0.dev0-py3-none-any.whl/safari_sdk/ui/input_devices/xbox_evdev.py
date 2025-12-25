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

"""An interface to the xbox that uses the joystick_evdev library.

This interface supports multiple devices connected to the same machine and used
concurrently.
"""

import copy
import time

from absl import logging

from safari_sdk.ui.input_devices import joystick_evdev

_XBOX_DEVICE_NAME_FILTER = 'Xbox Wireless Controller'

# The first 2 values correspond to the left-most joystick.
# The first value is such that the right is positive and left is negative.
# The second value is such that the up is positive and down is negative.
#
# The next 2 values correspond to the right-most joystick.
# The third value is such that right is positive and left is negative.
# The fourth value is such that up is positive and down is negative.
#
# The last two values are added for compatibility with the spacenav.
_AXIS_REMAPPING = [0, 1, 2, 5, 4, 3]
_AXIS_INVERT = [1, -1, 1, -1, 1, 1]

_DEFAULT_TIMEOUT_SECONDS = 50.0 / 1000.0  # 50ms

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
  return joystick_evdev.connected_devices(_XBOX_DEVICE_NAME_FILTER)


class XboxState:
  """The current state of the joystick buttons and axes."""

  def __init__(self, joystick_state: joystick_evdev.JoystickState):
    self._buttons = copy.deepcopy(joystick_state.buttons)
    self._axis_position = copy.deepcopy(joystick_state.axis_position)

    for index, value in enumerate(self._axis_position):
      value = 2 * value / 65536 - 1
      self._axis_position[index] = _AXIS_INVERT[index] * value

  @classmethod
  def make_zero_state(cls) -> 'XboxState':
    return cls(
        joystick_evdev.JoystickState(
            [0] * len(_KEY_INDICES), [65536 / 2] * len(_AXIS_REMAPPING)
        )
    )

  @property
  def buttons(self):
    return self._buttons

  @property
  def axis_position(self) -> list[float]:
    return self._axis_position

  @axis_position.setter
  def axis_position(self, value: list[float]):
    self._axis_position = value

  def __str__(self):
    return 'pos: {}, buttons: {}'.format(
        ','.join([str(x) for x in self.axis_position]),
        ','.join([str(x) for x in self.buttons]),
    )


class XboxInterface:
  """An interface to a xbox device."""

  def __init__(
      self,
      device: joystick_evdev.InputDevice,
      enable_double_click: bool = False,
      timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
  ):
    init_state = joystick_evdev.JoystickState(
        [0] * len(_KEY_INDICES), [65536 / 2] * len(_AXIS_REMAPPING)
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

  def state(self) -> XboxState:
    return XboxState(self._joystick.state())

  def is_update_thread_alive(self) -> bool:
    return self._joystick.is_update_thread_alive()

  def get_update_thread_exception(self) -> Exception | None:
    return self._joystick.get_update_thread_exception()


class RestartingXboxDevice:
  """XBox device that re-starts when the controller disconnects."""

  def __init__(self, retry_every_n_seconds: int):
    devices = connected_devices()
    while not devices:
      logging.warning('Xbox controller is disconnected. Trying to connect!')
      devices = connected_devices()

    self._xbox_device = XboxInterface(devices[0])
    self._is_closed = False
    self._last_reconnect_call = time.time()
    self._retry_every_n_seconds = retry_every_n_seconds

  def state(self) -> XboxState:
    if self._xbox_device.is_update_thread_alive():
      return self._xbox_device.state()
    else:
      if self._reconnect():
        return self._xbox_device.state()
      else:
        return XboxState.make_zero_state()

  def close(self):
    if not self._is_closed:
      self._xbox_device.close()
      self._is_closed = True

  def _reconnect(self):
    """Attempts to re-connect the controller every `retry_every_n_seconds`."""
    if not self._is_closed:
      self._xbox_device.close()
      self._is_closed = True
      self._last_reconnect_call = time.time()

    now = time.time()
    if now - self._last_reconnect_call >= self._retry_every_n_seconds:
      logging.warning('Xbox controller is disconnected. Trying to reconnect!')
      devices = connected_devices()
      if devices:
        self._xbox_device = XboxInterface(devices[0])
        self._is_closed = False
        return True

      self._last_reconnect_call = time.time()
    return False
