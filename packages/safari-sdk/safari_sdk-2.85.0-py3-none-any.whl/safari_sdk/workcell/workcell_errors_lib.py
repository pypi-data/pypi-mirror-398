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

"""Workcell errors definitions."""

import dataclasses
from safari_sdk.workcell import workcell_recovery_schemes_lib


@dataclasses.dataclass
class WorkcellErrors:
  error_identifier_regex: str
  error_recovery_scheme: workcell_recovery_schemes_lib.RecoveryScheme


test_error = WorkcellErrors(
    error_identifier_regex=r"Testing Workcell Error Recovery",
    error_recovery_scheme=workcell_recovery_schemes_lib.test_recovery_scheme,
)


# Empty errors list for platforms that don't have any workcell errors.
EMPTY_ERRORS_LIST: list[WorkcellErrors] = []
