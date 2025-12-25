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

"""Unit tests for logger."""

from os import path
import sys
from unittest import mock

from absl.testing import absltest
from safari_sdk.workcell import logger


class LoggerTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    with mock.patch.object(path, "open") as mock_open:
      with mock.patch.object(sys, "stdout") as mock_stdout:
        with mock.patch.object(sys, "stderr") as mock_stderr:
          self.log_file = mock_open.return_value
          self.stdout = mock_stdout.return_value
          self.stderr = mock_stderr.return_value
          self.logger = logger.Logger(self.log_file, self.stdout, self.stderr)

  def test_write(self):
    self.logger.write("test")
    self.log_file.write.assert_called_once_with("test")
    self.stdout.write.assert_called_once_with("test")
    self.stderr.write.assert_called_once_with("test")

  def test_flush(self):
    self.logger.flush()
    self.log_file.flush.assert_called_once()
    self.stdout.flush.assert_called_once()
    self.stderr.flush.assert_called_once()


if __name__ == "__main__":
  absltest.main()
