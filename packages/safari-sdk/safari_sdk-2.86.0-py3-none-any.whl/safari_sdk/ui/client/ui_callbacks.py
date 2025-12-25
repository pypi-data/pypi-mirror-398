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

"""Callback class for Framework."""

import binascii
from typing import Any

from safari_sdk.protos.ui import robot_command_pb2
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui.client import types


class UiCallbacks:
  """Contains callbacks that the researcher's script can override."""

  _version_reports: list[robotics_ui_pb2.VersionReport] | None = None

  def init_screen(self, framework: Any) -> None:
    """Requests that the project set up the screen, if it needs to.

    Args:
      framework: The framework. This is typed as `Any` to prevent circular
        dependencies and to not have to create a Framework interface.

    This is always called when the connection to Robotics UI is established.
    """
    del framework  # Unused in default implementation.
    print("Init screen called.")

  def get_version_reports(self) -> list[robotics_ui_pb2.VersionReport]:
    """Returns the version reports from all clients.

    This is used to get the versions of all the client connections, so the
    client can decide whether to proceed or not. The list is guaranteed to be
    up to date before init_screen is called, if the connection supports
    version reporting, as it is the first message sent by the server.
    If the server does not support version reporting, the version report is the
    default instance, with connection_ip and connection_port set to the host and
    port that the client connected to.
    """
    return self._version_reports or []

  def set_version_reports(
      self, version_reports: list[robotics_ui_pb2.VersionReport]
  ):
    """Sets the version reports from all clients.

    Do not override; the framework itself calls this.

    Args:
      version_reports: The version reports from all clients.
    """
    self._version_reports = version_reports

  def ui_connection_died(self) -> None:
    """Called when the connection died."""
    print("Connection to RoboticsUI died.")

  def console_data_received(self, command: str) -> None:
    """Called when a command typed in the Unity console is received."""

  def teleop_received(
      self, teleop_message: robotics_ui_pb2.TeleopMessage
  ) -> None:
    """DEPRECATED. Called when a teleop message is received.

    Use teleop_received_ts instead.

    Args:
      teleop_message: The teleop message.
    """

  def teleop_received_ts(
      self,
      teleop_message: robotics_ui_pb2.TeleopMessage,
      origin_timestamp_nsec: int,
      local_timestamp_nsec: int,
  ) -> None:
    """Called when a teleop message is received.

    Args:
      teleop_message: The teleop message.
      origin_timestamp_nsec: The timestamp of the message as sent by the server.
      local_timestamp_nsec: The timestamp of the message as received by the
        client.
    """

  def button_pressed(self, button_id: str) -> None:
    """Called when a button is pressed."""

  def button_released(self, button_id: str) -> None:
    """Called when a button is released."""

  def dialog_pressed(self, dialog_id: str, choice: str) -> None:
    """Called when a dialog is submitted."""

  def prompt_pressed(self, prompt_id: str, data: str) -> None:
    """Called when a prompt is submitted."""

  def dropdown_pressed(self, dropdown_id: str, choice: str | list[str]) -> None:
    """Called when a dropdown is submitted.

    Args:
      dropdown_id: The ID of the dropdown that was submitted.
      choice: The choice(s) that were selected. If multi-select, this will be a
        list of choices. Otherwise, it will be a single choice.
    """

  def command_received(self, command: robot_command_pb2.RobotCommand) -> None:
    """Called when a command is received from the Robotics UI."""

  def embody_response(self, response: robotics_ui_pb2.EmbodyResponse) -> None:
    """Called when an embody response is received from the Robotics UI."""

  def resource_uploaded(
      self, locator: types.ResourceLocator, hash_: bytes
  ) -> None:
    """Called when a resource with the given hash has been uploaded.

    The hash is an opaque identifier that can be used to refer to the resource
    later.

    Args:
      locator: The locator of the resource that was uploaded.
      hash_: The hash (opaque identifier) of the resource that was uploaded.
    """
    print(
        f"Uploaded resource confirmation for {locator.scheme}:{locator.path}"
        f"  received:{binascii.hexlify(hash_).decode('ascii').upper()}"
    )

  def form_pressed(self, form_id: str, results: str) -> None:
    """Called when the submit button of a form is pressed."""

  def kinematic_tree_robot_uploaded(
      self,
      kinematic_tree_robot_id: str,
      success: bool,
      error_message: str | None = None,
  ) -> None:
    """Called when a kinematic tree robot has been uploaded."""
    if success:
      print(f"Kinematic tree robot {kinematic_tree_robot_id} uploaded")
      return
    print(
        f"Kinematic tree robot {kinematic_tree_robot_id} upload failed:"
        f" {error_message}"
    )

  def gui_element_value_response(
      self, response: robotics_ui_pb2.GuiElementValueResponse
  ) -> None:
    """Called when a gui element value response is received from the Robotics UI."""

  def hover_received(self, element_id: str, text: str) -> None:
    """Called when a hover event is received from the Robotics UI."""

  def chat_received(self, chat_id: str, text: str) -> None:
    """Called when a chat line is received from the Robotics UI."""

  def toggle_pressed(self, toggle_id: str, selected: bool) -> None:
    """Called when a toggle is pressed."""
