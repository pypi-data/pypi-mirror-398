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

"""Operator Event class."""

import dataclasses
import enum

from safari_sdk.protos import operator_event_pb2
from safari_sdk.protos.ui import robotics_ui_pb2


ui_color = robotics_ui_pb2.Color
_UI_COLOR_WHITE = ui_color(red=1.0, green=1.0, blue=1.0, alpha=1.0)
_UI_COLOR_GREEN = ui_color(red=0.0, green=1.0, blue=0.0, alpha=1.0)
_UI_COLOR_RED = ui_color(red=1.0, green=0.0, blue=0.0, alpha=1.0)
_UI_COLOR_PURPLE = ui_color(red=0.8, green=0.0, blue=0.8, alpha=1.0)
_UI_COLOR_YELLOW = ui_color(red=1.0, green=1.0, blue=0.0, alpha=1.0)


# LINT.IfChange
class WorkcellStatus(enum.Enum):
  ERGO_BREAK = 'Ergo Break'
  IN_OPERATION = 'In Operation'
  OTHER_BREAK = 'Other Break'
  TASK_SETUP_CHANGE = 'Start & End of Shift Setup'
  BROKEN_WORKCELL = 'Broken Workcell'
  TROUBLESHOOTING_TESTING = 'Support/Troubleshooting'
  RESERVED_CELL = 'Reserved/Testing'
  EVAL_POLICY_TROUBLESHOOTING = 'Eval/Policy Troubleshooting'
  TASK_FEASIBILITY = 'Task Feasibility'
  AVAILABLE = 'Available'
  MAINTENANCE = 'Maintenance'


# Used for sending workcell state as int enum to Orca.
class RuiWorkcellState(enum.IntEnum):
  """Enum for representing Workcell states as integers for Orca."""
  UNSPECIFIED = 0
  ERGO_BREAK = 1
  IN_OPERATION = 2
  OTHER_BREAK = 3
  TASK_SETUP_CHANGE = 4
  BROKEN_WORKCELL = 5
  TROUBLESHOOTING_TESTING = 6
  RESERVED_CELL = 7
  EVAL_POLICY_TROUBLESHOOTING = 8
  TASK_FEASIBILITY = 9
  AVAILABLE = 10
  MAINTENANCE = 11

# LINT.ThenChange(
# //depot/google3/robotics/orca/backend/api/proto/orca_api.proto,
# //depot/google3/google/robotics/developer/v1/orchestrator.proto,
# //depot/google3/robotics/orca/storage/proto/orca_storage.proto)

workcell_status_to_name_map = {
    status.value: status.name for status in WorkcellStatus
}

workcell_status_list_default = [status.value for status in WorkcellStatus]

workcell_status_list_redacted = [
    WorkcellStatus.BROKEN_WORKCELL.value,
    WorkcellStatus.RESERVED_CELL.value,
]

workcell_status_list_broken = [
    WorkcellStatus.BROKEN_WORKCELL.value,
    WorkcellStatus.TROUBLESHOOTING_TESTING.value,
]

workcell_status_list_reserved = [
    WorkcellStatus.RESERVED_CELL.value,
    WorkcellStatus.EVAL_POLICY_TROUBLESHOOTING.value,
]


@dataclasses.dataclass
class RobotStageProperties:
  workcell_status_list: list[str]
  dropdown_value: str

