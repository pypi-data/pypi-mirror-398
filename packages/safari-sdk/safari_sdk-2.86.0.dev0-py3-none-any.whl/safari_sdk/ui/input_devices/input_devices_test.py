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

from absl.testing import absltest
from absl.testing import parameterized
from safari_sdk.ui.input_devices import input_devices


class UtilsTest(parameterized.TestCase):

  @parameterized.parameters([
      dict(x=1.0, expected_x_vel=10.0),
      dict(x=-1.0, expected_x_vel=-5.0),
      dict(x=0.05, expected_x_vel=0.0),
      dict(x=-0.05, expected_x_vel=0.0),
      dict(x=42, expected_x_vel=10.0),
  ])
  def test_joystick_x(self, x, expected_x_vel):
    x_vel, _, _ = input_devices.denormalize_joystick_cmd(
        x=x, y=0, yaw=0, max_x_pos_vel=10, min_x_neg_vel=5, deadzone=0.1
    )
    self.assertAlmostEqual(x_vel, expected_x_vel, places=5)

  @parameterized.parameters([
      dict(text="xbox", expected_value=input_devices.InputMode.XBOX),
      dict(
          text="keyboard",
          expected_value=input_devices.InputMode.KEYBOARD,
      ),
  ])
  def test_input_mode_enum_from_string(self, text, expected_value):
    self.assertEqual(expected_value, input_devices.InputMode(text))


if __name__ == "__main__":
  absltest.main()
