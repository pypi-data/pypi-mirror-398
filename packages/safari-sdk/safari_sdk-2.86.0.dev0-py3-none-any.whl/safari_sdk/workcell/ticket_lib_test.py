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

import json
from unittest import mock

from absl.testing import parameterized
from googleapiclient import discovery

from absl.testing import absltest
from safari_sdk.workcell import ticket_lib


# TODO: Add integration tests for sending tickets to the Orca
# backend
class TicketLibTest(parameterized.TestCase):

  @parameterized.named_parameters(
      dict(
          testcase_name="valid",
          ticket_form=json.dumps({
              "ticket_title": "title",
              "is_broken": "No",
              "ticket_priority": "P3",
              "ticket_description": "test",
              "ticket_context": "test",
              "failure_reason": "HARDWARE",
              "robot_id": "test_robot",
              "robot_location": "MTV",
          }),
          expected=(True, ""),
      ),
      dict(
          testcase_name="valid_mark_broken",
          ticket_form=json.dumps({
              "ticket_title": "title",
              "is_broken": "True",
              "ticket_priority": "P3",
              "ticket_description": "test broken",
              "ticket_context": "test broken robot",
              "failure_reason": "HARDWARE",
              "robot_id": "test_robot",
              "robot_location": "MTV",
          }),
          expected=(True, ""),
      ),
      dict(
          testcase_name="missing_fields",
          ticket_form=json.dumps({
              "ticket_title": "",
              "is_broken": "No",
              "ticket_priority": "P3",
              "ticket_description": "test",
              "ticket_context": "test",
              "failure_reason": "HARDWARE",
              "robot_id": "test_robot",
              "robot_location": "MTV",
          }),
          expected=(
              False,
              "Ticket not submitted. Field ticket title is required.",
          ),
      ),
      dict(
          testcase_name="unspecified_failure_reason",
          ticket_form=json.dumps({
              "ticket_title": "title",
              "is_broken": "No",
              "ticket_priority": "P3",
              "ticket_description": "test",
              "ticket_context": "test",
              "failure_reason": "",
              "robot_id": "test_robot",
              "robot_location": "MTV",
          }),
          expected=(
              False,
              "Ticket not submitted. Field failure reason is required.",
          ),
      ),
  )
  def test_is_valid_ticket_form(self, ticket_form, expected):
    """Tests that the required fields are included.

    Args:
      ticket_form: A json string representing the ticket form.
      expected: A tuple of (is_valid, error_message).

    Does not check for valid values.

    """
    self.assertEqual(
        expected, ticket_lib.is_valid_ticket_form(ticket_form=ticket_form)
    )

  @mock.patch.object(ticket_lib, "OrcaTicketCli", spec=ticket_lib.OrcaTicketCli)
  def test_get_ticket_cli_orca(self, orca_ticket_cli):
    mock_service = mock.Mock(spec=discovery.Resource)
    ticket_lib.get_ticket_cli(orca_service=mock_service)
    orca_ticket_cli.assert_called_once_with(service=mock_service)


if __name__ == "__main__":
  absltest.main()