robot_stage_properties_dict: dict[str, RobotStageProperties] = {
    'ROBOT_STAGE_UNKNOWN': RobotStageProperties(
        workcell_status_list=workcell_status_list_default,
        dropdown_value=WorkcellStatus.AVAILABLE.value,
    ),
    'ROBOT_STAGE_UNSPECIFIED': RobotStageProperties(
        workcell_status_list=workcell_status_list_broken,
        dropdown_value=WorkcellStatus.BROKEN_WORKCELL.value,
    ),
    'ROBOT_STAGE_ONLINE': RobotStageProperties(
        workcell_status_list=workcell_status_list_default,
        dropdown_value=WorkcellStatus.AVAILABLE.value,
    ),
    'ROBOT_STAGE_OFFLINE': RobotStageProperties(
        workcell_status_list=workcell_status_list_broken,
        dropdown_value=WorkcellStatus.BROKEN_WORKCELL.value,
    ),
    'ROBOT_STAGE_BROKEN': RobotStageProperties(
        workcell_status_list=workcell_status_list_broken,
        dropdown_value=WorkcellStatus.BROKEN_WORKCELL.value,
    ),
    'ROBOT_STAGE_RESERVED': RobotStageProperties(
        workcell_status_list=workcell_status_list_reserved,
        dropdown_value=WorkcellStatus.RESERVED_CELL.value,
    ),
    'ROBOT_STATUS_ARCHIVED': RobotStageProperties(
        workcell_status_list=workcell_status_list_broken,
        dropdown_value=WorkcellStatus.BROKEN_WORKCELL.value,
    ),
    'ROBOT_STAGE_BROKEN_ESCALATED_GDM': RobotStageProperties(
        workcell_status_list=workcell_status_list_broken,
        dropdown_value=WorkcellStatus.BROKEN_WORKCELL.value,
    ),
    'ROBOT_STAGE_BROKEN_ESCALATED_MANUFACTURER': RobotStageProperties(
        workcell_status_list=workcell_status_list_broken,
        dropdown_value=WorkcellStatus.BROKEN_WORKCELL.value,
    ),
    'ROBOT_STAGE_ONLINE_IMPACTED': RobotStageProperties(
        workcell_status_list=workcell_status_list_default,
        dropdown_value=WorkcellStatus.AVAILABLE.value,
    ),
}


class UIEvent(enum.Enum):
  LOGIN = 'login'
  LOGOUT = 'logout'
  OTHER_EVENT = 'other event'
  RESET_FEEDBACK = 'reset feedback'


@dataclasses.dataclass
class OperatorEventProperties:
  event_proto_enum: operator_event_pb2.OperatorEventType
  background_color: ui_color
  ui_process_list: list[str]
  logout_status: WorkcellStatus = WorkcellStatus.AVAILABLE

ergo_break = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_BREAK_ERGO,
    background_color=_UI_COLOR_WHITE,
    logout_status=WorkcellStatus.AVAILABLE,
    ui_process_list=[],
)
in_operation = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_IN_OPERATION,
    background_color=_UI_COLOR_GREEN,
    logout_status=WorkcellStatus.AVAILABLE,
    ui_process_list=['episode_timer'],
)
other_break = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_BREAK_OTHER,
    background_color=_UI_COLOR_WHITE,
    logout_status=WorkcellStatus.AVAILABLE,
    ui_process_list=[],
)
task_setup_change = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_PREPARE_SHIFT,
    background_color=_UI_COLOR_WHITE,
    logout_status=WorkcellStatus.AVAILABLE,
    ui_process_list=[],
)
broken_workcell = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_WORKCELL_BROKEN,
    background_color=_UI_COLOR_RED,
    logout_status=WorkcellStatus.BROKEN_WORKCELL,
    ui_process_list=['check_error_recovery'],
)
troubleshooting_testing = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_TROUBLESHOOTING_TESTING,
    background_color=_UI_COLOR_RED,
    logout_status=WorkcellStatus.TROUBLESHOOTING_TESTING,
    ui_process_list=[],
)
reserved_cell = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_RESERVED_CELL,
    background_color=_UI_COLOR_YELLOW,
    logout_status=WorkcellStatus.RESERVED_CELL,
    ui_process_list=[],
)
available = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_LOGOUT,
    background_color=_UI_COLOR_WHITE,
    logout_status=WorkcellStatus.AVAILABLE,
    ui_process_list=[],
)
login = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_LOGIN,
    background_color=_UI_COLOR_WHITE,
    ui_process_list=['start_login_timer'],
)
logout = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_LOGOUT,
    background_color=_UI_COLOR_WHITE,
    ui_process_list=['stop_login_timer'],
)
other_event = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_OTHER,
    background_color=_UI_COLOR_WHITE,
    ui_process_list=[],
)
reset_feedback = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_RESET_FEEDBACK,
    background_color=_UI_COLOR_WHITE,
    ui_process_list=[],
)
eval_policy_troubleshooting = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_EVAL_POLICY_TROUBLESHOOTING,
    background_color=_UI_COLOR_PURPLE,
    ui_process_list=[],
)
task_feasibility = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_TASK_FEASIBILITY,
    background_color=_UI_COLOR_GREEN,
    ui_process_list=[],
)
maintenance = OperatorEventProperties(
    event_proto_enum=operator_event_pb2.OPERATOR_EVENT_TYPE_MAINTENANCE,
    background_color=_UI_COLOR_PURPLE,
    ui_process_list=[],
)

