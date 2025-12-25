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

"""Operator Event Logger.

Fills out an Operator Event message proto and writes
to disk for upload to SSOT by robup.

Data flow: Owner of OperatorEventLogger obj (say RUI) -> OperatorEventLogger ->
Local Disk -> SSOT
"""

import abc
import platform
import time

from absl import logging
import overrides

from safari_sdk.logging.python import base_logger
from safari_sdk.protos import operator_event_pb2 as operator_event_external_pb2
from safari_sdk.workcell import operator_event_lib


_DEFAULT_LDAP = ''
_DEFAULT_REPORTING_LDAP = ''
_LOGGER_ID = 'operator_events'


class OperatorEventLogger(abc.ABC):
  """Creates and logs OperatorEvent messages."""

  ldap = _DEFAULT_LDAP
  reporting_ldap = _DEFAULT_REPORTING_LDAP

  @abc.abstractmethod
  def create_workcell_status_event(
      self, event: str, event_data: str = ''
  ) -> None:
    """Creates a Workcell Status message.

    Args:
      event: contains the choice from the dropdown menu
      event_data: string with note about event
    """

  @abc.abstractmethod
  def create_ui_event(self, event: str, event_data: str = '') -> None:
    """Creates a UI event message.

    Args:
      event: contains the choice from the dropdown menu
      event_data: string with note about event
    """

  @abc.abstractmethod
  def write_event(self) -> None:
    """Writes the OperatorEvent message to disk.

    It creates the foo.tfrecord.gz files which are consumed by robup.
    """

  @abc.abstractmethod
  def shutdown_logger(self) -> None:
    """Shuts down the logger."""

  def set_ldap(self, ldap: str) -> None:
    self.ldap = ldap

  def clear_ldap(self) -> None:
    self.ldap = _DEFAULT_LDAP

  def set_reporting_ldap(self, reporting_ldap: str) -> None:
    self.reporting_ldap = reporting_ldap

  def clear_reporting_ldap(self) -> None:
    self.reporting_ldap = _DEFAULT_REPORTING_LDAP


class OperatorEventLoggerExternal(OperatorEventLogger):
  """Creates and logs OperatorEvent messages."""

  def __init__(
      self,
      robotics_platform: str,
      output_base_dir: str,
  ):
    self.operator_event = operator_event_external_pb2.OperatorEvent()
    self.writer = base_logger.BaseLogger(
        agent_id=platform.node(),
        required_topics=['operator_events'],
        optional_topics=[],
        internal_topics=[],
        output_directory=output_base_dir,
        file_shard_size_limit_bytes=0,
    )
    self.writer.start_outside_session_logging(
        start_nsec=int(time.time_ns()), output_file_prefix='operator_events'
    )
    self._robotics_platform = robotics_platform
    logging.info('Created an Operator Event logger.')

  @overrides.override
  def create_workcell_status_event(
      self, event: str, event_data: str = ''
  ) -> None:
    """Creates a Workcell Status message.

    Args:
      event: contains the choice from the dropdown menu
      event_data: string with note about event
    """
    self.operator_event.user = self.ldap
    self.operator_event.reporting_user = self.reporting_ldap
    self.operator_event.event_type = (
        operator_event_lib.workcell_status_event_dict[event].event_proto_enum
    )
    self.operator_event.note = event_data

  @overrides.override
  def create_ui_event(self, event: str, event_data: str = '') -> None:
    """Creates a UI event message.

    Args:
      event: contains the choice from the dropdown menu
      event_data: string with note about event
    """
    self.operator_event.user = self.ldap
    self.operator_event.reporting_user = self.reporting_ldap
    self.operator_event.event_type = operator_event_lib.ui_event_dict[
        event
    ].event_proto_enum
    self.operator_event.note = event_data

  def create_software_version_event(
      self, name: str, version: str
  ) -> None:
    """Creates a Software Version message.
    """
    self.operator_event.user = self.ldap
    self.operator_event.reporting_user = self.reporting_ldap
    self.operator_event.event_type = (
        operator_event_external_pb2.OPERATOR_EVENT_TYPE_RELEASE_VERSION_INFO
    )
    sw_version = self.operator_event.software_version.add()
    sw_version.name = name
    sw_version.version_string = version
    self.operator_event.note = f'{name} version: {version}'

  @overrides.override
  def write_event(self) -> None:
    """Writes the OperatorEvent message to disk.

    It creates the foo.tfrecord.gz files which are consumed by robup.
    """
    self.writer.write_proto_message(
        topic='operator_events',
        message=self.operator_event,
        log_time_nsec=time.time_ns(),
        publish_time_nsec=time.time_ns(),
    )

  @overrides.override
  def shutdown_logger(self) -> None:
    """Shuts down the logger."""
    self.writer.stop_outside_session_logging_and_finalize_file(time.time_ns())
