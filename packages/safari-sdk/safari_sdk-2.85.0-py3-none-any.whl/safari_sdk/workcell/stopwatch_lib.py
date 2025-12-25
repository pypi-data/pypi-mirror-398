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

"""Stopwatch class for tracking elapsed time.

Importing library/binary can create Stopwatch objects which are set with alarm
interval and callback. The callback is triggered when the alarm time is
exceeded.

Post every alarm, the Stopwatch is set back by the alarm interval.

Importing code can also pause and resume the stopwatch.
"""

import threading
import time
from typing import Callable


class Stopwatch:
  """Stopwatch class for tracking elapsed time."""

  def __init__(
      self,
      alarm_time_minutes: float = 30.0,
      timer_interval_seconds: float = 1.0,
      alarm_callback: Callable[..., None] | None = None,
      interval_callback: Callable[..., None] | None = None,
      name: str | None = None,
  ):
    self._start_time: float | None = None
    self._elapsed_time: float = 0.0
    self._is_running = False
    self._pause_time: float | None = None
    self._accumulated_pause_time: float = 0.0
    self._timestepping_thread: threading.Thread | None = None
    self._stop_event = threading.Event()
    self._alarm_time_seconds: float = alarm_time_minutes * 60
    self._timer_interval_seconds: float = timer_interval_seconds
    self._alarm_triggered = False
    self._alarm_callback = alarm_callback
    self._interval_callback = interval_callback
    self._name = f"Stopwatch({name})" if name else "Stopwatch"

  def start(self):
    """Starts the stopwatch."""
    if self._timestepping_thread is None:
      self._start_time = time.time()
      self._elapsed_time = 0.0
      self._accumulated_pause_time = 0.0
      self._pause_time = None
      self._is_running = True
      self._alarm_triggered = False
      self._stop_event.clear()
      self._timestepping_thread = threading.Thread(target=self._timer_loop)
      self._timestepping_thread.start()
      print(f"{self._name} started.")
    else:
      print(f"{self._name} is already running or not properly stopped.")

  def _timer_loop(self):
    """Main loop for updating elapsed time and checking alarm."""
    while not self._stop_event.is_set():
      if self._is_running:
        now = time.time()
        self._elapsed_time = (
            now - self._start_time - self._accumulated_pause_time
        )
        if self._alarm_time_seconds > 0 and not self._alarm_triggered:
          self._check_alarm()
        if self._interval_callback:
          self._interval_callback()
      # Wait for the timer interval or until the stop event is set
      self._stop_event.wait(self._timer_interval_seconds)

  def reset(self):
    """Resets the stopwatch. Does not stop or start the timer thread."""
    self._start_time = time.time()
    self._elapsed_time = 0
    self._pause_time = None
    self._accumulated_pause_time = 0
    self._alarm_triggered = False
    print(f"{self._name} reset.")

  def _check_alarm(self):
    if self._elapsed_time > self._alarm_time_seconds:
      print(f"{self._name} alarm triggered: {self._elapsed_time:.2f} seconds")
      self._alarm_triggered = True
      if self._alarm_callback:
        self._alarm_callback()
      self.reset()

  def pause(self):
    """Pauses the stopwatch."""
    if self._is_running:
      self._pause_time = time.time()
      self._is_running = False
      print(f"{self._name} paused.")
    else:
      print(f"{self._name} is not running or already paused.")

  def resume(self):
    """Resumes the stopwatch."""
    if not self._is_running and self._start_time is not None:
      if self._pause_time is not None:
        self._accumulated_pause_time += time.time() - self._pause_time
        self._pause_time = None
      self._is_running = True
      print(f"{self._name} resumed.")
    elif self._is_running:
      print(f"{self._name} is already running.")
    else:
      print(f"{self._name} has not been started yet.")

  def stop(self):
    """Stops the stopwatch and terminates the timer thread."""
    self._stop_event.set()
    if self._timestepping_thread is not None:
      self._timestepping_thread.join()
      self._timestepping_thread = None
      self._is_running = False
      self._start_time = None
      print(f"{self._name} stopped.")
    else:
      print(f"{self._name} is not running.")

  def get_elapsed_time(self) -> float:
    return self._elapsed_time

  def is_running(self) -> bool:
    return self._is_running

  def is_paused(self) -> bool:
    return not self._is_running and self._start_time is not None and (
        self._pause_time is not None
    )
