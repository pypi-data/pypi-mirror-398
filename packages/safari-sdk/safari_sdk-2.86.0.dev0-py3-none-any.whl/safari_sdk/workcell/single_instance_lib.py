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

"""A library for ensuring only one instance of a program is running."""

import fcntl
import os
import pathlib
import signal
from typing import IO


class SingleInstanceError(Exception):
  """Base class for exceptions in the SingleInstance class."""


class LockFileError(SingleInstanceError):
  """Raised when there is an issue with the lock file."""


class AnotherInstanceRunningError(SingleInstanceError):
  """Raised when another instance of the program is already running."""


class SignalReceivedError(SingleInstanceError):
  """Raised when a signal is received."""


class SingleInstance:
  """A class to ensure only one instance of a program is running."""

  def __init__(self, lockfile: pathlib.Path, enabled: bool = True):
    self._lockfile: pathlib.Path = lockfile
    self._lock_acquired: bool = False
    self._fp: IO[str] | None = None
    self._enabled: bool = enabled
    self._existing_pid: int | None = None

    if self._enabled:
      self._acquire_lock()
      signal.signal(signal.SIGHUP, self._signal_handler)
      signal.signal(signal.SIGTERM, self._signal_handler)
      signal.signal(signal.SIGINT, self._signal_handler)
      if not self._lock_acquired:
        raise AnotherInstanceRunningError(
            "Another instance of the program is already running with PID:"
            f" {self._existing_pid}"
        )
    else:
      print("Single instance lock is disabled.")

  def _acquire_lock(self) -> None:
    """Acquires the lock for single instance."""
    self._fp = None
    try:
      if os.path.exists(self._lockfile):
        self._fp = open(self._lockfile, "r+")
      else:
        self._fp = open(self._lockfile, "w+")
      fcntl.lockf(self._fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
      self._lock_acquired = True
      self._fp.write(str(os.getpid()))
      self._fp.flush()
      self._fp.seek(0)
    except BlockingIOError:
      if self._fp:
        pid_str = self._fp.readline().strip()
        if pid_str:
          self._existing_pid = int(pid_str)
        else:
          self._existing_pid = None
    except OSError as e:
      raise LockFileError(
          f"Could not open or lock file '{self._lockfile}': {e}"
      ) from e
    finally:
      if self._fp:
        if not self._lock_acquired:
          self._fp.close()
          self._fp = None

  def _release_lock(self) -> None:
    """Releases the lock for single instance."""
    if self._lock_acquired and self._fp:
      try:
        fcntl.lockf(self._fp, fcntl.LOCK_UN)
        self._fp.close()
        if os.path.exists(self._lockfile):
          os.remove(self._lockfile)
      except OSError as e:
        raise LockFileError(
            f"Could not release lock for file '{self._lockfile}': {e}"
        ) from e
      self._lock_acquired = False
      self._fp = None

  def get_pid(self) -> int | None:
    """Returns the PID of the existing instance if locked, otherwise None."""
    return self._existing_pid

  def _signal_handler(self, signum, frame=None) -> None:
    """Handles signals to release the lock and exit."""
    del frame
    self._release_lock()
    raise SignalReceivedError(
        f"Signal {signum} received. Releasing lock and exiting."
    )

  def is_enabled(self) -> bool:
    """Returns whether the single instance lock is enabled."""
    return self._enabled

  def is_lock_acquired(self) -> bool:
    """Returns whether the single instance lock is acquired."""
    return self._lock_acquired
