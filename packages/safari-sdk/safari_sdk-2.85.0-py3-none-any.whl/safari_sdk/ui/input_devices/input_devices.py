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

"""Functions for providing joystick-like input to the robot."""

import enum
import numpy as np
from safari_sdk.ui.input_devices import keyboard_xbox_interface_emulator
from safari_sdk.ui.input_devices import xbox_evdev

XboxInterface = xbox_evdev.XboxInterface
XboxState = xbox_evdev.XboxState


@enum.unique
class InputMode(str, enum.Enum):
  XBOX = "xbox"
  KEYBOARD = "keyboard"


_DEADZONE = 0.05

MAX_X_POS_VEL = 1.2
MIN_X_NEG_VEL = 0.5
MAX_Y_ABS_VEL = 0.6
MAX_YAW_ABS_VEL = 1.5


def get_input_device(
    input_mode: InputMode = InputMode.XBOX,
) -> (
    keyboard_xbox_interface_emulator.KeyboardXboxInterfaceEmulator
    | xbox_evdev.RestartingXboxDevice
):
  match input_mode:
    case InputMode.XBOX:
      return xbox_evdev.RestartingXboxDevice(retry_every_n_seconds=1)
    case InputMode.KEYBOARD:
      return keyboard_xbox_interface_emulator.KeyboardXboxInterfaceEmulator()
    case _:
      raise RuntimeError("Unsupported input device type.")


def denormalize_joystick_cmd(
    x: float,
    y: float,
    yaw: float,
    max_x_pos_vel: float = MAX_X_POS_VEL,
    min_x_neg_vel: float = MIN_X_NEG_VEL,
    max_y_abs_vel: float = MAX_Y_ABS_VEL,
    max_yaw_abs_vel: float = MAX_YAW_ABS_VEL,
    deadzone: float = _DEADZONE,
) -> np.ndarray:
  r"""Converts [X, Y, YAW] values with range [-1, 1] to a joystick command.

  Plot of output x command vs input x from joystick (y and yaw are similar).
              x cmd
                ^        * max_x_pos_vel
                |       /
                |      /
  ----+---------+-----+--+--> x (joystick reading)
     -1   /     | dead   1
        /       | zone
      /         |
      * -min_x_neg_vel

  Args:
    x: Joystick position in range [-1, 1].
    y: Joystick position in range [-1, 1].
    yaw: Joystick position in range [-1, 1].
    max_x_pos_vel: Highest forward velocity command to return.
    min_x_neg_vel: Largest magnitude backward velocity command to return, >= 0.
    max_y_abs_vel: Largest magnitude sideways velocity command to return.
    max_yaw_abs_vel: Largest magnitude angular velocity command to return.
    deadzone: If abs x, y or yaw is less than this value, the corresponding
      velocity command will be 0.

  Returns:
    command: (x velocity command, y velocity command, yaw velocity command).
  """
  # Clip in case the values are outside the range.
  np_cmd = np.clip([x, y, yaw], -1.0, 1.0)

  zero_inds = np.abs(np_cmd) < deadzone

  # Scale by their max velocities.
  if np_cmd[0] >= 0.0:
    np_cmd = np.multiply(
        np_cmd - deadzone,
        (1 / (1 - deadzone))
        * np.array([max_x_pos_vel, max_y_abs_vel, max_yaw_abs_vel]),
    )
  else:
    np_cmd = np.multiply(
        np_cmd + deadzone,
        (1 / (1 - deadzone))
        * np.array([min_x_neg_vel, max_y_abs_vel, max_yaw_abs_vel]),
    )

  # Filter out the deadzone.
  np_cmd[zero_inds] = 0.0

  return np_cmd
