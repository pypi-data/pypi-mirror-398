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

"""Tests for Logitech F710 joystick using sample data from the real device."""

import numpy as np

from absl.testing import absltest
from absl.testing import parameterized
from safari_sdk.ui.input_devices import joystick_evdev
from safari_sdk.ui.input_devices import logitech_f710_evdev


class LogitechF710EvdevTest(parameterized.TestCase):

  @parameterized.named_parameters(
      dict(
          testcase_name="all_zero",
          axis_position=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          expected_axis_position=[0.0] * 6,
      ),
      dict(
          testcase_name="all_max",
          axis_position=[32767.0, 32767.0, 32767.0, 32767.0, 255.0, 255.0],
          expected_axis_position=[-1.0, -1.0, -1.0, -1.0, 1.0, 1.0],
      ),
      dict(
          testcase_name="all_min",
          axis_position=[
              -32767.0,
              -32767.0,
              -32767.0,
              -32767.0,
              0.0,
              0.0,
          ],
          expected_axis_position=[1.0, 1.0, 1.0, 1.0, 0.0, 0.0],
      ),
      dict(
          testcase_name="all_half",
          axis_position=[
              16383.0,
              16383.0,
              16383.0,
              16383.0,
              127.0,
              127.0,
          ],
          expected_axis_position=[-0.5, -0.5, -0.5, -0.5, 0.5, 0.5],
      ),
      dict(
          testcase_name="all_negative_half",
          axis_position=[
              -16383.0,
              -16383.0,
              -16383.0,
              -16383.0,
              0.0,
              0.0,
          ],
          expected_axis_position=[0.5, 0.5, 0.5, 0.5, 0.0, 0.0],
      ),
      dict(
          testcase_name="all_one_quarter",
          axis_position=[
              8191.0,
              8191.0,
              8191.0,
              8191.0,
              0.0,
              0.0,
          ],
          expected_axis_position=[-0.25, -0.25, -0.25, -0.25, 0.0, 0.0],
      ),
      dict(
          testcase_name="all_negative_one_quarter",
          axis_position=[
              -8191.0,
              -8191.0,
              -8191.0,
              -8191.0,
              0.0,
              0.0,
          ],
          expected_axis_position=[0.25, 0.25, 0.25, 0.25, 0.0, 0.0],
      ),
  )
  def test_state_scales_and_inverts_correctly(
      self, axis_position, expected_axis_position
  ):
    # Scaling to [-1, 1] applied to all axes.
    # Inversion of axes applied to match the right-hand rule coordinate system.
    # Moving sticks to the left and up must return positive values.
    state = logitech_f710_evdev.LogitechF710State(
        joystick_evdev.JoystickState(
            buttons=[0, 0, 0, 0, 0, 0],
            axis_position=axis_position,
        )
    )
    np.testing.assert_allclose(
        state.axis_position,
        expected_axis_position,
        rtol=5e-3,
    )

  @parameterized.named_parameters(
      dict(
          testcase_name="all_positives",
          axis_position=[32767.0, 16383.0, 8191.0, 4095.0, 255.0, 127.0],
          expected_axis_position=[-1.0, -0.5, -0.25, -0.125, 1.0, 0.5],
      ),
      dict(
          testcase_name="all_negatives",
          axis_position=[
              -32767.0,
              -16383.0,
              -8191.0,
              -4095.0,
              0.0,
              0.0,
          ],
          expected_axis_position=[1.0, 0.5, 0.25, 0.125, 0.0, 0.0],
      ),
      dict(
          testcase_name="left_hand_stick_only",
          axis_position=[32767.0, 16383.0, 0.0, 0.0, 0.0, 0.0],
          expected_axis_position=[-1.0, -0.5, 0.0, 0.0, 0.0, 0.0],
      ),
      dict(
          testcase_name="right_hand_stick_only",
          axis_position=[0.0, 0.0, 32767.0, 16383.0, 0.0, 0.0],
          expected_axis_position=[0.0, 0.0, -1.0, -0.5, 0.0, 0.0],
      ),
      dict(
          testcase_name="triggers_only_both_positives",
          axis_position=[0.0, 0.0, 0.0, 0.0, 255.0, 127.0],
          expected_axis_position=[0.0, 0.0, 0.0, 0.0, 1.0, 0.5],
      ),
      dict(
          testcase_name="triggers_only_both_zeros",
          axis_position=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
          expected_axis_position=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
      ),
  )
  def test_axis_inverts_correctly(
      self, axis_position, expected_axis_position
  ):
    # Axis order: left-hand stick (L) first, right-hand stick (R) second.
    # Raw axis order is left-right, up-down, trigger for L and R.
    # Remapping to L left-right, L up-down, R left-right, R up-down, L trigger
    # and R trigger.
    # Scaling and remapping are implicitly considered in the tests.
    state = logitech_f710_evdev.LogitechF710State(
        joystick_evdev.JoystickState(
            buttons=[0, 0, 0, 0, 0, 0],
            axis_position=axis_position,
        )
    )
    np.testing.assert_allclose(
        state.axis_position,
        expected_axis_position,
        rtol=5e-3,
    )

  def test_state_buttons_are_copied(self):
    state = logitech_f710_evdev.LogitechF710State(
        joystick_evdev.JoystickState(
            buttons=[1, 2, 3, 4, 5, 6],
            axis_position=[0.0] * 6,
        )
    )
    expected_buttons = [1, 2, 3, 4, 5, 6]
    self.assertEqual(state.buttons, expected_buttons)


if __name__ == "__main__":
  absltest.main()
