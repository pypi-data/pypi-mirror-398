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

"""Utilities for resources."""

import contextlib
from typing import IO, Iterator
import zipfile

from safari_sdk.protos.ui import robotics_ui_pb2


@contextlib.contextmanager
def open_resource(
    locator: robotics_ui_pb2.ResourceLocator,
) -> Iterator[IO[bytes]]:
  """Opens a binary resource from a locator.

  This is a context manager, so it can be used in a "with" statement.

  We only support these URI schemes:
  * "file:<path>"
  * "jar:file:<zip-path>!/<path-inside-zip>"

  Args:
    locator: The locator of the resource to open.

  Yields:
    A file-like object for the resource.
  """
  if locator.uri.startswith("file:"):
    try:
      with open(locator.uri[5:], "rb") as f:
        yield f
    finally:
      pass

  elif locator.uri.startswith("jar:file:"):
    paths = locator.uri[10:].split("!")
    zip_path = paths[0]
    path = paths[1]
    try:
      with zipfile.ZipFile(file=zip_path, mode="r") as z:
        with z.open(name=path) as f:
          yield f
    finally:
      pass

  else:
    raise ValueError(f"Unsupported URI scheme: {locator.uri}")
