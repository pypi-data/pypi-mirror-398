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

"""Operator Event API for interacting with the spanner database via the orchestrator server."""

import json
import time

from googleapiclient import discovery
from googleapiclient import errors

from safari_sdk.orchestrator.client.dataclass import api_response
from safari_sdk.orchestrator.client.dataclass import operator_event
from safari_sdk.workcell import operator_event_lib

_RESPONSE = api_response.OrchestratorAPIResponse

_ERROR_NO_ORCHESTRATOR_CONNECTION = (
    "OrchestratorCurrentRobotInfo: Orchestrator connection is invalid."
)

_ERROR_RECORD_OPERATOR_EVENT = (
    "OrchestratorOperatorEvent: Error in recording operator event.\n"
)

orca_supported_operator_event_str_list = [
    operator_event_lib.WorkcellStatus.ERGO_BREAK.value,
    operator_event_lib.WorkcellStatus.OTHER_BREAK.value,
    operator_event_lib.WorkcellStatus.TROUBLESHOOTING_TESTING.value,
    operator_event_lib.WorkcellStatus.EVAL_POLICY_TROUBLESHOOTING.value,
    operator_event_lib.WorkcellStatus.TASK_FEASIBILITY.value,
    operator_event_lib.OrcaStatus.WORKCELL_CLEANUP.value,
    operator_event_lib.OrcaStatus.OTHER.value,
    operator_event_lib.OrcaStatus.RESET_FEEDBACK.value,
    operator_event_lib.OrcaStatus.RELEASE_VERSION_INFO.value,
]


class OrchestratorOperatorEvent:
  """Operator Event API client for interacting with the spanner database via the orchestrator server."""

  def __init__(
      self, *, connection: discovery.Resource, robot_id: str,
  ):
    """Initializes the robot job handler."""
    self._connection = connection
    self._robot_id = robot_id

  def disconnect(self) -> None:
    """Clears current connection to the orchestrator server."""
    self._connection = None

  def add_operator_event(
      self,
      operator_event_str: str,
      operator_id: str,
      event_timestamp: int,
      resetter_id: str,
      event_note: str,
  ) -> _RESPONSE:
    """Set the current operator ID for the robot."""

    if self._connection is None:
      return _RESPONSE(error_message=_ERROR_NO_ORCHESTRATOR_CONNECTION)

    if operator_event_str not in orca_supported_operator_event_str_list:
      return _RESPONSE(
          error_message=(
              _ERROR_RECORD_OPERATOR_EVENT
              + f"Operator event type {operator_event_str} is not supported."
          )
      )

    workcell_event = operator_event_lib.workcell_status_event_dict.get(
        operator_event_str
    )
    orca_event = operator_event_lib.orca_event_dict.get(operator_event_str)

    if workcell_event is not None:
      operator_event_type = workcell_event.event_proto_enum
    elif orca_event is not None:
      operator_event_type = orca_event
    else:
      return _RESPONSE(
          error_message=(
              _ERROR_RECORD_OPERATOR_EVENT
              + f"Operator event type {operator_event_str} is not supported."
          )
      )

    body = {
        "operator_event": {
            "robotId": self._robot_id,
            "eventType": operator_event_type,
            "eventEpochMicros": event_timestamp,
            "operatorId": operator_id,
            "resetterId": resetter_id,
            "note": event_note,
        },
        "tracer": time.time_ns(),
    }

    try:
      response = (
          self._connection.orchestrator()
          .addOperatorEvent(body=body)
          .execute()
      )
    except errors.HttpError as e:
      return _RESPONSE(
          error_message=(
              _ERROR_RECORD_OPERATOR_EVENT
              + f"Reason: {e.reason}\nDetail: {e.error_details}"
          )
      )

    as_json = json.dumps(response)
    add_operator_event_response = (
        operator_event.AddOperatorEventResponse.from_json(as_json)
    )

    if not add_operator_event_response.success:
      return _RESPONSE(
          success=False,
          error_message=(
              f"Failed to record operator event [{operator_event_type}] for"
              f" [{self._robot_id}] at [{event_timestamp}]."
          ),
      )

    return _RESPONSE(success=True)
