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

"""Integration tests requiring a real Logitech F710.

This test needs to be run manually and locally on a machine with a Logitech F710
connected.
"""
import time

from absl import logging

from absl.testing import absltest
from safari_sdk.ui.input_devices import logitech_f710_evdev


class LogitechF710EvdevIntegrationTest(absltest.TestCase):
  """Integration tests requiring a real Logitech F710.

  The implemented tests open a real Logitech F710 device and runs tests with it.
  """

  def setUp(self):
    super().setUp()
    self.devices = logitech_f710_evdev.connected_devices()
    if not self.devices:
      self.fail("No Logitech F710 devices found.")
    logging.info("Found Logitech F710 devices: %s", self.devices)
    self.joystick_device = logitech_f710_evdev.LogitechF710Interface(
        device=self.devices[0],
        timeout_seconds=-1,
    )

  def test_state_has_correct_length(self):
    state = self.joystick_device.state()
    logging.info("State: %s", state)
    self.assertLen(state.axis_position, 6)
    self.assertLen(state.buttons, 6)

  def test_state_after_close(self):
    self.joystick_device.close()
    state = self.joystick_device.state()
    logging.info("State: %s", state)
    self.assertLen(state.axis_position, 6)
    self.assertLen(state.buttons, 6)

  def test_state_has_correct_length_after_close_and_reopen(self):
    self.joystick_device.close()
    self.joystick_device = logitech_f710_evdev.LogitechF710Interface(
        self.devices[0]
    )
    state = self.joystick_device.state()
    logging.info("State: %s", state)
    self.assertLen(state.axis_position, 6)
    self.assertLen(state.buttons, 6)

  def test_state_has_correct_length_with_no_timeout(self):
    self.joystick_device = logitech_f710_evdev.LogitechF710Interface(
        self.devices[0], timeout_seconds=-1
    )
    state = self.joystick_device.state()
    logging.info("State: %s", state)
    self.assertLen(state.axis_position, 6)
    self.assertLen(state.buttons, 6)

  def test_state_has_correct_length_with_short_timeout(self):
    self.joystick_device = logitech_f710_evdev.LogitechF710Interface(
        self.devices[0], timeout_seconds=0.05  # 50ms timeout.
    )
    state = self.joystick_device.state()
    logging.info("State: %s", state)
    self.assertLen(state.axis_position, 6)
    self.assertLen(state.buttons, 6)

  def test_print_state_values_for_debugging(self):
    start_time = time.time()
    while time.time() - start_time < 10:
      state = self.joystick_device.state()
      logging.info("State: %s", state)
      time.sleep(0.05)


if __name__ == "__main__":
  absltest.main()
