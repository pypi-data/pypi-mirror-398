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

"""Library for RUI Ergo interventions."""

import dataclasses
from importlib import resources
from typing import List

from safari_sdk.protos.ui import robotics_ui_pb2

ERGO_REMINDER_POPUP_ID: str = "ergo_reminder"
ERGO_BREAK_REQUIRED_MESSAGE: str = (
    "You have worked {time_worked} mins. Please take an Ergo break."
)
ERGO_REQUIREMENT_MET_COLOR = robotics_ui_pb2.Color(
    red=0.0, green=1.0, blue=0.0, alpha=1.0
)
ERGO_RECOMMENDED_COLOR = robotics_ui_pb2.Color(
    red=1.0, green=0.0, blue=0.0, alpha=1.0
)
ERGO_UPCOMING_COLOR = robotics_ui_pb2.Color(
    red=1.0, green=1.0, blue=0.0, alpha=1.0
)
ERGO_IMAGE_WINDOW_ID: str = "ergo_image_window"
ERGO_HYDRATE_WINDOW_ID: str = "ergo_hydrate_WINDOW"
ERGO_EYE_STRAIN_DIALOG_ID: str = "ergo_eye_strain_dialog"
ERGO_EYE_STRAIN_IMAGE_ID: str = "ergo_eye_strain_image"
ERGO_EYE_STRAIN_COUNTDOWN_TEXT_ID: str = "ergo_eye_strain_countdown_text"
ERGO_EYE_STRAIN_ALERT_TEXT_ID: str = "ergo_eye_strain_alert_text"


@dataclasses.dataclass
class BreakRequirement:
  """Dataclass to store a break requirement."""
  login_interval_start_minutes: float
  login_interval_end_minutes: float
  required_break_minutes: float


@dataclasses.dataclass
class ErgoParameters:
  """Dataclass to store ergo-related parameters."""

  alert_delay_seconds: float = 20 * 60.0
  upcoming_alert_delay_seconds: float = 15 * 60.0
  popup_delay_seconds: float = 10 * 60.0
  requirements_list_minutes: List[BreakRequirement] = dataclasses.field(
      default_factory=lambda: [
          BreakRequirement(
              login_interval_start_minutes=0.0,
              login_interval_end_minutes=20.0,
              required_break_minutes=0.0,
          ),
          BreakRequirement(
              login_interval_start_minutes=20.0,
              login_interval_end_minutes=40.0,
              required_break_minutes=5.0,
          ),
          BreakRequirement(
              login_interval_start_minutes=40.0,
              login_interval_end_minutes=float("inf"),
              required_break_minutes=10.0,
          ),
      ]
  )

  def __post_init__(self):
    if self.upcoming_alert_delay_seconds >= self.alert_delay_seconds:
      raise ValueError(
          "upcoming_alert_delay_seconds must be less than alert_delay_seconds."
      )

  def get_required_break_minutes(self, current_time_minutes: float) -> float:
    """Returns the required break minutes for the given current time.

    Args:
        current_time_minutes: The current time in minutes.

    Returns:
        The required break minutes.
    Raises:
        ValueError: If no matching break requirement is found.
    """
    for requirement in self.requirements_list_minutes:
      if (
          requirement.login_interval_start_minutes
          <= current_time_minutes
          < requirement.login_interval_end_minutes
      ):
        return requirement.required_break_minutes
    raise ValueError(
        "No matching break requirement found for"
        f" {current_time_minutes} minutes."
    )


default_ergo_parameters = ErgoParameters()

test_ergo_parameters = ErgoParameters(
    alert_delay_seconds=60.0,
    upcoming_alert_delay_seconds=30.0,
    popup_delay_seconds=90.0,
    requirements_list_minutes=[
        BreakRequirement(
            login_interval_start_minutes=0.0,
            login_interval_end_minutes=1.0,
            required_break_minutes=0.0,
        ),
        BreakRequirement(
            login_interval_start_minutes=1.0,
            login_interval_end_minutes=2.0,
            required_break_minutes=1.0,
        ),
        BreakRequirement(
            login_interval_start_minutes=2.0,
            login_interval_end_minutes=float("inf"),
            required_break_minutes=2.0,
        ),
    ],
)

ergo_disabled_parameters = ErgoParameters(
    alert_delay_seconds=float("inf"),
    popup_delay_seconds=float("inf"),
    requirements_list_minutes=[
        BreakRequirement(
            login_interval_start_minutes=0.0,
            login_interval_end_minutes=float("inf"),
            required_break_minutes=0.0,
        ),
    ],
)

ergo_enabled_parameters = ErgoParameters(
    alert_delay_seconds=30.0 * 60.0,
    upcoming_alert_delay_seconds=25.0 * 60.0,
    popup_delay_seconds=30.0 * 60.0,
    requirements_list_minutes=[
        BreakRequirement(
            login_interval_start_minutes=0.0,
            login_interval_end_minutes=30.0,
            required_break_minutes=0.0,
        ),
        BreakRequirement(
            login_interval_start_minutes=30.0,
            login_interval_end_minutes=60.0,
            required_break_minutes=2.0,
        ),
        BreakRequirement(
            login_interval_start_minutes=60.0,
            login_interval_end_minutes=float("inf"),
            required_break_minutes=4.0,
        ),
    ],
)


def get_ergo_exercise_images() -> list[str]:
  """Returns a list of ergo exercise images from the ergo/exercises directory.

  Returns:
      A list of ergo exercise images.
  """
  images = []
  try:
    anchor_pkg = "google3.third_party.safari.sdk.safari.workcell"
    images_path = resources.files(anchor_pkg).joinpath("ergo", "exercises")
    for resource in images_path.iterdir():
      if resource.is_file() and resource.name.endswith(
          (".png", ".jpg", ".jpeg")
      ):
        images.append(resource.name)
    print(f"Successfully listed images: {images}")
  except (ModuleNotFoundError, FileNotFoundError, NotADirectoryError) as e:
    print(f"Error listing images: {e}")
    images = []
  return images
