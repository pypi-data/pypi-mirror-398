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

"""Types used in the API."""

import dataclasses
import enum
import pathlib
import zipfile
from safari_sdk.protos.ui import robot_types_pb2

MIME_TYPE_WTF = "model/vnd.google.wtf"  # Wire Triangle Format


@enum.unique
class TransformType(enum.IntEnum):
  """The type of transform.

  Transforms are global (referenced to world zero) or local (referenced to the
  object's parent).
  """

  GLOBAL = 0
  LOCAL = 1


@dataclasses.dataclass
class BodySiteSpec:
  """Represents a site under a body in a mujoco XML file."""

  body: str  # Name of body under which the site goes.
  pos: robot_types_pb2.Position  # Position of the site relative to the body.
  rot: robot_types_pb2.Quaternion  # Rotation of the site relative to the body.


# Type alias for paths that can be opened with `open()` and read.
NonStrPathLike = pathlib.Path | zipfile.Path

# Type alias for paths that can be opened with `open()` and read. Although
# open() cannot be called on a str, str can be converted to pathlib.Path.
PathLike = str | NonStrPathLike

ResourceLocatorKey = tuple[str, PathLike]


@dataclasses.dataclass(frozen=True)
class ResourceLocator:
  """Like a URL, but with any scheme."""

  # The scheme of the upload locator. We only support "file" for now.
  scheme: str
  # The path of the resource to upload.
  path: PathLike
  # If there's in-memory data to upload, it's stored here.
  data: bytes | None = None

  def __str__(self) -> str:
    return f"{self.scheme}:{self.path}"

  def key(self) -> ResourceLocatorKey:
    """Returns a key that can be used to identify the locator."""
    return (self.scheme, self.path)
