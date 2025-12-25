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

"""Unit tests for single_instance_lib."""

import os
import pathlib
import signal
import tempfile
from unittest import mock
from absl.testing import absltest
from safari_sdk.workcell import single_instance_lib


class SingleInstanceLibTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.tmp_dir = tempfile.TemporaryDirectory()
    self.lockfile_path = pathlib.Path(self.tmp_dir.name) / "test_lockfile.lock"

  def tearDown(self):
    super().tearDown()
    self.tmp_dir.cleanup()

  def test_acquire_lock_successfully(self):
    single_instance = single_instance_lib.SingleInstance(
        lockfile=self.lockfile_path, enabled=True
    )
    self.assertTrue(single_instance.is_lock_acquired())
    self.assertTrue(self.lockfile_path.exists())
    with open(self.lockfile_path, "r") as f:
      self.assertEqual(int(f.read()), os.getpid())

  def test_acquire_lock_with_existing_lock_file(self):
    with open(self.lockfile_path, "w") as f:
      f.write(str(os.getpid()))
    single_instance = single_instance_lib.SingleInstance(
        lockfile=self.lockfile_path, enabled=True
    )
    self.assertTrue(single_instance.is_lock_acquired())
    self.assertTrue(self.lockfile_path.exists())
    with open(self.lockfile_path, "r") as f:
      self.assertEqual(int(f.read()), os.getpid())

  def test_acquire_lock_file_error(self):
    with mock.patch.object(os.path, "exists", autospec=True) as mock_exists:
      mock_exists.side_effect = OSError("test error")
      with self.assertRaises(single_instance_lib.LockFileError):
        single_instance_lib.SingleInstance(
            lockfile=self.lockfile_path, enabled=True
        )

  def test_release_lock_successfully(self):
    single_instance = single_instance_lib.SingleInstance(
        lockfile=self.lockfile_path, enabled=True
    )
    single_instance._release_lock()
    self.assertFalse(single_instance.is_lock_acquired())
    self.assertFalse(self.lockfile_path.exists())

  def test_signal_handler(self):
    test_signals = [signal.SIGHUP, signal.SIGTERM, signal.SIGINT]
    for signal_num in test_signals:
      single_instance = single_instance_lib.SingleInstance(
          lockfile=self.lockfile_path, enabled=True
      )
      with self.assertRaises(single_instance_lib.SignalReceivedError):
        single_instance._signal_handler(signal_num)
      self.assertFalse(single_instance.is_lock_acquired())
      self.assertFalse(self.lockfile_path.exists())

if __name__ == "__main__":
  absltest.main()
