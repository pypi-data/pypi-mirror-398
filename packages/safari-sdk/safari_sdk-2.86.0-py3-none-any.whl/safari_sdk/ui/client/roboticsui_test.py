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

"""Unit tests for framework."""

import datetime
import hashlib
import pathlib
import queue
import tempfile
import threading
import time
from unittest import mock
import uuid
import zipfile


from absl.testing import absltest
from absl.testing import parameterized
from safari_sdk.protos.ui import robot_command_pb2
from safari_sdk.protos.ui import robot_state_pb2
from safari_sdk.protos.ui import robot_types_pb2
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.protos.ui import xemb_pb2
from safari_sdk.ui import client
from safari_sdk.ui.client import _internal
from safari_sdk.ui.client import upload_engine


FAKE_NSEC_VALUE = 98765
SAMPLE_PREFIX = "examples/ui"
CAT_IMAGE_PATH = SAMPLE_PREFIX + "/cat.jpg"
PIZZACAT_IMAGE_PATH = SAMPLE_PREFIX + "/pizzacat.jpg"
JPEG_PIXEL_TYPE = robot_state_pb2.CameraImage.PixelType(
    compression=robot_state_pb2.CameraImage.PixelType.JPEG
)
FAKE_CLIENT_ID = robot_types_pb2.ClientID(uuid_high=888, uuid_low=999)
UiClientInterface = _internal.UiClientInterface

TEST_FILE_DATA = b"data"
TEST_FILE_DATA_HASH = hashlib.sha256(TEST_FILE_DATA).digest()
TESTDIR = pathlib.Path(
    "safari_sdk/ui/client/testdata"
)
EXPECTED_STL_DATA = robotics_ui_pb2.WireTriangleFormat(
    vertices=[
        client.make_position(1.1, 2, 3),
        client.make_position(4, 5, 6),
        client.make_position(7, 8, -9.9e9),
        client.make_position(-1, -2, -3),
    ],
    triangles=[
        robot_types_pb2.TriangleVertexIndices(index_0=0, index_1=1, index_2=2),
        robot_types_pb2.TriangleVertexIndices(index_0=0, index_1=1, index_2=3),
    ],
)


