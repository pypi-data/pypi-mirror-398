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

"""Tests for the event bus."""

import asyncio
import time
from typing import Any
import unittest

from absl.testing import absltest
from safari_sdk.agent.framework import config as framework_config
from safari_sdk.agent.framework import types
from safari_sdk.agent.framework.event_bus import event_bus


class FakeHandler:  # Implements types.EventBusHandlerSignature

  def __init__(self):
    self.events = []

  def __call__(self, event: types.Event, *args, **kwargs) -> Any:
    self.events.append(event.data)


class EventBusTest(unittest.IsolatedAsyncioTestCase):

  def setUp(self):
    super().setUp()
    self.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(self.loop)

  def tearDown(self):
    self.loop.close()
    super().tearDown()

  async def test_forward_handled_event(self):
    config = framework_config.AgentFrameworkConfig()
    bus = event_bus.EventBus(config=config)
    text_handler = FakeHandler()
    audio_handler = FakeHandler()
    bus.subscribe(
        event_types=[types.EventType.MODEL_TEXT_INPUT],
        handler=text_handler,
    )
    bus.subscribe(
        event_types=[types.EventType.MODEL_AUDIO_INPUT],
        handler=audio_handler,
    )

    bus.start()
    await bus.publish(
        types.Event(
            type=types.EventType.MODEL_TEXT_INPUT,
            source=types.EventSource.USER,
            data="hello",
        )
    )
    # NOTE: We can't guarantee that this terminates but hopefully 10 seconds is
    # enough.to not get flaky on TAP.
    timeout = time.time() + 10.0
    while not text_handler.events and time.time() < timeout:
      await asyncio.sleep(0.1)
    await asyncio.sleep(1.0)  # A little extra so handler 2 would have run too.
    bus.shutdown()

    with self.subTest("desired_event_received"):
      self.assertEqual(text_handler.events, ["hello"])
    with self.subTest("undesired_event_not_received"):
      self.assertEqual(audio_handler.events, [])  # No `assertEmpty` for async!


if __name__ == "__main__":
  absltest.main()
