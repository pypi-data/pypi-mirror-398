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

"""Synchronous RoboticsUI framework."""

from safari_sdk.ui.client import _internal
from safari_sdk.ui.client import framework
from safari_sdk.ui.client import ui_callbacks

UiCallbacks = ui_callbacks.UiCallbacks


class SynchronousFramework(framework.Framework):
  """A synchronous RoboticsUI framework.

  Use this when you don't want your callbacks to happen in another thread. This
  allows you to control when you handle received messages, by calling
  process_queue(). For example, you can call process_queue() at the top of
  your step() function, as long as your step() function is called regularly.
  """

  def __init__(
      self,
      callbacks: UiCallbacks | None = None,
      mock_clients: _internal.UiClientInterface | None = None,
  ):
    super().__init__(callbacks, mock_clients)
    self.is_synchronous = True

  def process_queue(self) -> None:
    while not self.incoming_msg_queue.empty():
      self._dequeue_received_message()
