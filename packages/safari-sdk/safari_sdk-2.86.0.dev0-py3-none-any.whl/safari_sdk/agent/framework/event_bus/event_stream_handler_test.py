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

"""Tests for event stream handler."""

import asyncio
from collections.abc import AsyncIterator
import unittest

from absl.testing import absltest
from safari_sdk.agent.framework import config as framework_config
from safari_sdk.agent.framework import constants
from safari_sdk.agent.framework import types
from safari_sdk.agent.framework.event_bus import event_bus
from safari_sdk.agent.framework.event_bus import event_stream_handler


async def test_stream() -> AsyncIterator[types.Event]:
  yield types.Event(
      type=types.EventType.GO_AWAY,
      source=types.EventSource.USER,
      metadata={"content": "foo"},
  )
  yield types.Event(
      type=types.EventType.GO_AWAY,
      source=types.EventSource.USER,
      metadata={"content": "bar"},
  )


class EventStreamHandlerTest(unittest.IsolatedAsyncioTestCase):

  def setUp(self):
    super().setUp()
    self.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(self.loop)

  def tearDown(self):
    self.loop.close()
    super().tearDown()

  def assertLen(self, container, expected_len):
    # IsolatedAsyncioTestCase has no assertLen.
    # pylint: disable=g-generic-assert
    self.assertEqual(len(container), expected_len)
    # pylint: enable=g-generic-assert

  async def test_give_me_a_name(self):
    stream_name = "stream_1"
    config = framework_config.AgentFrameworkConfig()
    bus = event_bus.EventBus(config=config)
    events = []
    bus.subscribe(
        event_types=[types.EventType.GO_AWAY],
        handler=events.append,  # Grab all events for testing.
    )

    handler = event_stream_handler.EventStreamHandler(
        bus=bus,
        streams={stream_name: test_stream()},
    )
    await handler.connect()
    bus.start()

    await asyncio.sleep(1)  # Potential flake but should be fine for two events.
    self.assertLen(events, 2)

    with self.subTest("stream_name_added_to_metadata"):
      self.assertEqual(
          events[0].metadata[constants.STREAM_NAME_METADATA_KEY], stream_name
      )
      self.assertEqual(
          events[1].metadata[constants.STREAM_NAME_METADATA_KEY], stream_name
      )

    await handler.disconnect()


if __name__ == "__main__":
  absltest.main()
