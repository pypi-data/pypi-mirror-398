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

"""The public interface for the Framework object."""

import abc
import datetime
from typing import Callable

from safari_sdk.protos.ui import robot_frames_pb2
from safari_sdk.protos.ui import robot_state_pb2
from safari_sdk.protos.ui import robot_types_pb2
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui.client import _internal
from safari_sdk.ui.client import images
from safari_sdk.ui.client import types
from safari_sdk.ui.client import ui_callbacks


class IFramework(abc.ABC):
  """The public interface for the Framework object."""

  @abc.abstractmethod
  def get_callbacks(self) -> ui_callbacks.UiCallbacks:
    """Returns the callbacks for the Framework."""

  @abc.abstractmethod
  def connect(
      self,
      host: str = "localhost",
      port: int = 50011,
      block_until_connected: bool = True,
      connect_retry_interval_secs: float = 2,
  ) -> None:
    """Connects to the RoboticsUI.

    Args:
      host: The host of the RoboticsUI to connect to. Defaults to localhost.
      port: The port of the RoboticsUI to connect to. Defaults to 50011.
      block_until_connected: Blocks until connected. Otherwise, tries to connect
        in a background thread. The init_screen() callback is called upon
        connect in either case.
      connect_retry_interval_secs: The number of seconds between connect
        retries.
    """

  @abc.abstractmethod
  def shutdown(self) -> None:
    """Shuts down the Framework.

    Any connection to the RoboticsUI is shut down. The Framework is no longer
    usable. If you want to reconnect to the RoboticsUI, create a new Framework.
    """

  @abc.abstractmethod
  def is_shutdown(self) -> bool:
    """Returns whether the framework is shutdown."""

  @abc.abstractmethod
  def send_raw_message(self, msg: robotics_ui_pb2.RuiMessage) -> str:
    """Sends a raw message to the RoboticsUI.

    This is meant as an "escape hatch" for users who need to send messages that
    are not supported by the SDK.

    Args:
      msg: The message to send.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def add_resource_upload_listener(
      self, receiver: Callable[[types.ResourceLocator, bytes], None]
  ) -> None:
    """Adds a receiver for resource uploads.

    Args:
      receiver: The function to call when a resource is uploaded. The function
        should take two arguments: the resource locator and the hash of the
        resource data.
    """

  @abc.abstractmethod
  def remove_resource_upload_listener(
      self, receiver: Callable[[types.ResourceLocator, bytes], None]
  ) -> None:
    """Removes a receiver for resource uploads.

    Args:
      receiver: The receiver to remove.
    """

  @abc.abstractmethod
  def upload_file(self, path: types.PathLike) -> str:
    """Uploads a file resource to the RoboticsUI cache.

    The file data is sent to the RoboticsUI if the data hasn't been uploaded
    already.

    When the file is uploaded successfully (or determined to be already in the
    cache), the resource_uploaded callback is called with a file locator
    and the hash to be used to refer to the resource later.

    Args:
      path: The path (on the client's local disk) of the file to upload.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def upload_resource(self, locator: types.ResourceLocator) -> str:
    """Uploads a resource to the RoboticsUI cache.

    The resource data is sent to the RoboticsUI if the data hasn't been
    uploaded already. If the resource is not of scheme "file", then the data
    must be provided in the locator.

    When the resource is uploaded successfully (or determined to be already in
    the cache), the resource_uploaded callback is called with the original
    locator and the hash to be used to refer to the resource later.

    Args:
      locator: The locator of the resource to upload.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def upload_stl_file(self, path: types.PathLike) -> str:
    """Uploads an STL resource as mesh data to the RoboticsUI cache.

    When the file is uploaded successfully (or determined to be already in the
    cache), the resource_uploaded callback is called with the original locator
    and the hash to be used to refer to the mesh later.

    The hash is not the same as the hash of the file data. It is the hash of
    the extracted mesh data. Best practice is to treat the hash as an opaque
    identifier.

    Args:
      path: The path (on the client's local disk) of the STL file to upload.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def upload_zipped_kinematic_tree_robot(
      self,
      kinematic_tree_robot_id: str,
      zip_path: str,
      xml_path: str,
      timeout: datetime.timedelta,
  ) -> None:
    """Uploads a zipped kinematic tree robot into the RoboticsUI cache.

    The zip file must contain the Mujoco XML file, the joint mapping file, and
    the sites file. If the XML file points to STL files, then the STL files must
    also be in the zip file. An example zip file could have these files:

    * the_robot.xml
    * the_robot_joint_mapping.json
    * the_robot_sites.json
    * meshes/the_robot_part_1.stl
    * meshes/the_robot_part_2.stl
    * ...

    The joint mapping file in the zip file is a JSON dictionary where the keys
    are the names of the frames (from robot_frames.proto), and the values are
    lists of the joint names in that frame, in the order that they are sent in a
    RobotState message. The names are the same as the ones in the XML file.

    The name of the joint mapping file is the name of the XML file, but with
    the ".xml" suffix replaced with "_joint_mapping.json".

    The joint mapping file may just be an empty dictionary, but it must exist.

    The sites file in the zip file is a JSON dictionary where the keys are the
    names of the sites, and the values are the JSON version of a BodySiteSpec
    (i.e. body, pos, and rot), with pos being a list of [x, y, z] and rot being
    a list of [qw, qx, qy, qz] -- qw comes first to be consistent with Mujoco's
    XML quaternion format. The keys supported are "Origin Point" and
    "Embody Point".

    Example:

      {
        "Origin Point": {
          "body": "torso",
          "pos": [0.0, 0.0, 0.0],
          "rot": [1.0, 0.0, 0.0, 0.0]
        },
        "Embody Point": {
          "body": "head",
          "pos": [1.0, 0.0, 0.0],
          "rot": [1.0, 0.0, 0.0, 0.0]
        }
      }

    The name of the sites file is the name of the XML file, but with the ".xml"
    suffix replaced with "_sites.json".

    The sites file may just be an empty dictionary, but it must exist.

    We do not support password-protected zip files.

    Args:
      kinematic_tree_robot_id: The ID of the kinematic tree robot. This is used
        in a create_or_update_request to create or update a kinematic tree robot
        instance.
      zip_path: The path (on the client's local disk) of the zip file containing
        the Mujoco XML file and ancillary files.
      xml_path: The path (in the zip file) of the Mujoco XML file.
      timeout: The timeout for the background upload job.

    Raises:
      KinematicTreeRobotUploadError: If the zip file cannot be opened, or if the
        XML file is not present or cannot be parsed.
    """

  @abc.abstractmethod
  def upload_kinematic_tree_robot(
      self,
      kinematic_tree_robot_id: str,
      xml_path: str,
      joint_mapping: dict[robot_frames_pb2.Frame.Enum, list[str]],
      timeout: datetime.timedelta,
      origin_site: types.BodySiteSpec | None = None,
      embody_site: types.BodySiteSpec | None = None,
  ) -> None:
    """Uploads a Mujoco-based robot into the RoboticsUI cache.

    Args:
      kinematic_tree_robot_id: The ID of the kinematic tree robot. This is used
        in a create_or_update_request to create or update a kinematic tree robot
        instance.
      xml_path: The path (on the client's local disk) of the Mujoco XML file.
      joint_mapping: A mapping of robot parts to joint names in the kinematic
        tree. The joint names are in the order that they must appear in a
        JointState message.
      timeout: The timeout for the background upload job.
      origin_site: The origin site for the kinematic tree robot.
      embody_site: The embody site for the kinematic tree robot.
    """

  @abc.abstractmethod
  def send_robot_state(
      self, robot_state: robot_state_pb2.RobotState, robot_id: str | None = None
  ) -> str:
    """Sends a robot state message to the Robotics UI.

    If a 3D object of robot type has been previously created using the same
    client_id as the RobotState, or the same robot_id if that is specified,
    then the model will be moved on screen according to the robot_state.

    Args:
      robot_state: The RobotState to send.
      robot_id: Overrides the RobotState header's client_id field to identify
        the robot to the Robotics UI.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def block_on_with_value(
      self, callback_data: _internal.CallbackData
  ) -> _internal.CallbackReturnValue:
    """Blocks on a blockable GUI element.

    Args:
      callback_data: The return value of a blockable function.

    Returns:
      The value of the event resulting when the element is dismissed by the
      user.

    Raises:
      RoboticsUIConnectionError: If the RoboticsUI is shut down or not
        connected.
      BlockOnNotSupportedError: If calling block_on() while operating in
        synchronous mode.

    This will cause your script to wait until the element is dismissed on the
    Robotics UI by the user. Callbacks for other events will continue to be
    called while waiting.

    Blocking is not compatible with operating in synchronous mode.

    Note: block_on() and UIMODE_MODAL are orthogonal. UIMODE_MODAL means that
    on the RoboticsUI, the user will not be able to interact with anything on
    the screen other than the dialog. block_on() means that this script will
    wait until the user has interacted with the dialog.

    block_on() will not prevent other events from being received. These events
    will sill be handled by your callbacks. It's just that the event for
    this particular dialog will NOT be handled through your callback, but will
    cause block_on() to return the result instead.
    """

  @abc.abstractmethod
  def block_on(self, callback_data: _internal.CallbackData) -> str:
    """Blocks on a blockable GUI element, but only str return values are supported.

    Args:
      callback_data: The return value of a blockable function.

    Returns:
      The value of the event resulting when the element is dismissed by the
      user.

    Raises:
      TypeError: If the return value of the blockable function is not a string.

    See block_on_with_value() for more details.
    """

  @abc.abstractmethod
  def ask_user_yes_no(self, question: str) -> bool:
    """Asks the user a yes or no question, blocking.

    This is a convenience function for creating a blocking modal dialog,
    centered on the screen, with yes and no buttons, returning a bool.

    Args:
      question: The question to ask the user.

    Returns:
      True if the user pressed "Yes", False otherwise.
    """

  @abc.abstractmethod
  def create_button(
      self,
      button_id: str,
      x: float,
      y: float,
      w: float,
      h: float,
      label: str,
      font_size: int = 0,  # defaults to Unity value
      interactable: bool = True,
      background_color: robotics_ui_pb2.Color | None = None,
      shortcuts: list[str] | None = None,
      transform: robotics_ui_pb2.UITransform | None = None,
      hover_text: str | None = None,
  ) -> _internal.CallbackData:
    """Creates a nonmodal button.

    A nonmodal button remains on the screen until the button is pressed, then it
    disappears, and while the button is on screen, the user can interact with
    other elements.

    Shortcuts do not trigger their bound buttons when in modal dialogs or when
    a text input is focused. Binding a shortcut to multiple buttons leads to
    undefined behavior.

    Args:
      button_id: The research script name for the button.
      x: Horizontal position on the screen. Values from 0.0 to 1.0 are in screen
        width fraction, where 0.0 is the left side of the screen. Values greater
        than 1.0 are in pixels and converted to int.
      y: Vertical position on the screen. Values from 0.0 to 1.0 are in screen
        height fraction, where 0.0 is the top of the screen. Values greater than
        1.0 are in pixels and converted to int.
      w: The width of the button. Values from 0.0 to 1.0 are in screen width
        fraction, where 0.0 is the left side of the screen. Values greater than
        1.0 are in pixels and converted to int.
      h: The height of the button. Values from 0.0 to 1.0 are in screen height
        fraction, where 0.0 is the top of the screen. Values greater than 1.0
        are in pixels and converted to int.
      label: The text inside the button.
      font_size: The font size of the text inside the button.
      interactable: Whether the button is interactable.
      background_color: The background color of the button.
      shortcuts: Any keyboard shortcuts to bind to the button. See the
        ButtonCreateRequest proto for the specification.
      transform: The transform of the button when rendered in 3D space with
        UIMode.UIMODE_VR.
      hover_text: The text that appears when the user hovers over the button.

    Returns:
      The blockable data for use in block_on().

    This function is blockable.
    """

  @abc.abstractmethod
  def create_button_spec(
      self,
      button_id: str,
      label: str,
      spec: robotics_ui_pb2.UISpec | None = None,
      shortcuts: list[str] | None = None,
  ) -> _internal.CallbackData:
    """Creates a nonmodal button.

    A nonmodal button remains on the screen until the button is pressed, then it
    disappears, and while the button is on screen, the user can interact with
    other elements.

    Shortcuts do not trigger their bound buttons when in modal dialogs or when
    a text input is focused. Binding a shortcut to multiple buttons leads to
    undefined behavior.

    Args:
      button_id: The research script name for the button.
      label: The text inside the button.
      spec: The UISpec for the button.
      shortcuts: Any keyboard shortcuts to bind to the button. See the
        ButtonCreateRequest proto for the specification.

    Returns:
      The blockable data for use in block_on().

    This function is blockable.
    """

  @abc.abstractmethod
  def create_dialog(
      self,
      dialog_id: str,
      title: str,
      msg: str,
      buttons: list[str] | None = None,
      spec: robotics_ui_pb2.UISpec | None = None,
  ) -> _internal.CallbackData:
    """Creates a dialog.

    Args:
      dialog_id: The research script name for the dialog.
      title: The title of the dialog window.
      msg: The message that the dialog will display.
      buttons: The values of the buttons in the dialog. Defaults to Yes/No.
      spec: The UISpec for the dialog. Defaults to a modal dialog, width and
        height 0.2, centered.

    Returns:
      The blockable data for use in block_on().

    This function is blockable.
    """

  @abc.abstractmethod
  def create_prompt(
      self,
      prompt_id: str,
      title: str,
      msg: str,
      submit_label: str,
      spec: robotics_ui_pb2.UISpec | None = None,
      multiline_input: bool = False,
      initial_value: str | None = None,
      autofill_values: list[str] | None = None,
  ) -> _internal.CallbackData:
    """Creates a prompt.

    Args:
      prompt_id: The research script name for the prompt.
      title: The title of the prompt window.
      msg: The message that the ptompt will display.
      submit_label: The label of the submit button in the prompt.
      spec: The UISpec for the prompt.
      multiline_input: Whether the input field allows multi-line input.
      initial_value: The initial value of the input field.
      autofill_values: The values to autofill in the input field.

    Returns:
      The blockable data for use in block_on().

    This function is blockable.
    """

  @abc.abstractmethod
  def create_dropdown(
      self,
      dropdown_id: str,
      title: str,
      msg: str,
      choices: list[str],
      submit_label: str,
      spec: robotics_ui_pb2.UISpec | None = None,
      initial_value: str | None = None,
      multi_select: bool = False,
      initial_values: list[str] | None = None,
      shortcuts: dict[str, str] | None = None,
  ) -> _internal.CallbackData:
    """Creates a prompt.

    Args:
      dropdown_id: The research script name for the dropdown.
      title: The title of the dropdown window.
      msg: The message that the dropdown will display.
      choices: The items in the dropdown.
      submit_label: The label of the submit button in the dropdown.
      spec: The UISpec for the dropdown. Using a spec with mode UIMODE_MODAL or
        UIMODE_NONMODAL creates a window with a dropdown and submit button while
        UIMODE_PERSISTENT creates a dropdown that is outside of a window and
        always on-screen.
      initial_value: The initial value of the dropdown.
      multi_select: Whether the dropdown allows multiple choices to be selected.
        This is static and cannot be changed after creation.
      initial_values: If multi_select is true, the list of initial values
        selected in the dropdown.
      shortcuts: Keyboard shortcut bindings to choices in the dropdown. The key
        is the shortcut, and the value is the choice. Shortcuts trigger the
        bound choice to become selected. For multi-select dropdowns, the bound
        choice is added to the list of selected choices. See the
        DropdownCreateRequest proto for the specification.

    Returns:
      The blockable data for use in block_on().

    This function is blockable.
    """

  @abc.abstractmethod
  def create_login(
      self,
      prompt_id: str | None = None,
      prompt_title: str | None = None,
      prompt_msg: str | None = None,
      submit_label: str | None = None,
      prompt_spec: robotics_ui_pb2.UISpec | None = None,
      text_id: str | None = None,
      text_spec: robotics_ui_pb2.UISpec | None = None,
      button_id: str | None = None,
      button_label: str | None = None,
      button_spec: robotics_ui_pb2.UISpec | None = None,
  ) -> _internal.CallbackData:
    """Creates a series of UI elements for a login/logout cycle.

    Args:
      prompt_id: The id of the prompt window. Default is "login:prompt_userid".
      prompt_title: The title of the prompt window. Default is "Login".
      prompt_msg: The message in the prompt window. Default is "Enter user id:".
      submit_label: The text in the submit button in the prompt. Default is "Log
        in".
      prompt_spec: The UISpec for the prompt.
      text_id: The id of the text element. Default is "login:text_userid".
      text_spec: The UISpec for the text element.
      button_id: The id of the button element. Default is "login:button_logout".
      button_label: The text in the button. Default is "Log out".
      button_spec: The UISpec for the button.

    Returns:
      The blockable data for use in block_on().

    This function is blockable.
    """

  @abc.abstractmethod
  def get_gui_element_value(self, element_id: str) -> _internal.CallbackData:
    """Sends a request to get the value of a GUI element.

    Args:
      element_id: The id of the GUI element to get the value of.

    Returns:
      The blockable data for use in block_on().

    This function is blockable.
    """

  @abc.abstractmethod
  def make_camera_window(
      self,
      sensor_id: int,
      title: str,
      spec: robotics_ui_pb2.UISpec,
      window_id: str | None = None,
  ) -> str:
    """Creates a camera window.

    Images sent in a robot state with the same sensor_id will be placed in this
    window.

    Args:
      sensor_id: The sensor id of the camera window.
      title: The title of the camera window.
      spec: The UISpec for the camera window.
      window_id: The research script name for the window. If not given, the
        window ID will be "image_window_{sensor_id}". This is the ID that can be
        used in remove_element().

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def make_stereo_image_quad(
      self,
      object_id: str,
      left_sensor_id: int,
      right_sensor_id: int,
      transform: robotics_ui_pb2.UITransform | None = None,
      transform_type: types.TransformType = types.TransformType.GLOBAL,
      parent_id: str | None = None,
      params: dict[str, str] | None = None,
      robot_id: str | robot_types_pb2.ClientID | None = None,
  ) -> str:
    """Creates a stereo image quad."""

  @abc.abstractmethod
  def display_splash_screen(
      self,
      jpeg_image: bytes,
      cols: int = 0,
      rows: int = 0,
      timeout_seconds: float = 5.0,
      spec: robotics_ui_pb2.UISpec | None = None,
  ) -> str:
    """Displays a splash screen.

    Args:
      jpeg_image: The JPEG-encoded data.
      cols: The width of the image in pixels. If not given, the image will be
        decoded and its size will be determined for you.
      rows: The height of the image in pixels. If not given, the image will be
        decoded and its size will be determined for you.
      timeout_seconds: The number of seconds the splash screen will be visible
        for. After this, the splash screen goes away.
      spec: Optionally specifies the position and size of the splash screen. The
        default will center the image on the screen, and take up no more than
        half the screen in any dimension. The mode in the spec is ignored.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def create_or_update_object(
      self,
      object_id: str,
      object_type: robotics_ui_pb2.ObjectType,
      transform: robotics_ui_pb2.UITransform | None = None,
      transform_type: types.TransformType = types.TransformType.GLOBAL,
      parent_id: str | None = None,
      params: dict[str, str] | None = None,
      robot_id: str | robot_types_pb2.ClientID | None = None,
      stereoscopic_image_sensors: (
          robotics_ui_pb2.StereoscopicImageSensors | None
      ) = None,
      manus_gloves_params: robotics_ui_pb2.ManusGlovesParams | None = None,
      vr_controller_params: robotics_ui_pb2.VRControllerParams | None = None,
      uploaded_object_params: (
          robotics_ui_pb2.UploadedObjectParams | None
      ) = None,
      material_specs: list[robotics_ui_pb2.MaterialSpec] | None = None,
      kinematic_tree_robot_params: (
          robotics_ui_pb2.KinematicTreeRobotParams | None
      ) = None,
      embodiable_robot_params: (
          robotics_ui_pb2.EmbodiableRobotParams | None
      ) = None,
  ) -> str:
    """Creates or updates an object.

    Note params: We prefer that you don't specify this field yourself, as any
    typo will result in unexpected behavior. Instead, use roboticsui's
    specific functions which have the keys as parameters.

    Args:
      object_id: The research script name for the object.
      object_type: The type of object.
      transform: The global or local transform of the object.
      transform_type: Whether the transform is global or local.
      parent_id: The optional parent to set on the object.
      params: Any parameters the object might take.
      robot_id: The id of an endpoint which Xemb messages to process/generate
      stereoscopic_image_sensors: The left and right sensor IDs for a stereo
        image quad. Only applicable if object_type is STEREO_IMAGE_QUAD.
      manus_gloves_params: Parameters for Manus glove inputs. Only applicable if
        object_type is INPUT_MANUS_GLOVES.
      vr_controller_params: Parameters for VR controller inputs. Only applicable
        if object_type is INPUT_VR_CONTROLLER.
      uploaded_object_params: Parameters for uploaded objects. Only applicable
        if object_type is UPLOADED_OBJECT.
      material_specs: Material specs for the object or object parts.
      kinematic_tree_robot_params: Parameters for kinematic tree robots. Only
        applicable if object_type is ROBOT_KINEMATIC_TREE.
      embodiable_robot_params: Parameters for embodiable robots. Only applicable
        if object_type is ROBOT_PSEUDO_EMBODIABLE.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def create_or_update_uploaded_object(
      self,
      object_id: str,
      object_hash: bytes,
      mime_type: str,
      transform: robotics_ui_pb2.UITransform | None = None,
      transform_type: types.TransformType = types.TransformType.GLOBAL,
      parent_id: str | None = None,
  ) -> str:
    """Creates or updates an uploaded object.

    Args:
      object_id: The name for the instance of the object.
      object_hash: The hash of the file that was uploaded.
      mime_type: The MIME type of the file.
      transform: The global or local transform of the object.
      transform_type: Whether the transform is global or local.
      parent_id: The optional parent to set on the object.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def clear_objects(self, prefix: str | None = None) -> str:
    """Clears 3D objects in the prefix (or all if prefix is empty)."""

  @abc.abstractmethod
  def clear_gui(self, prefix: str | None = None) -> str:
    """Clears GUI objects/dialogs in the prefix (or all if prefix is empty)."""

  @abc.abstractmethod
  def clear_all(self, prefix: str | None = None) -> None:
    """Clears 3D objects and GUI objects/dialogs in the prefix."""

  @abc.abstractmethod
  def reparent_object(self, object_id: str, parent_id: str) -> str:
    """Reparents a 3D object.

    Args:
      object_id: The ID of the object to reparent.
      parent_id: The ID of the object to parent to.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def get_last_ping_latency_nsec(self) -> int:
    """Gets the last ping latency in nanoseconds.

    Returns:
      The last ping latency in nanoseconds.

    If a ping reply hasn't been received in the last 10 seconds, the ping
    latency will be 999999999999.
    """

  @abc.abstractmethod
  def set_image_rate_throttling(self, rate_hz: float) -> None:
    """Sets the rate beyond which images will be dropped.

    Set to zero to disable throttling.

    This only applies to images sent via send_jpeg_image or send_jpeg_images.
    Images send in send_robot_state are never throttled.

    Args:
      rate_hz: The maximum image rate.

    Returns:
      Nothing.
    """

  @abc.abstractmethod
  def send_jpeg_image(
      self,
      camera_index: int,
      jpeg_image: bytes,
      cols: int = 0,
      rows: int = 0,
      sample_timestamp_nsec: int = 0,
      seq: int = 0,
      sensor_id: int | None = None,
      publish_timestamp_nsec: int = 0,
      client_id: robot_types_pb2.ClientID | None = None,
  ) -> str:
    """Sends a JPEG-encoded image.

    If image rate throttling is set, this image may get dropped.

    Args:
      camera_index: The index number of the camera generating the image in a
        fixed list of cameras.
      jpeg_image: The JPEG-encoded data.
      cols: The width of the image in pixels. If not given, the RoboticsUI will
        decode the image and determine its size.
      rows: The height of the image in pixels. If not given, the RoboticsUI will
        decode the image and determine its size.
      sample_timestamp_nsec: The time the image was sampled. See the
        MessageHeader.sample_timestamp_nsec field in robot_types.proto for more
        details. This will also be set as the image's sample time. Defaults to
        now.
      seq: The sequence number of the image. See the
        SensorHeader.sequence_number field in robot_types.proto for details.
        Defaults to 0.
      sensor_id: Identifier for which camera sensor this is. See the
        SensorHeader.sensor_id field in robot_types.proto for details. Defaults
        to camera_index.
      publish_timestamp_nsec: The time the image was published by the robot. See
        the MessageHeader.publish_timestamp_nsec field in robot_types.proto for
        more details. Defaults to 0.
      client_id: The 128-bit client ID. See the MessageHeader.client_id field in
        robot_types.proto for more details. Defaults to 0.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def send_jpeg_images(
      self,
      jpeg_camera_image_data: list[images.JpegCameraImageData | None],
      publish_timestamp_nsec: int = 0,
      client_id: robot_types_pb2.ClientID | None = None,
  ) -> str:
    """Sends a list of JPEG-encoded images.

    This sends all the images in jpeg_camera_image_data in a single RobotState
    message. The camera_index in each camera image in the world's PartState will
    be the same as the index in the list. Entries that are None will be filled
    in with an empty CameraImage message -- not an empty image!

    If image rate throttling is set, these images may get dropped.

    Args:
      jpeg_camera_image_data: The list of images to send.
      publish_timestamp_nsec: The time the image was published by the robot. See
        the MessageHeader.publish_timestamp_nsec field in robot_types.proto for
        more details. Defaults to 0.
      client_id: The 128-bit client ID. See the MessageHeader.client_id field in
        robot_types.proto for more details. Defaults to 0.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def create_or_update_text(
      self,
      text_id: str,
      text: str,
      spec: robotics_ui_pb2.UISpec | None = None,
      scrollable: bool = False,
  ) -> str:
    """Creates or updates a text box.

    You may use TextMeshPro Rich Text tags in the text to change size, color,
    justification, alignment, font, and so on. See
    http://digitalnativestudios.com/textmeshpro/docs/rich-text/ for a list of
    supported tags and examples of how to use them.

    Args:
      text_id: The ID of the GUI element, for later reference.
      text: The text to set the element to.
      spec: The UISpec for the element.
      scrollable: If the text becomes scrollable if it doesn't fit in its
        bounding box instead of sizing down.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def remove_element(self, element_id: str) -> str:
    """Removes a GUI element.

    Args:
      element_id: The ID of the GUI element to remove.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def create_chat(
      self,
      chat_id: str,
      title: str,
      submit_label: str | None = None,
      spec: robotics_ui_pb2.UISpec | None = None,
  ) -> str:
    """Creates a chat window.

    Args:
      chat_id: The ID of the chat window.
      title: The title of the chat window.
      submit_label: The label of the submit button in the chat window.
      spec: The UISpec for the chat window.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def add_chat_line(self, chat_id: str, text: str) -> str:
    """Adds a line to a chat window.

    Args:
      chat_id: The ID of the chat window to add the line to.
      text: The text to add.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def setup_header(
      self,
      height: float,
      visible: bool,
      collapsible: bool,
      expandable: bool,
      screen_scaling: bool = False,
  ) -> str:
    """Sets up the header state in the UI.

    Args:
      height: The height of the header.
      visible: Whether the header is visible.
      collapsible: Whether the header is collapsible.
      expandable: Whether the header is expandable.
      screen_scaling: Whether the header scales with the screen.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def create_toggle(
      self,
      toggle_id: str,
      label: str,
      msg: str | None = None,
      title: str | None = None,
      submit_label: str | None = None,
      initial_value: bool | None = None,
      spec: robotics_ui_pb2.UISpec | None = None,
  ) -> _internal.CallbackData:
    """Creates a toggle.

    Args:
      toggle_id: The ID of the toggle.
      label: The label of the toggle.
      msg: The message of the toggle.
      title: The title of the toggle.
      submit_label: The label of the submit button in the toggle.
      initial_value: The initial value of the toggle.
      spec: The UISpec for the toggle.

    Returns:
      The blockable data for use in block_on().
    """

  @abc.abstractmethod
  def send_button_pressed_event(self, button_id: str) -> str:
    """Sends a button pressed event.

    Args:
      button_id: The ID of the button that was pressed.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def send_prompt_pressed_event(self, prompt_id: str, text_input: str) -> str:
    """Sends a prompt pressed event with text input.

    Args:
      prompt_id: The ID of the prompt that was pressed.
      text_input: The text input.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def send_dialog_pressed_event(self, dialog_id: str, choice: str) -> str:
    """Sends a dialog pressed event with button choice.

    Args:
      dialog_id: The ID of the dialog that was pressed.
      choice: The button choice.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def send_dropdown_pressed_event(
      self, dropdown_id: str, choice: str | list[str]
  ) -> str:
    """Sends a dropdown pressed event with dropdown value.

    Args:
      dropdown_id: The ID of the dropdown that was pressed.
      choice: The dropdown choice. If multi-select, this can be a list of
        choices. Otherwise, it will be a single choice.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def send_toggle_pressed_event(
      self, toggle_id: str, selected: bool
  ) -> str:
    """Sends a toggle pressed event.

    Args:
      toggle_id: The ID of the toggle that was pressed.
      selected: The selected state of the toggle.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def embody(self, robot_id: str) -> str:
    """Embodies the robot."""

  @abc.abstractmethod
  def create_embodiable_pseudo_robot(
      self, robot_id: str, origin_object_id: str, head_object_id: str
  ) -> str:
    """Creates a psuedo robot for embodiment into.

    Args:
      robot_id: The ID of the robot.
      origin_object_id: The ID of the origin object.
      head_object_id: The ID of the head object.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def send_console_command(self, command: str) -> str:
    """Sends a command to be executed in the UI console.

    Args:
      command: The command to send.

    Returns:
      The message ID of the sent message.
    """

  @abc.abstractmethod
  def create_form(
      self,
      form_id: str,
      title: str,
      submit_label: str | None,
      spec: robotics_ui_pb2.UISpec | None,
      create_requests: list[robotics_ui_pb2.RuiMessage],
  ) -> _internal.CallbackData:
    """Creates a custom form dialog with the given list of requests.

    Args:
      form_id: The ID of the form.
      title: The title of the form.
      submit_label: The label of the submit button in the form.
      spec: The UISpec of the form.
      create_requests: The create requests for the form.

    Returns:
      The blockable data for use in block_on().

    This function is blockable.
    """

  @abc.abstractmethod
  def create_button_message(
      self,
      button_id: str,
      label: str,
      shortcuts: list[str] | None,
      spec: robotics_ui_pb2.UISpec | None = None,
  ) -> robotics_ui_pb2.RuiMessage:
    """Packages a ButtonCreateRequest into a RuiMessage message.

    Args:
      button_id: The research script name for the button.
      label: The text inside the button.
      shortcuts: Any keyboard shortcuts to bind to the button. See the
        ButtonCreateRequest proto for the specification.
      spec: The UISpec for the button.

    Returns:
      A RuiMessage containing a ButtonCreateRequest.
    """

  @abc.abstractmethod
  def create_prompt_message(
      self,
      prompt_id: str,
      title: str,
      msg: str,
      submit_label: str,
      spec: robotics_ui_pb2.UISpec | None = None,
      multiline_input: bool = False,
      initial_value: str | None = None,
      autofill_values: list[str] | None = None,
  ) -> robotics_ui_pb2.RuiMessage:
    """Packages a PromptCreateRequest into a RuiMessage message.

    Args:
      prompt_id: The research script name for the prompt.
      title: The title of the prompt.
      msg: The message inside the prompt.
      submit_label: The label of the submit button in the prompt.
      spec: The UISpec for the prompt.
      multiline_input: Whether the prompt allows multiline input.
      initial_value: The initial value of the prompt.
      autofill_values: The autofill values of the prompt.

    Returns:
      A RuiMessage containing a PromptCreateRequest.
    """

  @abc.abstractmethod
  def create_dropdown_message(
      self,
      dropdown_id: str,
      title: str,
      msg: str,
      choices: list[str],
      submit_label: str,
      spec: robotics_ui_pb2.UISpec | None = None,
      initial_value: str | None = None,
      multi_select: bool = False,
      initial_values: list[str] | None = None,
      shortcuts: dict[str, str] | None = None,
  ) -> robotics_ui_pb2.RuiMessage:
    """Packages a DropdownCreateRequest into a RuiMessage message.

    Args:
      dropdown_id: The research script name for the dropdown.
      title: The title of the dropdown.
      msg: The message inside the dropdown.
      choices: The choices in the dropdown.
      submit_label: The label of the submit button in the dropdown.
      spec: The UISpec for the dropdown.
      initial_value: The initial value of the dropdown.
      multi_select: Whether the dropdown allows multiple choices to be selected.
        This is static and cannot be changed after creation.
      initial_values: If multi_select is true, the list of initial values
        selected in the dropdown.
      shortcuts: Keyboard shortcut bindings to choices in the dropdown. The key
        is the shortcut, and the value is the choice. Shortcuts trigger the
        bound choice to become selected. For multi-select dropdowns, the bound
        choice is added to the list of selected choices. See the
        DropdownCreateRequest proto for the specification.

    Returns:
      A RuiMessage containing a DropdownCreateRequest.
    """

  @abc.abstractmethod
  def create_text_message(
      self,
      text_id: str,
      text: str,
      spec: robotics_ui_pb2.UISpec | None = None,
      scrollable: bool = False,
  ) -> robotics_ui_pb2.RuiMessage:
    """Packages a TextCreateOrUpdateRequest into a RuiMessage message.

    Args:
      text_id: The research script name for the text.
      text: The text to display.
      spec: The UISpec for the text.
      scrollable: Whether the text is scrollable.

    Returns:
      A RuiMessage containing a TextCreateOrUpdateRequest.
    """

  @abc.abstractmethod
  def create_row_message(
      self,
      create_requests: list[robotics_ui_pb2.RuiMessage],
      spec: robotics_ui_pb2.UISpec | None = None,
  ) -> robotics_ui_pb2.RuiMessage:
    """Packages a RowCreateRequest into a RuiMessage message.

    This function is used to create a row of GUI elements. It takes a list of
    create requests and fits each element to the size of the row defined by the
    row spec. The mode of each element in the row is UIMODE_PERSISTENT.

    Args:
      create_requests: The create requests for the row.
      spec: The UISpec for the row.

    Returns:
      A RuiMessage containing a RowCreateRequest.
    """

  @abc.abstractmethod
  def create_toggle_message(
      self,
      toggle_id: str,
      label: str,
      msg: str | None = None,
      title: str | None = None,
      submit_label: str | None = None,
      initial_value: bool | None = None,
      spec: robotics_ui_pb2.UISpec | None = None,
  ) -> robotics_ui_pb2.RuiMessage:
    """Packages a ToggleCreateRequest into a RuiMessage message.

    Args:
      toggle_id: The research script name for the toggle.
      label: The label of the toggle.
      msg: The message of the toggle.
      title: The title of the toggle.
      submit_label: The label of the submit button in the toggle.
      initial_value: The initial value of the toggle.
      spec: The UISpec for the toggle.

    Returns:
      A RuiMessage containing a ToggleCreateRequest.
    """

  @abc.abstractmethod
  def add_alert(self, alert_id: str, text: str, show: bool) -> str:
    """Adds an alert to the UI.

    Args:
      alert_id: The ID of the alert.
      text: The text of the alert.
      show: Whether to show an alert notification.
    """

  @abc.abstractmethod
  def remove_alert(self, alert_id: str) -> str:
    """Removes an alert from the UI.

    Args:
      alert_id: The ID of the alert to remove.
    """

  @abc.abstractmethod
  def clear_alerts(self) -> str:
    """Removes all alerts from the UI."""

  @abc.abstractmethod
  def set_minimized(self, element_id: str, minimized: bool) -> None:
    """Sets the minimized state of an element.

    Args:
      element_id: The ID of the element to set minimized.
      minimized: Whether to minimize the element.
    """
