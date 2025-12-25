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

"""Unit tests for functions."""

import math

import numpy as np
import numpy.testing as nptest

from absl.testing import absltest
from absl.testing import parameterized
from safari_sdk.protos.ui import robot_state_pb2
from safari_sdk.protos.ui import robot_types_pb2
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui import client


class FunctionsTest(parameterized.TestCase):

  def test_make_quaternion_from_euler_zero_angles(self):
    quaternion = client.make_quaternion_from_euler(0, 0, 0)
    self.assertEqual(
        quaternion, robot_types_pb2.Quaternion(qx=0, qy=0, qz=0, qw=1)
    )

  def test_make_quaternion_from_euler_non_zero_angles(self):
    quaternion = client.make_quaternion_from_euler(30, 45, 60)
    nptest.assert_almost_equal(quaternion.qx, 0.02226, 6)
    nptest.assert_almost_equal(quaternion.qy, 0.4396797, 6)
    nptest.assert_almost_equal(quaternion.qz, 0.3604234, 6)
    nptest.assert_almost_equal(quaternion.qw, 0.8223632, 6)

  def test_make_quaternion_from_euler_non_zero_smaller_angles(self):
    quaternion = client.make_quaternion_from_euler(10, 20, 30)
    nptest.assert_almost_equal(quaternion.qx, 0.0381346, 6)
    nptest.assert_almost_equal(quaternion.qy, 0.1893079, 6)
    nptest.assert_almost_equal(quaternion.qz, 0.2392983, 6)
    nptest.assert_almost_equal(quaternion.qw, 0.9515485, 6)

  @parameterized.named_parameters(
      dict(
          testcase_name="identity",
          pos=client.make_position(0, 0, 0),
          rot=client.make_identity_quaternion(),
          expected=np.identity(4),
      ),
      dict(
          testcase_name="identity_rot_with_pos",
          pos=client.make_position(1, 2, 3),
          rot=client.make_identity_quaternion(),
          expected=np.array(
              [[1, 0, 0, 1], [0, 1, 0, 2], [0, 0, 1, 3], [0, 0, 0, 1]]
          ),
      ),
      dict(
          testcase_name="rot_with_pos",
          pos=client.make_position(1, 2, 3),
          rot=client.make_quaternion_from_euler(30, 45, 60),
          expected=np.array([
              [0.3535534, -0.5732233, 0.7391989, 1],
              [0.6123725, 0.7391989, 0.2803301, 2],
              [-0.7071068, 0.3535534, 0.6123725, 3],
              [0, 0, 0, 1],
          ]),
      ),
  )
  def test_make_transform_matrix(self, pos, rot, expected):
    got = client.make_transform_matrix(pos=pos, rot=rot)
    nptest.assert_almost_equal(expected, got, 5)

  def test_make_position(self):
    position = client.make_position(1.1, 2.2, 3.3)
    self.assertEqual(position, robot_types_pb2.Position(px=1.1, py=2.2, pz=3.3))

  def test_make_scale(self):
    scale = client.make_scale(1.1, 2.2, 3.3)
    self.assertEqual(scale, robot_types_pb2.Position(px=1.1, py=2.2, pz=3.3))

  def test_make_transform(self):
    position = client.make_position(1.1, 2.2, 3.3)
    scale = client.make_scale(4.4, 5.5, 6.6)
    quaternion = client.make_quaternion_from_euler(0, 0, 0)
    transform = client.make_transform(position, quaternion, scale)
    self.assertEqual(
        transform,
        robotics_ui_pb2.UITransform(
            position=robot_types_pb2.Position(px=1.1, py=2.2, pz=3.3),
            scale=robot_types_pb2.Position(px=4.4, py=5.5, pz=6.6),
            rotation=robot_types_pb2.Quaternion(qx=0, qy=0, qz=0, qw=1),
        ),
    )

  @parameterized.named_parameters(
      dict(
          testcase_name="zero",
          x=0,
          y=0,
          z=0,
          w=0,
          expected_axis=(1, 0, 0),
          expected_angle=0,
      ),
      dict(
          testcase_name="identity",
          x=0,
          y=0,
          z=0,
          w=1,
          expected_axis=(1, 0, 0),
          expected_angle=0,
      ),
      dict(
          testcase_name="x180",
          x=1,
          y=0,
          z=0,
          w=0,
          expected_axis=(1, 0, 0),
          expected_angle=math.pi,
      ),
      dict(
          testcase_name="y90",
          x=0,
          y=math.sqrt(2) / 2,
          z=0,
          w=math.sqrt(2) / 2,
          expected_axis=(0, 1, 0),
          expected_angle=math.pi / 2,
      ),
      dict(
          testcase_name="z90",
          x=0,
          y=0,
          z=math.sqrt(2) / 2,
          w=math.sqrt(2) / 2,
          expected_axis=(0, 0, 1),
          expected_angle=math.pi / 2,
      ),
      dict(
          testcase_name="z-90",
          x=0,
          y=0,
          z=-math.sqrt(2) / 2,
          w=math.sqrt(2) / 2,
          expected_axis=(0, 0, -1),
          expected_angle=math.pi / 2,
      ),
  )
  def test_quaternion_xyzw_to_axis_angle(
      self,
      x: float,
      y: float,
      z: float,
      w: float,
      expected_axis: tuple[float, float, float],
      expected_angle: float,
  ):
    axis, angle = client.quaternion_xyzw_to_axis_angle(x, y, z, w)
    nptest.assert_almost_equal(axis, expected_axis, 5)
    nptest.assert_almost_equal(angle, expected_angle, 5)

  def test_invert_quaternion(self):
    e = 1.0 / math.sqrt(30)  # Makes a nice unit quaternion.
    quaternion = client.make_quaternion(qx=e, qy=2 * e, qz=3 * e, qw=4 * e)
    inverted = client.invert_quaternion(quaternion)
    nptest.assert_almost_equal(
        [inverted.qx, inverted.qy, inverted.qz, inverted.qw],
        [-e, -2 * e, -3 * e, 4 * e],
        5,
    )

  @parameterized.named_parameters(
      dict(
          testcase_name="zero",
          origin_pos=client.make_position(0, 0, 0),
          origin_rot=client.make_identity_quaternion(),
          translate=client.make_position(0, 0, 0),
          rotate=client.make_identity_quaternion(),
          expected_pos=client.make_position(0, 0, 0),
          expected_rot=client.make_identity_quaternion(),
      ),
      dict(
          testcase_name="zero_to_pos_only",
          origin_pos=client.make_position(0, 0, 0),
          origin_rot=client.make_identity_quaternion(),
          translate=client.make_position(1, 2, 3),
          rotate=client.make_identity_quaternion(),
          expected_pos=client.make_position(1, 2, 3),
          expected_rot=client.make_identity_quaternion(),
      ),
      dict(
          testcase_name="zero_to_rot_only",
          origin_pos=client.make_position(0, 0, 0),
          origin_rot=client.make_identity_quaternion(),
          translate=client.make_position(0, 0, 0),
          rotate=client.make_quaternion_from_euler(30, 45, 60),
          expected_pos=client.make_position(0, 0, 0),
          expected_rot=client.make_quaternion_from_euler(30, 45, 60),
      ),
      dict(
          testcase_name="zero_to_pos_and_rot",
          origin_pos=client.make_position(0, 0, 0),
          origin_rot=client.make_identity_quaternion(),
          translate=client.make_position(1, 2, 3),
          rotate=client.make_quaternion_from_euler(30, 45, 60),
          expected_pos=client.make_position(1, 2, 3),
          expected_rot=client.make_quaternion_from_euler(30, 45, 60),
      ),
      dict(
          testcase_name="pos_to_pos_only",
          origin_pos=client.make_position(1, 2, 3),
          origin_rot=client.make_identity_quaternion(),
          translate=client.make_position(4, 5, 6),
          rotate=client.make_identity_quaternion(),
          expected_pos=client.make_position(5, 7, 9),
          expected_rot=client.make_identity_quaternion(),
      ),
      dict(
          testcase_name="pos_to_rot_only",
          origin_pos=client.make_position(1, 2, 3),
          origin_rot=client.make_identity_quaternion(),
          translate=client.make_position(0, 0, 0),
          rotate=client.make_quaternion_from_euler(30, 45, 60),
          expected_pos=client.make_position(1, 2, 3),
          expected_rot=client.make_quaternion_from_euler(30, 45, 60),
      ),
      dict(
          testcase_name="pos_to_pos_and_rot",
          origin_pos=client.make_position(1, 2, 3),
          origin_rot=client.make_identity_quaternion(),
          translate=client.make_position(4, 5, 6),
          rotate=client.make_quaternion_from_euler(30, 45, 60),
          expected_pos=client.make_position(5, 7, 9),
          expected_rot=client.make_quaternion_from_euler(30, 45, 60),
      ),
      dict(
          testcase_name="rot_to_pos_only",
          origin_pos=client.make_position(0, 0, 0),
          origin_rot=client.make_quaternion_from_euler(30, 45, 60),
          translate=client.make_position(1, 2, 3),
          rotate=client.make_identity_quaternion(),
          expected_pos=client.make_position(1.4247, 2.93176, 1.83712),
          expected_rot=client.make_quaternion_from_euler(30, 45, 60),
      ),
      dict(
          testcase_name="rot_to_rot_only",
          origin_pos=client.make_position(0, 0, 0),
          origin_rot=client.make_quaternion_from_euler(30, 45, 60),
          translate=client.make_position(0, 0, 0),
          rotate=client.make_quaternion_from_euler(30, 45, 60),
          expected_pos=client.make_position(0, 0, 0),
          expected_rot=client.make_quaternion_from_euler(
              93.148, 27.808, 147.83
          ),
      ),
      dict(
          testcase_name="rot_to_pos_and_rot",
          origin_pos=client.make_position(0, 0, 0),
          origin_rot=client.make_quaternion_from_euler(30, 45, 60),
          translate=client.make_position(1, 2, 3),
          rotate=client.make_quaternion_from_euler(30, 45, 60),
          expected_pos=client.make_position(1.4247, 2.93176, 1.83712),
          expected_rot=client.make_quaternion_from_euler(
              93.148, 27.808, 147.83
          ),
      ),
      dict(
          testcase_name="pos_and_rot_to_pos_and_rot",
          origin_pos=client.make_position(1, 2, 3),
          origin_rot=client.make_quaternion_from_euler(30, 45, 60),
          translate=client.make_position(4, 5, 6),
          rotate=client.make_quaternion_from_euler(30, 45, 60),
          expected_pos=client.make_position(3.98329, 9.82747, 5.61357),
          expected_rot=client.make_quaternion_from_euler(
              93.148, 27.808, 147.83
          ),
      ),
  )
  def test_apply_local_pose(
      self,
      origin_pos: robot_types_pb2.Position,
      origin_rot: robot_types_pb2.Quaternion,
      translate: robot_types_pb2.Position,
      rotate: robot_types_pb2.Quaternion,
      expected_pos: robot_types_pb2.Position,
      expected_rot: robot_types_pb2.Quaternion,
  ):
    got_pos, got_rot = client.apply_local_pose(
        origin_pos, origin_rot, translate, rotate
    )
    nptest.assert_almost_equal(
        [got_pos.px, got_pos.py, got_pos.pz],
        [expected_pos.px, expected_pos.py, expected_pos.pz],
        5,
    )
    nptest.assert_almost_equal(
        [got_rot.qx, got_rot.qy, got_rot.qz, got_rot.qw],
        [expected_rot.qx, expected_rot.qy, expected_rot.qz, expected_rot.qw],
        5,
    )

  @parameterized.named_parameters(
      dict(
          testcase_name="zero",
          origin_pos=client.make_position(0, 0, 0),
          origin_rot=client.make_identity_quaternion(),
          obj_pos=client.make_position(0, 0, 0),
          obj_rot=client.make_identity_quaternion(),
          expected_pos=client.make_position(0, 0, 0),
          expected_rot=client.make_identity_quaternion(),
      ),
      dict(
          testcase_name="zero_to_pos_only",
          origin_pos=client.make_position(0, 0, 0),
          origin_rot=client.make_identity_quaternion(),
          obj_pos=client.make_position(1, 2, 3),
          obj_rot=client.make_identity_quaternion(),
          expected_pos=client.make_position(1, 2, 3),
          expected_rot=client.make_identity_quaternion(),
      ),
      dict(
          testcase_name="zero_to_rot_only",
          origin_pos=client.make_position(0, 0, 0),
          origin_rot=client.make_identity_quaternion(),
          obj_pos=client.make_position(0, 0, 0),
          obj_rot=client.make_quaternion_from_euler(30, 45, 60),
          expected_pos=client.make_position(0, 0, 0),
          expected_rot=client.make_quaternion_from_euler(30, 45, 60),
      ),
      dict(
          testcase_name="zero_to_pos_and_rot",
          origin_pos=client.make_position(0, 0, 0),
          origin_rot=client.make_identity_quaternion(),
          obj_pos=client.make_position(1, 2, 3),
          obj_rot=client.make_quaternion_from_euler(30, 45, 60),
          expected_pos=client.make_position(1, 2, 3),
          expected_rot=client.make_quaternion_from_euler(30, 45, 60),
      ),
      dict(
          testcase_name="pos_to_pos_only",
          origin_pos=client.make_position(1, 2, 3),
          origin_rot=client.make_identity_quaternion(),
          obj_pos=client.make_position(5, 7, 9),
          obj_rot=client.make_identity_quaternion(),
          expected_pos=client.make_position(4, 5, 6),
          expected_rot=client.make_identity_quaternion(),
      ),
      dict(
          testcase_name="pos_to_rot_only",
          origin_pos=client.make_position(1, 2, 3),
          origin_rot=client.make_identity_quaternion(),
          obj_pos=client.make_position(1, 2, 3),
          obj_rot=client.make_quaternion_from_euler(30, 45, 60),
          expected_pos=client.make_position(0, 0, 0),
          expected_rot=client.make_quaternion_from_euler(30, 45, 60),
      ),
      dict(
          testcase_name="pos_to_pos_and_rot",
          origin_pos=client.make_position(1, 2, 3),
          origin_rot=client.make_identity_quaternion(),
          obj_pos=client.make_position(5, 7, 9),
          obj_rot=client.make_quaternion_from_euler(30, 45, 60),
          expected_pos=client.make_position(4, 5, 6),
          expected_rot=client.make_quaternion_from_euler(30, 45, 60),
      ),
      dict(
          testcase_name="rot_to_pos_only",
          origin_pos=client.make_position(0, 0, 0),
          origin_rot=client.make_quaternion_from_euler(30, 45, 60),
          obj_pos=client.make_position(1, 2, 3),
          obj_rot=client.make_identity_quaternion(),
          expected_pos=client.make_position(-0.54302, 1.96583, 3.13698),
          expected_rot=client.make_quaternion_from_euler(
              24.5973, -47.6635, -58.3344
          ),
      ),
      dict(
          testcase_name="rot_to_rot_only",
          origin_pos=client.make_position(0, 0, 0),
          origin_rot=client.make_quaternion_from_euler(30, 45, 60),
          obj_pos=client.make_position(0, 0, 0),
          obj_rot=client.make_quaternion_from_euler(60, 90, 120),
          expected_pos=client.make_position(0, 0, 0),
          expected_rot=client.make_quaternion_from_euler(
              -39.2317, 37.7606, -26.5654
          ),
      ),
      dict(
          testcase_name="rot_to_pos_and_rot",
          origin_pos=client.make_position(0, 0, 0),
          origin_rot=client.make_quaternion_from_euler(30, 45, 60),
          obj_pos=client.make_position(1, 2, 3),
          obj_rot=client.make_quaternion_from_euler(60, 90, 120),
          expected_pos=client.make_position(-0.54302, 1.96583, 3.13698),
          expected_rot=client.make_quaternion_from_euler(
              -39.232, 37.761, -26.565
          ),
      ),
      dict(
          testcase_name="pos_and_rot_to_pos_and_rot",
          origin_pos=client.make_position(1, 2, 3),
          origin_rot=client.make_quaternion_from_euler(30, 45, 60),
          obj_pos=client.make_position(4, 5, 6),
          obj_rot=client.make_quaternion_from_euler(60, 90, 120),
          expected_pos=client.make_position(0.77646, 1.55859, 4.8957),
          expected_rot=client.make_quaternion_from_euler(
              -39.232, 37.761, -26.565
          ),
      ),
  )
  def test_get_relative_pose(
      self,
      origin_pos: robot_types_pb2.Position,
      origin_rot: robot_types_pb2.Quaternion,
      obj_pos: robot_types_pb2.Position,
      obj_rot: robot_types_pb2.Quaternion,
      expected_pos: robot_types_pb2.Position,
      expected_rot: robot_types_pb2.Quaternion,
  ):
    relative_pos, relative_rot = client.get_relative_pose(
        origin_pos, origin_rot, obj_pos, obj_rot
    )
    nptest.assert_almost_equal(
        [relative_pos.px, relative_pos.py, relative_pos.pz],
        [expected_pos.px, expected_pos.py, expected_pos.pz],
        5,
    )
    nptest.assert_almost_equal(
        [relative_rot.qx, relative_rot.qy, relative_rot.qz, relative_rot.qw],
        [expected_rot.qx, expected_rot.qy, expected_rot.qz, expected_rot.qw],
        5,
    )

  def test_add_joint_state_to_raw_joints_generic(self):
    raw_joints = robotics_ui_pb2.RawJoints()
    joint_state = robot_state_pb2.JointState(positions=[1, 2, 3])
    client.add_joint_state_to_raw_joints(raw_joints, "thing", joint_state)
    expected_generic = {
        "thing": robot_state_pb2.JointState(positions=[1, 2, 3])
    }
    self.assertEqual(
        raw_joints,
        robotics_ui_pb2.RawJoints(generic=expected_generic),
    )

  def test_add_joint_state_to_raw_joints_field(self):
    raw_joints = robotics_ui_pb2.RawJoints()
    joint_state = robot_state_pb2.JointState(positions=[1, 2, 3])
    client.add_joint_state_to_raw_joints(
        raw_joints, "right_arm", joint_state
    )
    self.assertEqual(
        raw_joints,
        robotics_ui_pb2.RawJoints(
            right_arm=robot_state_pb2.JointState(positions=[1, 2, 3])
        ),
    )

  def test_get_position_from_transform(self):
    """Tests extracting position from a Transform."""
    expected_pos = client.make_position(1.1, 2.2, 3.3)
    # Use robot_types_pb2.Transform directly
    transform = robot_types_pb2.Transform(
        px=expected_pos.px, py=expected_pos.py, pz=expected_pos.pz
    )
    actual_pos = client.get_position_from_transform(transform)
    self.assertEqual(actual_pos, expected_pos)

  def test_get_rotation_from_transform(self):
    """Tests extracting rotation from a Transform."""
    expected_rot = client.make_quaternion_from_euler(30, 45, 60)
    # Use robot_types_pb2.Transform directly
    transform = robot_types_pb2.Transform(
        qx=expected_rot.qx,
        qy=expected_rot.qy,
        qz=expected_rot.qz,
        qw=expected_rot.qw,
    )
    actual_rot = client.get_rotation_from_transform(transform)
    self.assertEqual(actual_rot, expected_rot)


if __name__ == "__main__":
  absltest.main()
