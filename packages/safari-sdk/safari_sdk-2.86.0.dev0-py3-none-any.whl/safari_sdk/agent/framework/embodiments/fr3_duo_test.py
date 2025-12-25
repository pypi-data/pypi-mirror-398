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

"""Tests for the OmegaStar embodiment."""

import asyncio
import unittest

from absl.testing import absltest
from safari_sdk.agent.framework import config as framework_config
from safari_sdk.agent.framework.embodiments import omega_star
from safari_sdk.agent.framework.event_bus import event_bus


class OmegaStarTest(unittest.IsolatedAsyncioTestCase):

  def setUp(self):
    super().setUp()
    self.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(self.loop)

  def tearDown(self):
    self.loop.close()
    super().tearDown()

  async def test_instantiate(self):
    # TODO: Add more tests.
    config = framework_config.AgentFrameworkConfig()
    _ = omega_star.OmegaStarEmbodiment(bus=event_bus.EventBus(config=config))


if __name__ == "__main__":
  absltest.main()
