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

"""Tests for the run task planning tool."""

import asyncio
import unittest

from absl.testing import absltest
from safari_sdk.agent.framework import config as framework_config
from safari_sdk.agent.framework.event_bus import event_bus
from safari_sdk.agent.framework.tools import task_planning


class TaskPlanningTest(unittest.IsolatedAsyncioTestCase):

  def setUp(self):
    super().setUp()
    self.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(self.loop)
    self.config = framework_config.AgentFrameworkConfig()
    self.bus = event_bus.EventBus(config=self.config)

  def tearDown(self):
    self.loop.close()
    super().tearDown()

  async def test_instantiation_test(self):
    task_planning.VisionTaskPlanningTool(
        bus=self.bus,
        camera_stream_name="test_camera_stream_name",
        camera_fps=30.0,
        api_key="test_api_key",
        num_history_frames=31,
        planning_images_fps=1.0,
        one_time_planning=False,
    )


if __name__ == "__main__":
  absltest.main()
