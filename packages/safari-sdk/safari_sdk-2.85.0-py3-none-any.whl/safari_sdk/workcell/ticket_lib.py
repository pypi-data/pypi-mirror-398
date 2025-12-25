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

"""Ticket client library."""

import abc
import json

from googleapiclient import discovery
from googleapiclient import errors

from safari_sdk.orchestrator.client.dataclass import ticket as orca_ticket
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui import client


HttpError = errors.HttpError
_REQUIRED_TICKET_FIELDS = [
    "ticket_title",
    "is_broken",
    "robot_id",
    "ticket_description",
    "ticket_context",
    "failure_reason",
]
_TICKET_TYPE = {
    "Robot Maintenance": (
        orca_ticket.TicketType.TICKET_TYPE_ROBOT_MAINTENANCE.value
    ),
    "Orchestrator Issue": (
        orca_ticket.TicketType.TICKET_TYPE_ORCHESTRATOR_ISSUE.value
    ),
}
_ROBOT_FAILURE_REASON = {
    "Hardware Failure": orca_ticket.RobotFailureReason.HARDWARE.value,
    "Unexpected Software Behavior": (
        orca_ticket.RobotFailureReason.SOFTWARE.value
    ),
    "ALOHA Eval Issue": orca_ticket.RobotFailureReason.SOFTWARE_EVAL.value,
    "Unexpected Robot Behavior": (
        orca_ticket.RobotFailureReason.ROBOT_BEHAVIOR.value
    ),
    "Investigation": orca_ticket.RobotFailureReason.INVESTIGATION.value,
    "Upgrade": orca_ticket.RobotFailureReason.UPGRADE.value,
}


def fill_ticket_form(
    ui: client.Framework,
    robot_id: str,
) -> None:
  """Fills a ticket form from UI input."""
  spec = robotics_ui_pb2.UISpec(
      width=500,
      height=30,
  )
  multi_line_spec = robotics_ui_pb2.UISpec(
      width=500,
      height=60,
  )
  non_interactive_spec = robotics_ui_pb2.UISpec(
      width=500,
      height=30,
      disabled=True,
  )
  ui.create_form(
      form_id="ticket_form",
      title="Create Ticket",
      submit_label="Submit Ticket",
      spec=robotics_ui_pb2.UISpec(
          mode=robotics_ui_pb2.UIMode.UIMODE_NONMODAL,
          x=0.7,
          y=0.7,
          height=0.8,
          width=0.6,
      ),
      create_requests=[
          # Dummy button to prevent the form from submitting early.
          ui.create_button_message(
              button_id="dummy_button",
              label="",
              shortcuts=None,
              spec=robotics_ui_pb2.UISpec(
                  x=0,
                  y=0,
              ),
          ),
          ui.create_prompt_message(
              prompt_id="ticket_title",
              title="Title*",
              msg="",
              submit_label="Submit Ticket",
              spec=spec,
          ),
          ui.create_dropdown_message(
              dropdown_id="is_broken",
              title="Is the robot broken ?",
              msg="",
              choices=["Yes", "No"],
              submit_label="Submit Ticket",
              initial_value="No",
              spec=spec,
          ),
          ui.create_prompt_message(
              prompt_id="robot_id",
              title="Robot ID*",
              msg="",
              submit_label="Submit Ticket",
              initial_value=robot_id,
              spec=non_interactive_spec,
          ),
          ui.create_dropdown_message(
              dropdown_id="failure_reason",
              title="Select failure reason*",
              msg="",
              choices=list(_ROBOT_FAILURE_REASON.keys()),
              submit_label="Submit Ticket",
              spec=spec,
          ),
          ui.create_prompt_message(
              prompt_id="ticket_description",
              title="What issue are you experiencing?*",
              msg="",
              submit_label="Submit Ticket",
              spec=multi_line_spec,
              multiline_input=True,
          ),
          ui.create_prompt_message(
              prompt_id="ticket_context",
              title="What was happening when the problem occurred?*",
              msg="",
              submit_label="Submit Ticket",
              spec=multi_line_spec,
              multiline_input=True,
          ),
          ui.create_prompt_message(
              prompt_id="ticket_info",
              title="Additional Info",
              msg="",
              submit_label="Submit Ticket",
              spec=multi_line_spec,
              multiline_input=True,
          ),
      ],
  )


