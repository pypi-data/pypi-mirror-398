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

"""The public API for Robotics UI."""

from safari_sdk.ui.client import exceptions
from safari_sdk.ui.client import framework
from safari_sdk.ui.client import functions
from safari_sdk.ui.client import iframework
from safari_sdk.ui.client import images
from safari_sdk.ui.client import kinematic_tree_robot
from safari_sdk.ui.client import server
from safari_sdk.ui.client import synchronous_framework
from safari_sdk.ui.client import types
from safari_sdk.ui.client import ui_callbacks

# Class aliases into individual files.

JpegCameraImageData = images.JpegCameraImageData
IFramework = iframework.IFramework
Framework = framework.Framework
TcpServer = server.TcpServer
SynchronousFramework = synchronous_framework.SynchronousFramework
UiCallbacks = ui_callbacks.UiCallbacks
TransformType = types.TransformType
BodySiteSpec = types.BodySiteSpec
PathLike = types.PathLike
ResourceLocator = types.ResourceLocator
ResourceLocatorKey = types.ResourceLocatorKey
KinematicTree = kinematic_tree_robot.KinematicTree

BlockOnNotSupportedError = exceptions.BlockOnNotSupportedError
RoboticsUIConnectionError = exceptions.RoboticsUIConnectionError
FileUploadError = exceptions.FileUploadError
KinematicTreeRobotUploadError = exceptions.KinematicTreeRobotUploadError
StlParseError = exceptions.StlParseError

# Function aliases into individual files.

add_joint_state_to_raw_joints = functions.add_joint_state_to_raw_joints
apply_local_pose = functions.apply_local_pose
get_relative_pose = functions.get_relative_pose
invert_quaternion = functions.invert_quaternion
make_euler_from_quaternion = functions.make_euler_from_quaternion
multiply_vector_by_quaternion = functions.multiply_vector_by_quaternion
make_identity = functions.make_identity
make_identity_quaternion = functions.make_identity_quaternion
make_position = functions.make_position
make_quaternion = functions.make_quaternion
make_quaternion_from_euler = functions.make_quaternion_from_euler
make_scale = functions.make_scale
make_transform = functions.make_transform
make_transform_matrix = functions.make_transform_matrix
multiply_quaternions = functions.multiply_quaternions
positions_approximately_equal = functions.positions_approximately_equal
quaternion_to_axis_angle = functions.quaternion_to_axis_angle
quaternion_xyzw_to_axis_angle = functions.quaternion_xyzw_to_axis_angle
quaternions_approximately_equal = functions.quaternions_approximately_equal
get_position_from_transform = functions.get_position_from_transform
get_rotation_from_transform = functions.get_rotation_from_transform

# Mime types.

MIME_TYPE_WTF = types.MIME_TYPE_WTF