class UiTest(parameterized.TestCase):
  fake_uuid = 0
  queued_messages: queue.Queue[robotics_ui_pb2.RuiMessage | None]
  queue_enabled: bool

  def _generate_fake_uuid(self) -> uuid.UUID:
    self.fake_uuid += 1
    return uuid.UUID(int=self.fake_uuid)

  def _respond_to_wait_for_message(
      self, *args, **kwargs
  ) -> robotics_ui_pb2.RuiMessage | None:
    """Returns a queued message, or a pong if the queue is empty.

    Used as the side_effect for mock_client.wait_for_message.

    Args:
      *args: Positional arguments to pass to the mock.
      **kwargs: Keyword arguments to pass to the mock.
    """
    del args, kwargs
    try:
      return self.queued_messages.get(block=True, timeout=0.01)
    except queue.Empty:
      return robotics_ui_pb2.RuiMessage(
          message_id="",
          ui_message=robotics_ui_pb2.UIMessage(pong=robotics_ui_pb2.Pong()),
      )

  def _queue_response(
      self, response: robotics_ui_pb2.RuiMessage | None
  ) -> None:
    """Queues a response to be returned by the mock client."""
    self.queued_messages.put(response)

  def _await_messages_processed(self, timeout: float) -> None:
    """Waits for the queue to be empty, or for the timeout to elapse."""
    while not self.queued_messages.empty() and timeout > 0:
      time.sleep(0.01)
      timeout -= 0.01
    self.assertTrue(
        self.queued_messages.empty(), "Queued messages not empty after timeout"
    )

  def setUp(self):
    super().setUp()
    self.fake_uuid = 0
    self.fake_nsec = 0
    self.queued_messages = queue.Queue()
    self.queue_enabled = True

    self.mock_start_pinger_thread_fn = self.enter_context(
        mock.patch.object(
            client.Framework,
            "_start_pinger_thread",
            autospec=True,
        )
    )
    self.mock_callbacks = mock.create_autospec(
        client.UiCallbacks, instance=True
    )
    self.mock_client = mock.create_autospec(
        _internal.UiClientInterface, instance=True
    )
    self.mock_upload_engine = mock.create_autospec(
        upload_engine.UploadEngine, instance=True
    )
    self.mock_stl_parser = mock.create_autospec(
        client.stl_parser.parse_stl, instance=True
    )
    self.mock_stl_parser.return_value = EXPECTED_STL_DATA

    self.enter_context(
        mock.patch.object(uuid, "uuid4", autospec=True)
    ).side_effect = self._generate_fake_uuid
    self.enter_context(
        mock.patch.object(time, "time_ns", autospec=True)
    ).return_value = FAKE_NSEC_VALUE
    self.mock_client.wait_for_message.side_effect = (
        self._respond_to_wait_for_message
    )

  def tearDown(self):
    super().tearDown()
    if self.queue_enabled:
      self.queued_messages.put(None)
      self._await_messages_processed(1.5)

  def test_framework_callback_console_data(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(console_data="console_data")
        )
    )
    self._await_messages_processed(1.5)

    self.mock_callbacks.console_data_received.assert_called_once_with(
        "console_data"
    )

  def test_framework_callback_command_received(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            xemb_message=xemb_pb2.XembMessage(
                robot_command=robot_command_pb2.RobotCommand(
                    command_start_time_nsec=111
                )
            )
        )
    )
    self._await_messages_processed(1.5)

    self.mock_callbacks.command_received.assert_called_once_with(
        robot_command_pb2.RobotCommand(command_start_time_nsec=111)
    )

  def test_framework_send_robot_state_with_robot_id(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.send_robot_state(
        robot_state_pb2.RobotState(
            header=robot_types_pb2.MessageHeader(client_id=FAKE_CLIENT_ID)
        ),
        robot_id="robot_id",
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            xemb_message=xemb_pb2.XembMessage(
                robot_id="robot_id",
                robot_state=robot_state_pb2.RobotState(
                    header=robot_types_pb2.MessageHeader(
                        client_id=FAKE_CLIENT_ID,
                    ),
                ),
            ),
        )
    )

  def test_framework_send_robot_state_with_client_id(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.send_robot_state(
        robot_state_pb2.RobotState(
            header=robot_types_pb2.MessageHeader(
                client_id=FAKE_CLIENT_ID,
            ),
        ),
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            xemb_message=xemb_pb2.XembMessage(
                client_id=FAKE_CLIENT_ID,
                robot_state=robot_state_pb2.RobotState(
                    header=robot_types_pb2.MessageHeader(
                        client_id=FAKE_CLIENT_ID,
                    ),
                ),
            ),
        )
    )

  def test_framework_create_button(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    callback_data = framework.create_button(
        "button_id",
        0.1,
        0.2,
        0.3,
        0.4,
        "label",
        30,
        False,
        background_color=robotics_ui_pb2.Color(
            red=0.1, green=0.2, blue=0.3, alpha=0.4
        ),
        transform=robotics_ui_pb2.UITransform(
            position=robot_types_pb2.Position(px=1.1, py=2.2, pz=3.3),
            rotation=robot_types_pb2.Quaternion(qx=4.4, qy=5.5, qz=6.6, qw=7.7),
            scale=robot_types_pb2.Position(px=8.8, py=9.9, pz=10.10),
        ),
        shortcuts=["shortcut1", "shortcut2"],
        hover_text="hover_text",
    )
    self.assertEqual(callback_data.element_id, "button_id")
    self.assertEqual(callback_data.element_type, _internal.ElementType.BUTTON)
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                button_create_request=robotics_ui_pb2.ButtonCreateRequest(
                    spec=robotics_ui_pb2.UISpec(
                        mode=robotics_ui_pb2.UIMode.UIMODE_PERSISTENT,
                        x=0.1,
                        y=0.2,
                        width=0.3,
                        height=0.4,
                        font_size=30,
                        background_color=robotics_ui_pb2.Color(
                            red=0.1, green=0.2, blue=0.3, alpha=0.4
                        ),
                        transform=robotics_ui_pb2.UITransform(
                            position=robot_types_pb2.Position(
                                px=1.1, py=2.2, pz=3.3
                            ),
                            rotation=robot_types_pb2.Quaternion(
                                qx=4.4, qy=5.5, qz=6.6, qw=7.7
                            ),
                            scale=robot_types_pb2.Position(
                                px=8.8, py=9.9, pz=10.10
                            ),
                        ),
                        hover_text="hover_text",
                    ),
                    button_id="button_id",
                    label="label",
                    shortcut=["shortcut1", "shortcut2"],
                )
            ),
        )
    )

  def test_framework_callback_button_pressed(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                button_pressed_event=robotics_ui_pb2.ButtonPressedEvent(
                    button_id="button_id"
                )
            )
        )
    )
    self._await_messages_processed(1.5)

    self.mock_callbacks.button_pressed.assert_called_once_with("button_id")

  def test_framework_block_on_button_pressed(self):
    unblocked = threading.Event()

    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    def _block_on_button_pressed() -> None:
      response = framework.block_on(
          framework.create_button("button_id", 0, 0, 0, 0, "")
      )
      self.assertEqual(response, "button_id")
      unblocked.set()

    thread = threading.Thread(target=_block_on_button_pressed, daemon=True)
    thread.start()
    self.assertTrue(
        framework.is_blocking_on.wait(5.0), "Framework never blocked"
    )
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                button_pressed_event=robotics_ui_pb2.ButtonPressedEvent(
                    button_id="button_id"
                )
            )
        )
    )
    self.assertTrue(unblocked.wait(5.0), "Framework never unblocked")

    self.mock_callbacks.button_pressed.assert_not_called()

  def test_block_on_cannot_be_called_on_synchronous_framework(self):
    framework = client.SynchronousFramework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    with self.assertRaises(ValueError):
      framework.block_on(framework.create_button("button_id", 0, 0, 0, 0, ""))

  def test_framework_create_dialog_defaults(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    callback_data = framework.create_dialog(
        "dialog_id",
        "title",
        "msg",
    )

    self.assertEqual(callback_data.element_id, "dialog_id")
    self.assertEqual(callback_data.element_type, _internal.ElementType.DIALOG)
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                dialog_create_request=robotics_ui_pb2.DialogCreateRequest(
                    spec=robotics_ui_pb2.UISpec(
                        mode=robotics_ui_pb2.UIMODE_MODAL,
                        width=0.2,
                        height=0.2,
                        x=0.5,
                        y=0.5,
                    ),
                    dialog_id="dialog_id",
                    title="title",
                    msg="msg",
                    buttons=["Yes", "No"],
                )
            ),
        )
    )

  def test_framework_create_dialog(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    callback_data = framework.create_dialog(
        "dialog_id",
        "title",
        "msg",
        buttons=["A", "B", "C"],
        spec=robotics_ui_pb2.UISpec(
            mode=robotics_ui_pb2.UIMODE_PERSISTENT,
            width=1.1,
            height=2.2,
            x=3.3,
            y=4.4,
        ),
    )

    self.assertEqual(callback_data.element_id, "dialog_id")
    self.assertEqual(callback_data.element_type, _internal.ElementType.DIALOG)
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                dialog_create_request=robotics_ui_pb2.DialogCreateRequest(
                    spec=robotics_ui_pb2.UISpec(
                        mode=robotics_ui_pb2.UIMODE_PERSISTENT,
                        width=1.1,
                        height=2.2,
                        x=3.3,
                        y=4.4,
                    ),
                    dialog_id="dialog_id",
                    title="title",
                    msg="msg",
                    buttons=["A", "B", "C"],
                )
            ),
        )
    )

  def test_framework_callback_dialog_pressed(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                dialog_pressed_event=robotics_ui_pb2.DialogPressedEvent(
                    dialog_id="dialog_id", choice="choice"
                )
            )
        )
    )
    self._await_messages_processed(1.5)

    self.mock_callbacks.dialog_pressed.assert_called_once_with(
        "dialog_id", "choice"
    )

  def test_framework_block_on_dialog_pressed(self):
    unblocked = threading.Event()

    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    def _block_on_dialog_pressed() -> None:
      response = framework.block_on(
          framework.create_dialog("dialog_id", "", "")
      )
      self.assertEqual(response, "choice")
      unblocked.set()

    thread = threading.Thread(target=_block_on_dialog_pressed, daemon=True)
    thread.start()
    self.assertTrue(
        framework.is_blocking_on.wait(5.0), "Framework never blocked"
    )
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                dialog_pressed_event=robotics_ui_pb2.DialogPressedEvent(
                    dialog_id="dialog_id",
                    choice="choice",
                )
            )
        )
    )
    self.assertTrue(unblocked.wait(5.0), "Framework never unblocked")

    self.mock_callbacks.dialog_pressed.assert_not_called()

  @parameterized.named_parameters(
      dict(testcase_name="Yes", choice="Yes", expected=True),
      dict(testcase_name="No", choice="No", expected=False),
  )
  def test_framework_ask_user_yes_no(self, choice: str, expected: bool):
    unblocked = threading.Event()

    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    def _block_on_dialog_pressed() -> None:
      response = framework.ask_user_yes_no("question")
      self.assertEqual(response, expected)
      unblocked.set()

    thread = threading.Thread(target=_block_on_dialog_pressed, daemon=True)
    thread.start()
    self.assertTrue(
        framework.is_blocking_on.wait(5.0), "Framework never blocked"
    )
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                dialog_pressed_event=robotics_ui_pb2.DialogPressedEvent(
                    dialog_id=str(uuid.UUID(int=1)),
                    choice=choice,
                )
            )
        )
    )
    self.assertTrue(unblocked.wait(5.0), "Framework never unblocked")

    self.mock_callbacks.dialog_pressed.assert_not_called()

  def test_framework_create_prompt(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    callback_data = framework.create_prompt(
        "prompt_id",
        "title",
        "msg",
        "submit_label",
        spec=robotics_ui_pb2.UISpec(
            mode=robotics_ui_pb2.UIMODE_NONMODAL,
            x=0.1,
            y=0.2,
            width=0.3,
            height=0.4,
        ),
        initial_value="initial_value",
        autofill_values=["test", "atest", "btest"],
    )
    self.assertEqual(callback_data.element_id, "prompt_id")
    self.assertEqual(callback_data.element_type, _internal.ElementType.PROMPT)
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                prompt_create_request=robotics_ui_pb2.PromptCreateRequest(
                    spec=robotics_ui_pb2.UISpec(
                        mode=robotics_ui_pb2.UIMode.UIMODE_NONMODAL,
                        x=0.1,
                        y=0.2,
                        width=0.3,
                        height=0.4,
                    ),
                    prompt_id="prompt_id",
                    title="title",
                    msg="msg",
                    submit_label="submit_label",
                    multiline_input=False,
                    initial_value="initial_value",
                    autofill_values=["test", "atest", "btest"],
                )
            ),
        )
    )

  def test_framework_callback_prompt_pressed(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                prompt_pressed_event=robotics_ui_pb2.PromptPressedEvent(
                    prompt_id="prompt_id",
                    input="choice",
                )
            )
        )
    )
    self._await_messages_processed(1.5)

    self.mock_callbacks.prompt_pressed.assert_called_once_with(
        "prompt_id", "choice"
    )

  def test_framework_block_on_prompt_pressed(self):
    unblocked = threading.Event()

    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    def _block_on_prompt_pressed() -> None:
      response = framework.block_on(
          framework.create_prompt(
              "prompt_id", "", "", "", robotics_ui_pb2.UISpec()
          )
      )
      self.assertEqual(response, "choice")
      unblocked.set()

    thread = threading.Thread(target=_block_on_prompt_pressed, daemon=True)
    thread.start()
    self.assertTrue(
        framework.is_blocking_on.wait(5.0), "Framework never blocked"
    )
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                prompt_pressed_event=robotics_ui_pb2.PromptPressedEvent(
                    prompt_id="prompt_id",
                    input="choice",
                )
            )
        )
    )
    self.assertTrue(unblocked.wait(5.0), "Framework never unblocked")

    self.mock_callbacks.prompt_pressed.assert_not_called()

  def test_framework_create_login(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    callback_data = framework.create_login()
    self.assertEqual(callback_data.element_id, "login:prompt_userid")
    self.assertEqual(callback_data.element_type, _internal.ElementType.PROMPT)
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                login_create_request=robotics_ui_pb2.LoginCreateRequest(
                    prompt_id="login:prompt_userid",
                    prompt_msg="Enter user id:",
                    prompt_title="Login",
                    submit_label="Log in",
                    prompt_spec=robotics_ui_pb2.UISpec(
                        x=0.5,
                        y=0.5,
                        height=0.2,
                        width=0.2,
                        mode=robotics_ui_pb2.UIMode.UIMODE_MODAL,
                    ),
                    text_id="login:text_userid",
                    text_spec=robotics_ui_pb2.UISpec(
                        x=0.5,
                        y=0.95,
                        height=0.05,
                        width=0.2,
                        mode=robotics_ui_pb2.UIMode.UIMODE_PERSISTENT,
                    ),
                    button_id="login:button_logout",
                    button_label="Log out",
                    button_spec=robotics_ui_pb2.UISpec(
                        x=0.7,
                        y=0.95,
                        height=0.05,
                        width=0.1,
                        mode=robotics_ui_pb2.UIMode.UIMODE_PERSISTENT,
                    ),
                )
            ),
        )
    )

  def test_framework_create_dropdown(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    callback_data = framework.create_dropdown(
        "dropdown_id",
        "title",
        "msg",
        ["A", "B", "C"],
        "submit_label",
        spec=robotics_ui_pb2.UISpec(
            mode=robotics_ui_pb2.UIMODE_NONMODAL,
            x=0.1,
            y=0.2,
            width=0.3,
            height=0.4,
        ),
        multi_select=True,
        initial_value="initial_value",
        initial_values=["initial_value1", "initial_value2"],
        shortcuts={"1": "A", "2": "B", "3": "C"},
    )
    self.assertEqual(callback_data.element_id, "dropdown_id")
    self.assertEqual(callback_data.element_type, _internal.ElementType.DROPDOWN)
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                dropdown_create_request=robotics_ui_pb2.DropdownCreateRequest(
                    spec=robotics_ui_pb2.UISpec(
                        mode=robotics_ui_pb2.UIMode.UIMODE_NONMODAL,
                        x=0.1,
                        y=0.2,
                        width=0.3,
                        height=0.4,
                    ),
                    dropdown_id="dropdown_id",
                    title="title",
                    msg="msg",
                    choices=["A", "B", "C"],
                    submit_label="submit_label",
                    multi_select=True,
                    initial_value="initial_value",
                    initial_values=["initial_value1", "initial_value2"],
                    shortcuts={"1": "A", "2": "B", "3": "C"},
                )
            ),
        )
    )

  def test_framework_callback_dropdown_pressed(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                dropdown_pressed_event=robotics_ui_pb2.DropdownPressedEvent(
                    dropdown_id="dropdown_id",
                    choice="choice",
                )
            )
        )
    )
    self._await_messages_processed(1.5)

    self.mock_callbacks.dropdown_pressed.assert_called_once_with(
        "dropdown_id", "choice"
    )

  def test_framework_block_on_dropdown_pressed(self):
    unblocked = threading.Event()

    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    def _block_on_dropdown_pressed() -> None:
      response = framework.block_on(
          framework.create_dropdown(
              "dropdown_id", "", "", [], "", robotics_ui_pb2.UISpec()
          )
      )
      self.assertEqual(response, "choice")
      unblocked.set()

    thread = threading.Thread(target=_block_on_dropdown_pressed, daemon=True)
    thread.start()
    self.assertTrue(
        framework.is_blocking_on.wait(5.0), "Framework never blocked"
    )
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                dropdown_pressed_event=robotics_ui_pb2.DropdownPressedEvent(
                    dropdown_id="dropdown_id",
                    choice="choice",
                )
            )
        )
    )
    self.assertTrue(unblocked.wait(5.0), "Framework never unblocked")

    self.mock_callbacks.dropdown_pressed.assert_not_called()

  def test_framework_block_on_with_value(self):
    unblocked = threading.Event()

    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    def _block_on_dropdown_pressed() -> None:
      with self.assertRaises(TypeError):
        framework.block_on(
            framework.create_dropdown(
                "dropdown_id", "", "", [], "", robotics_ui_pb2.UISpec()
            )
        )
      unblocked.set()

    def _block_on_with_value_dropdown_pressed() -> None:
      response = framework.block_on_with_value(
          framework.create_dropdown(
              "dropdown_id", "", "", [], "", robotics_ui_pb2.UISpec()
          )
      )
      self.assertEqual(response, ["choice1", "choice2"])
      unblocked.set()

    rui_message = robotics_ui_pb2.RuiMessage(
        ui_message=robotics_ui_pb2.UIMessage(
            dropdown_pressed_event=robotics_ui_pb2.DropdownPressedEvent(
                dropdown_id="dropdown_id",
                choices=["choice1", "choice2"],
            )
        )
    )

    # Test block_on() with a non-str return value. This should raise a
    # TypeError.
    thread = threading.Thread(target=_block_on_dropdown_pressed, daemon=True)
    thread.start()
    self.assertTrue(
        framework.is_blocking_on.wait(5.0), "Framework never blocked"
    )
    self._queue_response(rui_message)
    self.assertTrue(unblocked.wait(5.0), "Framework never unblocked")
    unblocked.clear()

    # Test block_on_with_value() with a list[str] return value. This should not
    # raise a TypeError.
    thread = threading.Thread(
        target=_block_on_with_value_dropdown_pressed, daemon=True
    )
    thread.start()
    self.assertTrue(
        framework.is_blocking_on.wait(5.0), "Framework never blocked"
    )
    self._queue_response(rui_message)
    self.assertTrue(unblocked.wait(5.0), "Framework never unblocked")

    self.mock_callbacks.dropdown_pressed.assert_not_called()

  def test_framework_make_camera_window(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.make_camera_window(
        sensor_id=456,
        title="title",
        spec=robotics_ui_pb2.UISpec(
            mode=robotics_ui_pb2.UIMODE_NONMODAL,
            x=0.1,
            y=0.2,
            width=0.3,
            height=0.4,
        ),
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                image_window_request=robotics_ui_pb2.ImageWindowRequest(
                    sensor_id=456,
                    title="title",
                    window_id="image_window:title",
                    spec=robotics_ui_pb2.UISpec(
                        mode=robotics_ui_pb2.UIMODE_NONMODAL,
                        x=0.1,
                        y=0.2,
                        width=0.3,
                        height=0.4,
                    ),
                )
            ),
        )
    )

  def test_framework_display_splash_screen(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.display_splash_screen(
        jpeg_image=b"\x01\x02",
        cols=100,
        rows=200,
        timeout_seconds=1.1,
        spec=robotics_ui_pb2.UISpec(
            mode=robotics_ui_pb2.UIMODE_NONMODAL,
            x=0.1,
            y=0.2,
            width=0.3,
            height=0.4,
        ),
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                splash_screen_request=robotics_ui_pb2.SplashScreenRequest(
                    jpeg_image=robot_state_pb2.CameraImage(
                        pixel_type=JPEG_PIXEL_TYPE,
                        cols=100,
                        rows=200,
                        data=b"\x01\x02",
                    ),
                    timeout_seconds=1.1,
                    spec=robotics_ui_pb2.UISpec(
                        mode=robotics_ui_pb2.UIMODE_NONMODAL,
                        x=0.1,
                        y=0.2,
                        width=0.3,
                        height=0.4,
                    ),
                ),
            ),
        )
    )

  def test_framework_display_splash_screen_compute_cols_and_rows(self):
    with open((CAT_IMAGE_PATH), "rb") as f:
      jpeg_image = f.read()

    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.display_splash_screen(
        jpeg_image=jpeg_image,
        timeout_seconds=1.1,
        spec=robotics_ui_pb2.UISpec(
            mode=robotics_ui_pb2.UIMODE_NONMODAL,
            x=0.1,
            y=0.2,
            width=0.3,
            height=0.4,
        ),
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                splash_screen_request=robotics_ui_pb2.SplashScreenRequest(
                    jpeg_image=robot_state_pb2.CameraImage(
                        pixel_type=JPEG_PIXEL_TYPE,
                        cols=287,
                        rows=175,
                        data=jpeg_image,
                    ),
                    timeout_seconds=1.1,
                    spec=robotics_ui_pb2.UISpec(
                        mode=robotics_ui_pb2.UIMODE_NONMODAL,
                        x=0.1,
                        y=0.2,
                        width=0.3,
                        height=0.4,
                    ),
                ),
            ),
        )
    )

  @parameterized.named_parameters(
      dict(
          testcase_name="100_200",
          cols=100,
          rows=200,
          x=0.375,
          y=0.25,
          width=0.25,
          height=0.5,
      ),
      dict(
          testcase_name="200_100",
          cols=200,
          rows=100,
          x=0.25,
          y=0.375,
          width=0.5,
          height=0.25,
      ),
  )
  def test_framework_display_splash_screen_aspect_ratio(
      self,
      cols: int,
      rows: int,
      x: float,
      y: float,
      width: float,
      height: float,
  ):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.display_splash_screen(
        jpeg_image=b"\x01\x02",
        cols=cols,
        rows=rows,
        timeout_seconds=1.1,
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                splash_screen_request=robotics_ui_pb2.SplashScreenRequest(
                    jpeg_image=robot_state_pb2.CameraImage(
                        pixel_type=JPEG_PIXEL_TYPE,
                        cols=cols,
                        rows=rows,
                        data=b"\x01\x02",
                    ),
                    timeout_seconds=1.1,
                    spec=robotics_ui_pb2.UISpec(
                        mode=robotics_ui_pb2.UIMODE_PERSISTENT,
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                    ),
                ),
            ),
        )
    )

  def test_framework_display_send_jpeg_image(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.send_jpeg_image(
        camera_index=1,
        jpeg_image=b"\x01\x02",
        cols=222,
        rows=333,
        sample_timestamp_nsec=444,
        seq=555,
        sensor_id=666,
        publish_timestamp_nsec=777,
        client_id=FAKE_CLIENT_ID,
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            xemb_message=xemb_pb2.XembMessage(
                client_id=FAKE_CLIENT_ID,
                robot_state=robot_state_pb2.RobotState(
                    header=robot_types_pb2.MessageHeader(
                        sample_timestamp_nsec=444,
                        publish_timestamp_nsec=777,
                        client_id=FAKE_CLIENT_ID,
                    ),
                    parts=robot_state_pb2.PartsState(
                        world=robot_state_pb2.PartState(
                            cameras=[
                                robot_state_pb2.CameraImage(),
                                robot_state_pb2.CameraImage(
                                    header=robot_types_pb2.SensorHeader(
                                        sample_timestamp_nsec=444,
                                        sequence_number=555,
                                        sensor_id=666,
                                    ),
                                    pixel_type=JPEG_PIXEL_TYPE,
                                    cols=222,
                                    rows=333,
                                    data=b"\x01\x02",
                                ),
                            ]
                        )
                    ),
                ),
            ),
        )
    )

  def test_framework_display_send_jpeg_image_defaults(self):
    with open((CAT_IMAGE_PATH), "rb") as f:
      jpeg_image = f.read()

    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.send_jpeg_image(
        camera_index=1,
        jpeg_image=jpeg_image,
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            xemb_message=xemb_pb2.XembMessage(
                client_id=robot_types_pb2.ClientID(),
                robot_state=robot_state_pb2.RobotState(
                    header=robot_types_pb2.MessageHeader(
                        sample_timestamp_nsec=FAKE_NSEC_VALUE,
                        publish_timestamp_nsec=FAKE_NSEC_VALUE,
                        client_id=robot_types_pb2.ClientID(),
                    ),
                    parts=robot_state_pb2.PartsState(
                        world=robot_state_pb2.PartState(
                            cameras=[
                                robot_state_pb2.CameraImage(),
                                robot_state_pb2.CameraImage(
                                    header=robot_types_pb2.SensorHeader(
                                        sample_timestamp_nsec=FAKE_NSEC_VALUE,
                                        sequence_number=0,
                                        sensor_id=1,
                                    ),
                                    pixel_type=JPEG_PIXEL_TYPE,
                                    data=jpeg_image,
                                    cols=287,
                                    rows=175,
                                ),
                            ]
                        )
                    ),
                ),
            ),
        )
    )

  def test_framework_display_send_jpeg_images(self):
    camera_images: list[client.JpegCameraImageData] = [
        None,
        None,
        None,
        None,
    ]

    with open((CAT_IMAGE_PATH), "rb") as f:
      camera_images[1] = client.JpegCameraImageData(
          jpeg_image=f.read(),
          sample_timestamp_nsec=FAKE_NSEC_VALUE,
      )

    with open((CAT_IMAGE_PATH), "rb") as f:
      camera_images[3] = client.JpegCameraImageData(
          jpeg_image=f.read(),
          sensor_id=400,
          sample_timestamp_nsec=FAKE_NSEC_VALUE + 100,
      )

    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.send_jpeg_images(
        jpeg_camera_image_data=camera_images,
        publish_timestamp_nsec=FAKE_NSEC_VALUE + 200,
        client_id=FAKE_CLIENT_ID,
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            xemb_message=xemb_pb2.XembMessage(
                client_id=FAKE_CLIENT_ID,
                robot_state=robot_state_pb2.RobotState(
                    header=robot_types_pb2.MessageHeader(
                        sample_timestamp_nsec=FAKE_NSEC_VALUE + 100,
                        publish_timestamp_nsec=FAKE_NSEC_VALUE + 200,
                        client_id=FAKE_CLIENT_ID,
                    ),
                    parts=robot_state_pb2.PartsState(
                        world=robot_state_pb2.PartState(
                            cameras=[
                                robot_state_pb2.CameraImage(),
                                robot_state_pb2.CameraImage(
                                    header=robot_types_pb2.SensorHeader(
                                        sample_timestamp_nsec=FAKE_NSEC_VALUE,
                                        sequence_number=0,
                                        sensor_id=1,
                                    ),
                                    pixel_type=JPEG_PIXEL_TYPE,
                                    data=camera_images[1].jpeg_image,
                                    cols=287,
                                    rows=175,
                                ),
                                robot_state_pb2.CameraImage(),
                                robot_state_pb2.CameraImage(
                                    header=robot_types_pb2.SensorHeader(
                                        sample_timestamp_nsec=(
                                            FAKE_NSEC_VALUE + 100
                                        ),
                                        sequence_number=0,
                                        sensor_id=400,
                                    ),
                                    pixel_type=JPEG_PIXEL_TYPE,
                                    cols=287,
                                    rows=175,
                                    data=camera_images[3].jpeg_image,
                                ),
                            ]
                        )
                    ),
                ),
            ),
        )
    )

  def test_framework_create_or_update_object(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.create_or_update_object(
        object_id="object_id",
        object_type=robotics_ui_pb2.ObjectType.CUBE_UNIT,
        transform=client.make_transform(
            client.make_position(0, 1, 2),
            client.make_quaternion_from_euler(0, 0, 0),
            client.make_scale(1, 1, 1),
        ),
        transform_type=client.TransformType.LOCAL,
        parent_id="parent_id",
        params={"param1": "value1"},
        robot_id="robot_id",
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                object_create_or_update_request=robotics_ui_pb2.ObjectCreateOrUpdateRequest(
                    object_id="object_id",
                    object_type=robotics_ui_pb2.ObjectType.CUBE_UNIT,
                    local_transform=client.make_transform(
                        client.make_position(0, 1, 2),
                        client.make_quaternion_from_euler(0, 0, 0),
                        client.make_scale(1, 1, 1),
                    ),
                    parent_id="parent_id",
                    params={"param1": "value1"},
                    robot_id="robot_id",
                )
            ),
        )
    )

  def test_framework_create_or_update_object_defaults(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.create_or_update_object(
        object_id="object_id",
        object_type=robotics_ui_pb2.ObjectType.CUBE_UNIT,
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                object_create_or_update_request=robotics_ui_pb2.ObjectCreateOrUpdateRequest(
                    object_id="object_id",
                    object_type=robotics_ui_pb2.ObjectType.CUBE_UNIT,
                    global_transform=client.make_transform(
                        client.make_position(0, 0, 0),
                        client.make_quaternion_from_euler(0, 0, 0),
                        client.make_scale(1, 1, 1),
                    ),
                    params={},
                )
            ),
        )
    )

  def test_framework_create_or_update_object_client_id(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.create_or_update_object(
        object_id="object_id",
        object_type=robotics_ui_pb2.ObjectType.CUBE_UNIT,
        robot_id=FAKE_CLIENT_ID,
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                object_create_or_update_request=robotics_ui_pb2.ObjectCreateOrUpdateRequest(
                    object_id="object_id",
                    object_type=robotics_ui_pb2.ObjectType.CUBE_UNIT,
                    global_transform=client.make_transform(
                        client.make_position(0, 0, 0),
                        client.make_quaternion_from_euler(0, 0, 0),
                        client.make_scale(1, 1, 1),
                    ),
                    params={},
                    client_id=FAKE_CLIENT_ID,
                )
            ),
        )
    )

  def test_framework_clear_objects(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.clear_objects()

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                clear_objects_request=robotics_ui_pb2.ClearObjectsRequest(
                    prefix=""
                )
            ),
        )
    )

  def test_framework_clear_gui(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.clear_gui()

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                clear_gui_request=robotics_ui_pb2.ClearGuiRequest(prefix="")
            ),
        )
    )

  def test_framework_clear_all(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.clear_all()

    self.assertSequenceEqual(
        [
            mock.call(
                robotics_ui_pb2.RuiMessage(
                    message_id=str(uuid.UUID(int=1)),
                    ui_message=robotics_ui_pb2.UIMessage(
                        clear_objects_request=robotics_ui_pb2.ClearObjectsRequest(
                            prefix=""
                        )
                    ),
                )
            ),
            mock.call(
                robotics_ui_pb2.RuiMessage(
                    message_id=str(uuid.UUID(int=2)),
                    ui_message=robotics_ui_pb2.UIMessage(
                        clear_gui_request=robotics_ui_pb2.ClearGuiRequest(
                            prefix=""
                        )
                    ),
                )
            ),
        ],
        self.mock_client.send_message.call_args_list,
    )

  def test_framework_clear_objects_with_prefix(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.clear_objects(prefix="prefix")

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                clear_objects_request=robotics_ui_pb2.ClearObjectsRequest(
                    prefix="prefix"
                )
            ),
        )
    )

  def test_framework_clear_gui_with_prefix(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.clear_gui(prefix="prefix")

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                clear_gui_request=robotics_ui_pb2.ClearGuiRequest(
                    prefix="prefix"
                )
            ),
        )
    )

  def test_framework_clear_all_with_prefix(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.clear_all(prefix="prefix")

    self.assertSequenceEqual(
        [
            mock.call(
                robotics_ui_pb2.RuiMessage(
                    message_id=str(uuid.UUID(int=1)),
                    ui_message=robotics_ui_pb2.UIMessage(
                        clear_objects_request=robotics_ui_pb2.ClearObjectsRequest(
                            prefix="prefix"
                        )
                    ),
                )
            ),
            mock.call(
                robotics_ui_pb2.RuiMessage(
                    message_id=str(uuid.UUID(int=2)),
                    ui_message=robotics_ui_pb2.UIMessage(
                        clear_gui_request=robotics_ui_pb2.ClearGuiRequest(
                            prefix="prefix"
                        )
                    ),
                )
            ),
        ],
        self.mock_client.send_message.call_args_list,
    )

  def test_framework_delete_object(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.delete_object("object_id")

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                object_delete_request=robotics_ui_pb2.ObjectDeleteRequest(
                    object_id="object_id"
                )
            ),
        )
    )

  def test_framework_reparent_object(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.reparent_object("object_id", "parent_id")

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                object_reparent_request=robotics_ui_pb2.ObjectReparentRequest(
                    object_id="object_id",
                    parent_id="parent_id",
                )
            ),
        )
    )

  def test_framework_create_or_update_text(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.create_or_update_text(
        text_id="text_id",
        text='<align="right">text',
        spec=robotics_ui_pb2.UISpec(
            x=1.1,
            y=2.2,
            width=3.3,
            height=4.4,
            background_color=robotics_ui_pb2.Color(
                red=0.1, green=0.2, blue=0.3, alpha=0.4
            ),
        ),
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                text_create_or_update_request=robotics_ui_pb2.TextCreateOrUpdateRequest(
                    text_id="text_id",
                    text='<align="right">text',
                    spec=robotics_ui_pb2.UISpec(
                        x=1.1,
                        y=2.2,
                        width=3.3,
                        height=4.4,
                        background_color=robotics_ui_pb2.Color(
                            red=0.1, green=0.2, blue=0.3, alpha=0.4
                        ),
                    ),
                    scrollable=False,
                )
            ),
        )
    )

  def test_framework_create_or_update_text_defaults(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.create_or_update_text(
        text_id="text_id",
        text='<align="right">text',
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                text_create_or_update_request=robotics_ui_pb2.TextCreateOrUpdateRequest(
                    text_id="text_id",
                    text='<align="right">text',
                    scrollable=False,
                )
            ),
        )
    )

  def test_framework_remove_element(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.remove_element(element_id="element_id")

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                remove_gui_element_request=robotics_ui_pb2.RemoveGuiElementRequest(
                    element_id="element_id",
                )
            ),
        )
    )

  def test_framework_create_chat(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.create_chat(
        chat_id="chat_id",
        title="title",
        submit_label="submit_label",
        interactive=True,
        spec=robotics_ui_pb2.UISpec(
            x=0.1,
            y=0.2,
            width=0.3,
            height=0.4,
        ),
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                chat_create_request=robotics_ui_pb2.ChatCreateRequest(
                    chat_id="chat_id",
                    title="title",
                    submit_label="submit_label",
                    interactive=True,
                    spec=robotics_ui_pb2.UISpec(
                        x=0.1,
                        y=0.2,
                        width=0.3,
                        height=0.4,
                    ),
                )
            ),
        )
    )

  def test_framework_add_chat_line(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.add_chat_line(
        chat_id="chat_id",
        text="text",
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                add_chat_line=robotics_ui_pb2.AddChatLine(
                    chat_id="chat_id",
                    text="text",
                )
            ),
        )
    )

  def test_framework_callback_chat_received(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                chat_pressed_event=robotics_ui_pb2.ChatPressedEvent(
                    chat_id="chat_id",
                    input="Hello world",
                )
            ),
        )
    )
    self._await_messages_processed(1.5)

    self.mock_callbacks.chat_received.assert_called_once_with(
        "chat_id", "Hello world"
    )

  def test_framework_send_prompt_pressed_event(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.send_prompt_pressed_event("prompt_id", "data")

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                prompt_pressed_event=robotics_ui_pb2.PromptPressedEvent(
                    prompt_id="prompt_id",
                    input="data",
                )
            ),
        )
    )

  def test_framework_send_dialog_pressed_event(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.send_dialog_pressed_event("dialog_id", "choice")

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                dialog_pressed_event=robotics_ui_pb2.DialogPressedEvent(
                    dialog_id="dialog_id",
                    choice="choice",
                )
            ),
        )
    )

  def test_framework_send_dropdown_pressed_event(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.send_dropdown_pressed_event("dropdown_id", "choice")

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                dropdown_pressed_event=robotics_ui_pb2.DropdownPressedEvent(
                    dropdown_id="dropdown_id",
                    choice="choice",
                )
            ),
        )
    )

  def test_framework_send_multiselect_dropdown_pressed_event(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    framework.send_dropdown_pressed_event(
        "dropdown_id", ["choice1", "choice2"]
    )
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                dropdown_pressed_event=robotics_ui_pb2.DropdownPressedEvent(
                    dropdown_id="dropdown_id",
                    choices=["choice1", "choice2"],
                )
            ),
        )
    )

  def test_framework_send_button_pressed_event(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.send_button_pressed_event("button_id")

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                button_pressed_event=robotics_ui_pb2.ButtonPressedEvent(
                    button_id="button_id",
                )
            ),
        )
    )

  def test_framework_setup_header(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.setup_header(
        height=0.1, visible=True, collapsible=True, expandable=True
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                setup_header_request=robotics_ui_pb2.SetupHeaderRequest(
                    height=0.1,
                    visible=True,
                    collapsible=True,
                    expandable=True,
                )
            ),
        )
    )

  def test_framework_get_gui_element_value(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    callback_data = framework.get_gui_element_value("text_id")
    self.assertEqual(callback_data.element_id, "text_id")
    self.assertEqual(callback_data.element_type, _internal.ElementType.UNKNOWN)
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                gui_element_value_request=robotics_ui_pb2.GuiElementValueRequest(
                    element_id="text_id"
                )
            ),
        )
    )

  def test_framework_block_on_get_gui_element_value(self):
    unblocked = threading.Event()

    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    def _block_on_get_gui_element_value() -> None:
      framework.create_or_update_text("text_id", "text")
      response = framework.block_on(framework.get_gui_element_value("text_id"))
      self.assertEqual(response, "text")
      unblocked.set()

    thread = threading.Thread(
        target=_block_on_get_gui_element_value, daemon=True
    )
    thread.start()
    self.assertTrue(
        framework.is_blocking_on.wait(5.0), "Framework never blocked"
    )
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                gui_element_value_response=robotics_ui_pb2.GuiElementValueResponse(
                    element_id="text_id",
                    value="text",
                )
            ),
        )
    )
    self.assertTrue(unblocked.wait(5.0), "Framework never unblocked")

    self.mock_callbacks.gui_element_value_response.assert_not_called()

  def test_framework_send_console_command(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.send_console_command(
        command="command",
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                console_command="command",
            ),
        )
    )

  def test_framework_upload_file(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks,
        mock_clients=[self.mock_client],
        mock_upload_engine=self.mock_upload_engine,
    )
    framework.connect()

    framework.upload_file(pathlib.Path("/path/to/file.txt"))

    self.mock_upload_engine.upload_file.assert_called_once_with(
        pathlib.Path("/path/to/file.txt")
    )

  def test_framework_upload_resource(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks,
        mock_clients=[self.mock_client],
        mock_upload_engine=self.mock_upload_engine,
    )
    framework.connect()

    framework.upload_resource(
        client.ResourceLocator(
            scheme="mesh",
            path="original_stl_path.stl",
            data=TEST_FILE_DATA,
        )
    )

    self.mock_upload_engine.upload_resource.assert_called_once_with(
        client.ResourceLocator(
            scheme="mesh",
            path="original_stl_path.stl",
            data=TEST_FILE_DATA,
        )
    )

  def test_framework_upload_stl_file_not_found(self):
    self.mock_stl_parser.side_effect = FileNotFoundError
    framework = client.Framework(
        callbacks=self.mock_callbacks,
        mock_clients=[self.mock_client],
        mock_upload_engine=self.mock_upload_engine,
        mock_stl_parser=self.mock_stl_parser,
    )
    framework.connect()

    with self.assertRaises(client.FileUploadError):
      framework.upload_stl_file(pathlib.Path("/path/to/file.stl"))

  def test_framework_upload_stl_file_parse_error(self):
    self.mock_stl_parser.side_effect = client.StlParseError
    framework = client.Framework(
        callbacks=self.mock_callbacks,
        mock_clients=[self.mock_client],
        mock_upload_engine=self.mock_upload_engine,
        mock_stl_parser=self.mock_stl_parser,
    )
    framework.connect()

    with self.assertRaises(client.FileUploadError):
      framework.upload_stl_file(pathlib.Path("/path/to/file.stl"))

  def test_framework_upload_stl_file_success(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks,
        mock_clients=[self.mock_client],
        mock_upload_engine=self.mock_upload_engine,
        mock_stl_parser=self.mock_stl_parser,
    )
    framework.connect()

    framework.upload_stl_file(pathlib.Path("/path/to/file.stl"))
    self.mock_upload_engine.upload_resource.assert_called_once_with(
        client.ResourceLocator(
            scheme="mesh",
            path=pathlib.Path("/path/to/file.stl"),
            data=EXPECTED_STL_DATA.SerializeToString(),
        )
    )

  def test_framework_upload_kinematic_tree_robot(self):
    upload_request_sent = threading.Event()

    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    # Mock the check file cache response, so that we don't try to upload the
    # file, but instead pretend that the file is already in the cache. Also, if
    # the message was a upload_kinematic_tree_robot_request, then respond with
    # a success.
    def _send_message_mock(message: robotics_ui_pb2.RuiMessage) -> str:
      if message.ui_message.HasField("check_file_cache_request"):
        self._queue_response(
            robotics_ui_pb2.RuiMessage(
                ui_message=robotics_ui_pb2.UIMessage(
                    check_file_cache_response=robotics_ui_pb2.CheckFileCacheResponse(
                        hash=message.ui_message.check_file_cache_request.hash,
                        in_cache=True,
                    )
                )
            )
        )
      elif message.ui_message.HasField("upload_kinematic_tree_robot_request"):
        self._queue_response(
            robotics_ui_pb2.RuiMessage(
                ui_message=robotics_ui_pb2.UIMessage(
                    upload_kinematic_tree_robot_response=robotics_ui_pb2.UploadKinematicTreeRobotResponse(
                        success=True
                    )
                )
            )
        )
        upload_request_sent.set()
      return ""

    self.mock_client.send_message.side_effect = _send_message_mock

    xml_path = pathlib.Path(
        (TESTDIR / "kinematic_tree_robot.xml")
    )
    framework.upload_kinematic_tree_robot(
        kinematic_tree_robot_id="kinematic_tree_robot",
        xml_path=xml_path,
        joint_mapping={},
        timeout=datetime.timedelta(seconds=5),
    )
    self.assertTrue(
        upload_request_sent.wait(5.0),
        "upload_kinematic_tree_robot_request not sent",
    )

  def test_framework_upload_zipped_kinematic_tree_robot(self):
    upload_request_sent = threading.Event()

    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    # Mock the check file cache response, so that we don't try to upload the
    # file, but instead pretend that the file is already in the cache. Also, if
    # the message was a upload_kinematic_tree_robot_request, then respond with
    # a success.
    def _send_message_mock(message: robotics_ui_pb2.RuiMessage) -> str:
      if message.ui_message.HasField("check_file_cache_request"):
        self._queue_response(
            robotics_ui_pb2.RuiMessage(
                ui_message=robotics_ui_pb2.UIMessage(
                    check_file_cache_response=robotics_ui_pb2.CheckFileCacheResponse(
                        hash=message.ui_message.check_file_cache_request.hash,
                        in_cache=True,
                    )
                )
            )
        )
      elif message.ui_message.HasField("upload_kinematic_tree_robot_request"):
        self._queue_response(
            robotics_ui_pb2.RuiMessage(
                ui_message=robotics_ui_pb2.UIMessage(
                    upload_kinematic_tree_robot_response=robotics_ui_pb2.UploadKinematicTreeRobotResponse(
                        success=True
                    )
                )
            )
        )
        upload_request_sent.set()
      return ""

    self.mock_client.send_message.side_effect = _send_message_mock

    with tempfile.NamedTemporaryFile(
        mode="wb", suffix=".zip", delete=False
    ) as zip_file:
      with zipfile.ZipFile(zip_file.name, mode="w") as zf:
        for file in [
            "kinematic_tree_robot.xml",
            "kinematic_tree_robot_joint_mapping.json",
            "kinematic_tree_robot_sites.json",
            "mesh_left_arm.stl",
            "mesh_right_arm.stl",
            "mesh_torso.stl",
            "mesh_head.stl",
        ]:
          zf.write((TESTDIR / file), file)

      framework.upload_zipped_kinematic_tree_robot(
          kinematic_tree_robot_id="kinematic_tree_robot",
          zip_path=zip_file.name,
          xml_path="kinematic_tree_robot.xml",
          timeout=datetime.timedelta(seconds=1),
      )

      self.assertTrue(
          upload_request_sent.wait(5.0),
          "upload_kinematic_tree_robot_request not sent",
      )

  def test_framework_create_form(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    framework.create_form(
        form_id="form_dialog",
        title="Form",
        submit_label="Submit",
        spec=robotics_ui_pb2.UISpec(
            mode=robotics_ui_pb2.UIMode.UIMODE_MODAL,
            x=0.5,
            y=0.5,
            height=0.2,
            width=0.2,
        ),
        create_requests=[
            framework.create_text_message(
                text_id="form_text",
                text="Hello world",
            ),
            framework.create_dropdown_message(
                dropdown_id="form_dropdown",
                title="Choose a color",
                msg="Which color do you want?",
                choices=["red", "green", "blue"],
                submit_label="Submit",
                initial_value="red",
            ),
            framework.create_dropdown_message(
                dropdown_id="form_dropdown",
                title="Choose another color",
                msg="Which color do you want?",
                choices=["yellow", "purple", "pink", "brown"],
                submit_label="Submit",
                multi_select=True,
                initial_values=["yellow", "brown"],
            ),
            framework.create_prompt_message(
                prompt_id="form_prompt",
                title="Enter a number",
                msg="Enter a number between 1 and 10",
                submit_label="Submit",
                autofill_values=["1", "2", "3", "4", "5"],
            ),
            framework.create_button_message(
                button_id="form_button",
                label="Submit",
                shortcuts=None,
            ),
            framework.create_row_message(
                create_requests=[
                    framework.create_text_message(
                        text_id="form_text_row",
                        text="Hello world",
                    ),
                    framework.create_button_message(
                        button_id="form_button_row",
                        label="Do something",
                        shortcuts=None,
                    ),
                ]
            ),
        ],
    )

    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=9)),
            ui_message=robotics_ui_pb2.UIMessage(
                form_create_request=robotics_ui_pb2.FormCreateRequest(
                    form_id="form_dialog",
                    title="Form",
                    submit_label="Submit",
                    spec=robotics_ui_pb2.UISpec(
                        mode=robotics_ui_pb2.UIMode.UIMODE_MODAL,
                        x=0.5,
                        y=0.5,
                        height=0.2,
                        width=0.2,
                    ),
                    create_requests=[
                        robotics_ui_pb2.RuiMessage(
                            message_id=str(uuid.UUID(int=1)),
                            ui_message=robotics_ui_pb2.UIMessage(
                                text_create_or_update_request=robotics_ui_pb2.TextCreateOrUpdateRequest(
                                    text_id="form_text",
                                    text="Hello world",
                                )
                            ),
                        ),
                        robotics_ui_pb2.RuiMessage(
                            message_id=str(uuid.UUID(int=2)),
                            ui_message=robotics_ui_pb2.UIMessage(
                                dropdown_create_request=robotics_ui_pb2.DropdownCreateRequest(
                                    dropdown_id="form_dropdown",
                                    title="Choose a color",
                                    msg="Which color do you want?",
                                    choices=["red", "green", "blue"],
                                    submit_label="Submit",
                                    spec=None,
                                    initial_value="red",
                                )
                            ),
                        ),
                        robotics_ui_pb2.RuiMessage(
                            message_id=str(uuid.UUID(int=3)),
                            ui_message=robotics_ui_pb2.UIMessage(
                                dropdown_create_request=robotics_ui_pb2.DropdownCreateRequest(
                                    dropdown_id="form_dropdown",
                                    title="Choose another color",
                                    msg="Which color do you want?",
                                    choices=[
                                        "yellow",
                                        "purple",
                                        "pink",
                                        "brown",
                                    ],
                                    submit_label="Submit",
                                    spec=None,
                                    multi_select=True,
                                    initial_values=["yellow", "brown"],
                                )
                            )
                        ),
                        robotics_ui_pb2.RuiMessage(
                            message_id=str(uuid.UUID(int=4)),
                            ui_message=robotics_ui_pb2.UIMessage(
                                prompt_create_request=robotics_ui_pb2.PromptCreateRequest(
                                    prompt_id="form_prompt",
                                    title="Enter a number",
                                    msg="Enter a number between 1 and 10",
                                    submit_label="Submit",
                                    autofill_values=["1", "2", "3", "4", "5"],
                                    spec=None,
                                )
                            ),
                        ),
                        robotics_ui_pb2.RuiMessage(
                            message_id=str(uuid.UUID(int=5)),
                            ui_message=robotics_ui_pb2.UIMessage(
                                button_create_request=robotics_ui_pb2.ButtonCreateRequest(
                                    button_id="form_button",
                                    label="Submit",
                                    spec=None,
                                    shortcut=None,
                                )
                            ),
                        ),
                        robotics_ui_pb2.RuiMessage(
                            message_id=str(uuid.UUID(int=8)),
                            ui_message=robotics_ui_pb2.UIMessage(
                                row_create_request=robotics_ui_pb2.RowCreateRequest(
                                    create_requests=[
                                        robotics_ui_pb2.RuiMessage(
                                            message_id=str(uuid.UUID(int=6)),
                                            ui_message=robotics_ui_pb2.UIMessage(
                                                text_create_or_update_request=robotics_ui_pb2.TextCreateOrUpdateRequest(
                                                    text_id="form_text_row",
                                                    text="Hello world",
                                                )
                                            ),
                                        ),
                                        robotics_ui_pb2.RuiMessage(
                                            message_id=str(uuid.UUID(int=7)),
                                            ui_message=robotics_ui_pb2.UIMessage(
                                                button_create_request=robotics_ui_pb2.ButtonCreateRequest(
                                                    button_id="form_button_row",
                                                    label="Do something",
                                                    spec=None,
                                                    shortcut=None,
                                                )
                                            ),
                                        ),
                                    ]
                                )
                            ),
                        ),
                    ],
                )
            ),
        )
    )

  def test_framework_block_on_form_pressed_with_callback(self):
    unblocked = threading.Event()

    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    def _block_on_form_pressed() -> None:
      print("blocking")
      response = framework.block_on(
          framework.create_form(
              form_id="form_dialog",
              title="Form",
              submit_label="Submit",
              spec=robotics_ui_pb2.UISpec(
                  mode=robotics_ui_pb2.UIMode.UIMODE_MODAL,
                  x=0.5,
                  y=0.5,
                  height=0.2,
                  width=0.2,
              ),
              create_requests=[],
          )
      )
      print(response)
      self.assertEqual(response, "text")
      unblocked.set()

    thread = threading.Thread(target=_block_on_form_pressed, daemon=True)
    thread.start()
    self.assertTrue(
        framework.is_blocking_on.wait(5.0), "Framework never blocked"
    )
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                form_pressed_event=robotics_ui_pb2.FormPressedEvent(
                    form_id="form_dialog",
                    results="text",
                )
            ),
        )
    )
    self.assertTrue(unblocked.wait(5.0), "Framework never unblocked")

    self.mock_callbacks.form_pressed.assert_not_called()

  def test_framework_register_remote_command(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    framework.register_remote_command("command", "description")
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                register_remote_command=robotics_ui_pb2.RegisterRemoteCommand(
                    command="command",
                    description="description",
                )
            ),
        )
    )

  def test_framework_unregister_remote_command(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    framework.unregister_remote_command("command")
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                unregister_remote_command=robotics_ui_pb2.UnregisterRemoteCommand(
                    command="command",
                )
            ),
        )
    )

  def test_framework_create_embodiable_pseudo_robot(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    framework.create_embodiable_pseudo_robot(
        robot_id="robot_id",
        origin_object_id="origin_object_id",
        head_object_id="head_object_id",
    )
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                object_create_or_update_request=robotics_ui_pb2.ObjectCreateOrUpdateRequest(
                    object_id="robot_id",
                    robot_id="robot_id",
                    object_type=robotics_ui_pb2.ObjectType.ROBOT_PSEUDO_EMBODIABLE,
                    global_transform=client.make_identity(),
                    embodiable_robot_params=robotics_ui_pb2.EmbodiableRobotParams(
                        origin_object_id="origin_object_id",
                        head_object_id="head_object_id",
                    ),
                )
            ),
        )
    )

  def test_framework_add_alert(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    framework.add_alert(
        alert_id="alert_id",
        text="alert text",
        show=True,
    )
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                alert_create_request=robotics_ui_pb2.AlertCreateRequest(
                    alert_id="alert_id",
                    text="alert text",
                    show=True,
                )
            ),
        )
    )

  def test_framework_remove_alert(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    framework.remove_alert(
        alert_id="alert_id",
    )
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                alert_remove_request=robotics_ui_pb2.AlertRemoveRequest(
                    alert_id="alert_id",
                )
            ),
        )
    )

  def test_framework_clear_alerts(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    framework.clear_alerts()
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                alert_clear_request=robotics_ui_pb2.AlertClearRequest(),
            ),
        )
    )

  def test_framework_set_minimized(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    framework.set_minimized(
        element_id="element_id",
        minimized=True,
    )
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                set_minimized_request=robotics_ui_pb2.SetMinimizedRequest(
                    element_id="element_id",
                    minimized=True,
                ),
            ),
        )
    )

  def test_framework_create_toggle(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    framework.create_toggle(
        toggle_id="toggle_dialog",
        title="Toggle window",
        label="Check this box and press the submit button",
        msg="This is a test toggle dialog.",
        submit_label="Submit",
        spec=robotics_ui_pb2.UISpec(
            x=0.5,
            y=0.5,
            height=0.3,
            width=0.3,
            mode=robotics_ui_pb2.UIMODE_MODAL,
        ),
    )
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                toggle_create_request=robotics_ui_pb2.ToggleCreateRequest(
                    toggle_id="toggle_dialog",
                    title="Toggle window",
                    label="Check this box and press the submit button",
                    msg="This is a test toggle dialog.",
                    submit_label="Submit",
                    spec=robotics_ui_pb2.UISpec(
                        x=0.5,
                        y=0.5,
                        height=0.3,
                        width=0.3,
                        mode=robotics_ui_pb2.UIMODE_MODAL,
                    ),
                )
            ),
        )
    )

  def test_framework_callback_toggle_pressed(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                toggle_pressed_event=robotics_ui_pb2.TogglePressedEvent(
                    toggle_id="toggle_dialog",
                    selected=True,
                )
            )
        )
    )
    self._await_messages_processed(1.5)

    self.mock_callbacks.toggle_pressed.assert_called_once_with(
        "toggle_dialog", True
    )

  def test_framework_send_toggle_pressed_event(self):
    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()
    framework.send_toggle_pressed_event(
        toggle_id="toggle_dialog",
        selected=True,
    )
    self.mock_client.send_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                toggle_pressed_event=robotics_ui_pb2.TogglePressedEvent(
                    toggle_id="toggle_dialog",
                    selected=True,
                )
            ),
        )
    )

  def test_framework_block_on_toggle_pressed(self):
    unblocked = threading.Event()

    framework = client.Framework(
        callbacks=self.mock_callbacks, mock_clients=[self.mock_client]
    )
    framework.connect()

    def _block_on_toggle_pressed() -> None:
      response = framework.block_on_with_value(
          framework.create_toggle(toggle_id="toggle_id", label="label")
      )
      self.assertEqual(response, True)
      unblocked.set()

    thread = threading.Thread(target=_block_on_toggle_pressed, daemon=True)
    thread.start()
    self.assertTrue(
        framework.is_blocking_on.wait(5.0), "Framework never blocked"
    )
    self._queue_response(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                toggle_pressed_event=robotics_ui_pb2.TogglePressedEvent(
                    toggle_id="toggle_id",
                    selected=True,
                )
            )
        )
    )
    self.assertTrue(unblocked.wait(5.0), "Framework never unblocked")

    self.mock_callbacks.toggle_pressed.assert_not_called()

if __name__ == "__main__":
  absltest.main()