def is_valid_ticket_form(ticket_form: str) -> tuple[bool, str]:
  """Validates a ticket form."""
  ticket = json.loads(ticket_form)
  for field in _REQUIRED_TICKET_FIELDS:
    if not ticket[field]:
      print(
          f"Ticket not submitted. Field {field.replace('_', ' ')} is required."
      )
      return (
          False,
          f"Ticket not submitted. Field {field.replace('_', ' ')} is required.",
      )
  return True, ""


def prepare_ticket_form_for_user(ticket_form: str, login_user: str) -> str:
  """Prepares ticket from raw ticket form."""
  ticket = json.loads(ticket_form)
  ticket["ticket_title"] = (
      f"{ticket['robot_id'].upper()} - {ticket['ticket_title']}"
  )
  ticket["is_broken"] = ticket["is_broken"]
  ticket["ticket_type"] = _TICKET_TYPE["Robot Maintenance"]
  ticket["failure_reason"] = ticket["failure_reason"]
  ticket["ticket_creator_email"] = f"{login_user}@google.com"
  description = (
      "## What issue are you experiencing?\n"
      f"{ticket['ticket_description']}\n\n"
      "## What was happening when the problem occurred?\n"
      f"{ticket['ticket_context']}\n\n"
      "## Additional information:\n"
      f"{ticket['ticket_info']}\n\n"
  )
  ticket["ticket_description"] = description
  return json.dumps(ticket)


def prepare_ticket_form_for_orca(ticket_form: str) -> str:
  """Cleans up ticket form."""
  ticket = json.loads(ticket_form)
  ticket["ticket_description"] = ticket["ticket_description"].replace(
      "\n", "\n\n"
  )
  ticket["ticket_description"] = ticket["ticket_description"].replace(
      "\x0b", "\n\n"
  )
  ticket["ticket_context"] = ticket["ticket_context"].replace("\n", "\n\n")
  ticket["ticket_context"] = ticket["ticket_context"].replace("\x0b", "\n\n")
  ticket["ticket_info"] = ticket["ticket_info"].replace("\n", "\n\n")
  ticket["ticket_info"] = ticket["ticket_info"].replace("\x0b", "\n\n")
  return json.dumps(ticket)


class TicketCliInterface(abc.ABC):
  """Interface for ticket client."""

  @abc.abstractmethod
  def submit_ticket(self, ticket_form: str) -> str | Exception:
    """Creates a ticket."""


class OrcaTicketCli(TicketCliInterface):
  """Ticket client to go/robotics-orca."""

  def __init__(self, service: discovery.Resource):
    self._service = service

  def submit_ticket(self, ticket_form: str) -> str:
    """Creates a ticket."""
    ticket_form = prepare_ticket_form_for_orca(ticket_form)
    ticket = json.loads(ticket_form)
    body = {"title": ticket["ticket_title"],
            "description": ticket["ticket_description"],
            "creator_email": ticket["ticket_creator_email"],
            "type": ticket["ticket_type"],
            "robot_ids": [ticket["robot_id"]],
            "failure_reason": _ROBOT_FAILURE_REASON[ticket["failure_reason"]],
            "is_broken": ticket["is_broken"] == "Yes",
            }
    print(f"Creating orca ticket: {body}")
    try:
      response = self._service.orchestrator().newTicket(body=body).execute()
      return response["ticketId"]
    except HttpError as e:
      input_provided = f"You provided: {body}"
      error_message = f"Orca service returned error: {e}"
      return input_provided + "\n" + error_message
    except KeyError as e:
      input_provided = f"You provided: {body}"
      error_message = f"Orca service response missing ticket id: {e}"
      return input_provided + "\n" + error_message


class DummyTicketCli(TicketCliInterface):
  """Dummy ticket client."""

  def submit_ticket(self, ticket_form: str) -> NotImplementedError:
    """Creates a ticket."""
    return NotImplementedError(
        "Dummy ticket client does not support ticket creation. "
        "Please check your project id and API key."
    )


def get_ticket_cli(
    orca_service: discovery.Resource,
) -> TicketCliInterface:
  """Returns a ticket client."""
  return OrcaTicketCli(
      service=orca_service,
  )
