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

import functools
import time
from unittest import mock

from safari_sdk.workcell import stopwatch_lib
from absl.testing import absltest


class StopwatchLibTest(absltest.TestCase):

  def test_pause_resume(self):
    """Test that pause duration is not included in elapsed_time."""
    sw = stopwatch_lib.Stopwatch(timer_interval_seconds=0.1)
    sw.start()
    elapsed_before_pause = sw.get_elapsed_time()
    sw.pause()
    time.sleep(2.0)  # Simulate pause
    sw.resume()
    elapsed_after_resume = sw.get_elapsed_time()
    sw.stop()
    self.assertAlmostEqual(
        elapsed_after_resume, elapsed_before_pause, delta=0.1
    )

  def test_alarm_callback_and_reset(self):
    """Test that alarm callback is called and reset works correctly."""
    mock_callback = mock.Mock()
    sw = stopwatch_lib.Stopwatch(
        alarm_time_minutes=0.01,
        timer_interval_seconds=0.1,
        alarm_callback=mock_callback,
    )  # 0.6 seconds
    for _ in range(3):
      mock_callback.reset_mock()
      sw.start()
      time.sleep(1.0)
      mock_callback.assert_called_once()
      sw.reset()
    sw.stop()

  def test_multiple_stopwatches_pause_interaction(self):
    """Test interaction between two stopwatches, pausing/resuming sw2 from sw1 callback."""
    def callback_sw1(other_sw: stopwatch_lib.Stopwatch):
      other_sw.pause()
      time.sleep(0.2)
      other_sw.resume()

    sw2 = stopwatch_lib.Stopwatch(timer_interval_seconds=0.01)

    sw1 = stopwatch_lib.Stopwatch(
        alarm_time_minutes=0.01,
        timer_interval_seconds=0.01,
        alarm_callback=functools.partial(callback_sw1, other_sw=sw2),
    )
    sw1.start()
    sw2.start()
    time.sleep(1.0)
    elapsed_after_resume = sw2.get_elapsed_time()
    sw1.stop()
    sw2.stop()
    self.assertAlmostEqual(elapsed_after_resume, 0.8, delta=0.1)

if __name__ == "__main__":
  absltest.main()