workcell_status_event_dict: dict[str, OperatorEventProperties] = {
    WorkcellStatus.ERGO_BREAK.value: ergo_break,
    WorkcellStatus.IN_OPERATION.value: in_operation,
    WorkcellStatus.OTHER_BREAK.value: other_break,
    WorkcellStatus.TASK_SETUP_CHANGE.value: task_setup_change,
    WorkcellStatus.BROKEN_WORKCELL.value: broken_workcell,
    WorkcellStatus.TROUBLESHOOTING_TESTING.value: troubleshooting_testing,
    WorkcellStatus.RESERVED_CELL.value: reserved_cell,
    WorkcellStatus.AVAILABLE.value: available,
    WorkcellStatus.EVAL_POLICY_TROUBLESHOOTING.value: (
        eval_policy_troubleshooting
    ),
    WorkcellStatus.TASK_FEASIBILITY.value: task_feasibility,
    WorkcellStatus.MAINTENANCE.value: maintenance,
}

workcell_shortcut_dict: dict[str, str] = {
    'e': WorkcellStatus.ERGO_BREAK.value,
    'i': WorkcellStatus.IN_OPERATION.value,
    'o': WorkcellStatus.OTHER_BREAK.value,
    's': WorkcellStatus.TASK_SETUP_CHANGE.value,
    'k': WorkcellStatus.BROKEN_WORKCELL.value,
    't': WorkcellStatus.TROUBLESHOOTING_TESTING.value,
    'r': WorkcellStatus.RESERVED_CELL.value,
    'v': WorkcellStatus.AVAILABLE.value,
    'l': WorkcellStatus.EVAL_POLICY_TROUBLESHOOTING.value,
    'f': WorkcellStatus.TASK_FEASIBILITY.value,
    'm': WorkcellStatus.MAINTENANCE.value,
}

ui_event_dict: dict[str, OperatorEventProperties] = {
    UIEvent.LOGIN.value: login,
    UIEvent.LOGOUT.value: logout,
    UIEvent.OTHER_EVENT.value: other_event,
    UIEvent.RESET_FEEDBACK.value: reset_feedback,
}


class OrcaStatus(enum.Enum):
  RELEASE_VERSION_INFO = 'Release Version'
  WORKCELL_CLEANUP = 'Workcell Clean'
  OTHER = 'Other'
  RESET_FEEDBACK = 'Reset Feedback'

orca_event_dict: dict[str, operator_event_pb2.OperatorEventType] = {
    OrcaStatus.RELEASE_VERSION_INFO.value: (
        operator_event_pb2.OPERATOR_EVENT_TYPE_RELEASE_VERSION_INFO
    ),
    OrcaStatus.WORKCELL_CLEANUP.value: (
        operator_event_pb2.OPERATOR_EVENT_TYPE_WORKCELL_CLEANUP
    ),
    OrcaStatus.OTHER.value: (
        operator_event_pb2.OPERATOR_EVENT_TYPE_OTHER
    ),
    OrcaStatus.RESET_FEEDBACK.value: (
        operator_event_pb2.OPERATOR_EVENT_TYPE_RESET_FEEDBACK
    ),
}
