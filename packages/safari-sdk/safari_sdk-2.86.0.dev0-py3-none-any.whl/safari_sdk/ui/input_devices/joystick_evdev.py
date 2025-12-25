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

"""An interface to a joystick that uses the evdev library.

This interface supports multiple devices connected to the same machine and used
concurrently.
"""

import contextlib
import copy
import grp
import re
import select
import threading
import time
from typing import Optional

from absl import logging
import evdev
import immutabledict

InputDevice = evdev.InputDevice

# Threshold under which 2 consecutive clicks will be registers as a double
# click.
_DOUBLE_CLICK_THRESHOLD_SECONDS = 250.0 / 1000.0

# Values for axis events.
_ABS_MIN_CODE = 0
_ABS_MAX_CODE = 5

# Evdev Event types
_KEY_EVENT_TYPE = 1
_AXIS_EVENT_TYPE = 2
_ABSOLUTE_EVENT_TYPE = 3


def connected_devices(name_filter: str) -> list[InputDevice]:
  """Return a list of devices sorted by their USB port labels, for consistency."""
  devices = []
  for device_path in evdev.list_devices():
    device = InputDevice(device_path)
    if re.search(name_filter, device.name) is not None:
      devices.append(device)

  if not devices:
    logging.warning('No devices found.')
    for group in grp.getgrall():
      if group.gr_name == 'input':
        break
    else:
      logging.warning(
          'You are not a member of the "input" group. Run the '
          'following to add yourself: \n'
          'sudo usermod -a -G input ${USER}\n'
          'And re-login using: \n'
          'su ${USER}'
      )

  return sorted(devices, key=lambda device: device.phys)


class JoystickState:
  """The current state of the joystick buttons and axes."""

  def __init__(self, buttons: list[int], axis_position: list[float]):
    self._buttons = buttons
    self._axis_position = axis_position

  @property
  def buttons(self) -> list[int]:
    return self._buttons

  @property
  def axis_position(self) -> list[float]:
    return self._axis_position

  def __str__(self):
    return 'pos: {}, buttons: {}'.format(
        ','.join([str(x) for x in self.axis_position]),
        ','.join([str(x) for x in self.buttons]),
    )


class JoystickEvdev:
  """An interface to a joystick device."""

  def __init__(
      self,
      device: Optional[InputDevice],
      button_indices: dict[int, int] | immutabledict.immutabledict[int, int],
      axis_remapping: list[int],
      enable_double_click: bool = False,
      timeout_seconds: float = -1,
      init_state: Optional[JoystickState] = None,
  ):
    self._device = device
    self._enable_double_click = enable_double_click
    if init_state is not None:
      self._init_state = copy.deepcopy(init_state)
    else:
      self._init_state = JoystickState(
          [0] * len(button_indices), [0.0] * len(axis_remapping)
      )
    self._cur_state = copy.deepcopy(self._init_state)
    self._timeout_seconds = timeout_seconds
    now = time.time()
    self._last_button_update_time: dict[int, float] = {
        button: now for button in button_indices
    }

    self._button_indices = button_indices
    self._axis_remapping = axis_remapping

    self._thread_exc = None
    self._should_stop = False
    if self._device is not None:
      self._last_update_time = time.time()

      self._lock = threading.Lock()
      self._thread = threading.Thread(target=self._update_loop, daemon=True)
      self._thread.start()

  def close(self) -> None:
    with self._lock:
      self._should_stop = True
    self._thread.join()

    if self._device is not None:
      self._device.close()

  def state(self) -> JoystickState:
    with self._lock:
      if self._device is None:
        return copy.deepcopy(self._cur_state)
      else:
        if self._timeout_seconds > 0:
          if time.time() - self._last_update_time > self._timeout_seconds:
            self._cur_state = self._init_state
        return copy.deepcopy(self._cur_state)

  def is_update_thread_alive(self) -> bool:
    return self._thread.is_alive()

  def get_update_thread_exception(self) -> Exception | None:
    return self._thread_exc

  def _update_loop(self):
    """Update thread loop for updating the state based on incoming events."""
    assert self._device is not None

    button_events = []
    axis_events = []

    try:
      with contextlib.closing(self._device):
        with self._device.grab_context():
          while True:
            # Read all events available.
            # pylint: disable-next=unused-variable
            r, w, x = select.select([self._device.fd], [], [])
            for event in self._device.read():
              self._update_loop_event_processor(
                  event, button_events, axis_events
              )

            # Update internal state once with all events. This prevents spurious
            # locking.
            with self._lock:
              if self._should_stop:
                break

              self._push_new_state(button_events, axis_events)
              button_events = []
              axis_events = []

    except Exception as e:  # pylint: disable=broad-exception-caught
      self._thread_exc = e

  def _update_loop_event_processor(self, event, button_events, axis_events):
    """Processes events arising in `_update_loop`."""
    if event.type == _KEY_EVENT_TYPE and event.code in self._button_indices:
      # event.value: 0 = up, 1 = down, 2 = double click if enabled
      button_events.append((
          self._button_indices[event.code],
          self._input_to_button_event(event.code, int(event.value)),
      ))
    elif event.type == _AXIS_EVENT_TYPE and (
        event.code >= 0 and event.code <= 5
    ):
      axis = event.code
      amount = float(event.value)
      axis_events.append((axis, amount))
    elif (
        event.type == _ABSOLUTE_EVENT_TYPE
        and event.code >= _ABS_MIN_CODE
        and event.code <= _ABS_MAX_CODE
    ):
      axis = event.code
      amount = float(event.value)
      axis_events.append((axis, amount))

  def _push_new_state(self, button_events, axis_events):
    """Update the current state from the given events."""
    if self._timeout_seconds >= 0:
      self._last_update_time = time.time()

    for index, value in button_events:
      self._cur_state.buttons[index] = value

    for index, value in axis_events:
      index = self._axis_remapping[index]
      self._cur_state.axis_position[index] = value

  def _input_to_button_event(self, button_code: int, pressed: int) -> int:
    """Returns state of button."""
    # Return 0 if button is not pressed.
    value = 0
    if pressed == 1:
      # Return 1 if the button is pressed.
      value = 1
      now = time.time()
      if (
          self._enable_double_click
          and now - self._last_button_update_time[button_code]
          < _DOUBLE_CLICK_THRESHOLD_SECONDS
      ):
        # Return 2 if double clicking is enabled and if the clicks are close
        # enough.
        value = 2
      self._last_button_update_time[button_code] = now
    return value
