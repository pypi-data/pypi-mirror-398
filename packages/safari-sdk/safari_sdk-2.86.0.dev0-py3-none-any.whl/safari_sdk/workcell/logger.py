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

"""Logger for logging to a file and to stdout."""

from typing import TextIO


class Logger:
  """Logs to a file and to stdout."""

  def __init__(self, *streams: TextIO):
    self.streams = streams

  def write(self, data: str) -> None:
    for stream in self.streams:
      stream.write(data)
      stream.flush()

  def flush(self) -> None:
    for stream in self.streams:
      stream.flush()
