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

"""Recovery schemes for workcell errors."""

import dataclasses
import io
from typing import Any

field = dataclasses.field


@dataclasses.dataclass
class RecoveryScheme:
  """A recovery scheme for workcell errors.

  Attributes:
    recovery_image_filename: The filename of the recovery image.
    recovery_image_path: The path to the recovery image.
    recovery_initial_message: The initial message to display to the user.
    recovery_confirmation: Whether to require user confirmation before
      proceeding with the recovery.
    recovery_follow_up_scheme: The follow-up scheme to execute after the user
      confirms the recovery.
  """
  recovery_image_filename: str
  recovery_image_path: str | None = field(init=False)
  recovery_initial_message: str
  recovery_confirmation: bool
  recovery_follow_up_scheme: Any

  def __post_init__(self):
    self.recovery_image_path = None
    if self.recovery_image_path is None:
      self.recovery_image_path = (
          "/usr/share/icons/Adwaita/16x16/emblems/emblem-unreadable.png"
      )

  def get_recovery_image_bytes(self) -> bytes:
    """Gets the bytes of an image resource."""
    recovery_image_path = self.recovery_image_path
    with open(recovery_image_path, "rb") as image:
      f = image.read()
      image_bytes = bytearray(f)
      image_buffer = io.BytesIO(image_bytes)
      byte_array = image_buffer.getvalue()
      return byte_array


test_recovery_scheme = RecoveryScheme(
    recovery_image_filename="support_img_base.png",
    recovery_initial_message="Testing.",
    recovery_confirmation=False,
    recovery_follow_up_scheme=None,
)
