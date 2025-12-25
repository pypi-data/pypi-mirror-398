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

"""Exceptions and errors for the RoboticsUI client."""


class BlockOnNotSupportedError(ValueError):
  """Raised when block on is not supported for the operation."""


class RoboticsUIConnectionError(ValueError):
  """Raised when the RoboticsUI is not connected."""


class FileUploadError(ValueError):
  """Raised when there is an error uploading a file."""


class KinematicTreeRobotUploadError(ValueError):
  """Raised when there is an error uploading a kinematic tree robot."""


class StlParseError(ValueError):
  """Raised when there is an error parsing an STL file."""

