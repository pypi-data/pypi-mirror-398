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

"""Workcell Process class."""

import dataclasses
from safari_sdk.workcell import workcell_messages_lib


@dataclasses.dataclass
class WorkcellProcess:
  process_filename: str
  process_path: str
  process_args: list[str]
  start_warning_message: str | None = None
  stop_warning_message: str | None = None
  watchdog_state_conditions: (
      list[workcell_messages_lib.WorkcellMessage] | None
  ) = None
