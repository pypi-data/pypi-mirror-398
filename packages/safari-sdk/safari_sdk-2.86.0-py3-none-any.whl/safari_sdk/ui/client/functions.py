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

"""Functions for working with the Robotics UI API."""

import math

import numpy as np

from safari_sdk.protos.ui import robot_state_pb2
from safari_sdk.protos.ui import robot_types_pb2
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui.client import quaternions


_POSITION_TOLERANCE = 1e-6
_ANGLE_TOLERANCE = 1e-2


def _to_np(x: float, y: float, z: float, w: float) -> np.ndarray:
  return np.asarray([w, x, y, z], dtype=np.float32)


def _quaternion_to_np(
    q: robot_types_pb2.Quaternion,
) -> np.ndarray:
  return _to_np(x=q.qx, y=q.qy, z=q.qz, w=q.qw)


def _np_to_quaternion(
    q: np.ndarray,
) -> robot_types_pb2.Quaternion:
  return robot_types_pb2.Quaternion(qw=q[0], qx=q[1], qy=q[2], qz=q[3])


def quaternion_xyzw_to_axis_angle(
    x: float, y: float, z: float, w: float
) -> tuple[tuple[float, float, float], float]:
  """Converts a quaternion to axis-angle representation.

  Args:
    x: The x component of the quaternion.
    y: The y component of the quaternion.
    z: The z component of the quaternion.
    w: The w component of the quaternion.

  Returns:
    A tuple of the axis and the angle in radians.
  """
  q = _to_np(x, y, z, w)
  npaxis, angle = quaternions.quat2axangle(q)
  axis = npaxis.tolist()

  return ((axis[0], axis[1], axis[2]), angle)


def quaternion_to_axis_angle(
    q: robot_types_pb2.Quaternion,
) -> tuple[tuple[float, float, float], float]:
  return quaternion_xyzw_to_axis_angle(x=q.qx, y=q.qy, z=q.qz, w=q.qw)


def multiply_quaternions(
    q1: robot_types_pb2.Quaternion, q2: robot_types_pb2.Quaternion
) -> robot_types_pb2.Quaternion:
  """Multiplies two quaternions, q1 * q2."""
  return _np_to_quaternion(
      quaternions.qmult(_quaternion_to_np(q1), _quaternion_to_np(q2))
  )


def multiply_vector_by_quaternion(
    q: robot_types_pb2.Quaternion, v: robot_types_pb2.Position
) -> robot_types_pb2.Position:
  """Multiplies a vector by a quaternion, effectively rotating the vector."""
  rot_matrix = quaternions.quat2mat(_quaternion_to_np(q))
  np_v = np.asarray([v.px, v.py, v.pz])
  rotated_v = rot_matrix @ np_v
  return robot_types_pb2.Position(
      px=rotated_v[0], py=rotated_v[1], pz=rotated_v[2]
  )


def invert_quaternion(
    q: robot_types_pb2.Quaternion,
) -> robot_types_pb2.Quaternion:
  """Inverts a quaternion."""
  return _np_to_quaternion(quaternions.qinverse(_quaternion_to_np(q)))


def make_transform_matrix(
    pos: robot_types_pb2.Position, rot: robot_types_pb2.Quaternion
) -> np.ndarray:
  """Converts a position and quaternion to a 4x4 transform matrix."""
  m = np.identity(4)
  m[:3, :3] = quaternions.quat2mat(_quaternion_to_np(rot))
  m[:3, 3] = [pos.px, pos.py, pos.pz]
  return m


def get_relative_pose(
    origin_pos: robot_types_pb2.Position,
    origin_rot: robot_types_pb2.Quaternion,
    obj_pos: robot_types_pb2.Position,
    obj_rot: robot_types_pb2.Quaternion,
) -> tuple[robot_types_pb2.Position, robot_types_pb2.Quaternion]:
  """Returns the relative pose of obj with respect to origin."""
  zero_t_origin = make_transform_matrix(origin_pos, origin_rot)
  zero_t_obj = make_transform_matrix(obj_pos, obj_rot)
  origin_t_zero = np.linalg.inv(zero_t_origin)
  origin_t_obj = origin_t_zero @ zero_t_obj
  return (
      robot_types_pb2.Position(
          px=origin_t_obj[0, 3], py=origin_t_obj[1, 3], pz=origin_t_obj[2, 3]
      ),
      _np_to_quaternion(quaternions.mat2quat(origin_t_obj[:3, :3])),
  )


def apply_local_pose(
    origin_pos: robot_types_pb2.Position,
    origin_rot: robot_types_pb2.Quaternion,
    translate: robot_types_pb2.Position,
    rotate: robot_types_pb2.Quaternion,
) -> tuple[robot_types_pb2.Position, robot_types_pb2.Quaternion]:
  """Applies a local translation and rotation to a global pose."""
  zero_t_origin = make_transform_matrix(origin_pos, origin_rot)
  zero_t_local = make_transform_matrix(translate, rotate)
  zero_t_obj = zero_t_origin @ zero_t_local
  return (
      robot_types_pb2.Position(
          px=zero_t_obj[0, 3], py=zero_t_obj[1, 3], pz=zero_t_obj[2, 3]
      ),
      _np_to_quaternion(quaternions.mat2quat(zero_t_obj[:3, :3])),
  )


def make_euler_from_quaternion(
    qw: float, qx: float, qy: float, qz: float
) -> tuple[float, float, float]:
  """Converts a Quaternion proto to Euler angles (with order of rotation ZYX).

  Args:
      qw: The w component of the quaternion.
      qx: The x component of the quaternion.
      qy: The y component of the quaternion.
      qz: The z component of the quaternion.

  Returns:
      A tuple containing the roll, pitch, and yaw angles in radians.
  """
  t0 = +2.0 * (qw * qx + qy * qz)
  t1 = +1.0 - 2.0 * (qx * qx + qy * qy)
  roll_x = math.atan2(t0, t1)

  t2 = +2.0 * (qw * qy - qz * qx)
  t2 = +1.0 if t2 > +1.0 else t2
  t2 = -1.0 if t2 < -1.0 else t2
  pitch_y = math.asin(t2)

  t3 = +2.0 * (qw * qz + qx * qy)
  t4 = +1.0 - 2.0 * (qy * qy + qz * qz)
  yaw_z = math.atan2(t3, t4)

  return roll_x, pitch_y, yaw_z


def make_quaternion_from_euler(
    rx: float, ry: float, rz: float
) -> robot_types_pb2.Quaternion:
  """Converts Euler angles (with order of rotation ZYX) to a Quaternion proto.

  Args:
    rx: The rotation about the x axis, in degrees, in a right-handed system,
      also known as roll.
    ry: The rotation about the y axis, in degrees, in a right-handed system,
      also known as pitch.
    rz: The rotation about the z axis, in degrees, in a right-handed system,
      also known as yaw.

  Returns:
    The corresponding Quaternion.
  """
  rx = math.radians(rx)
  ry = math.radians(ry)
  rz = math.radians(rz)

  rh = rx / 2
  ph = ry / 2
  yh = rz / 2

  crh = math.cos(rh)
  srh = math.sin(rh)
  cph = math.cos(ph)
  sph = math.sin(ph)
  cyh = math.cos(yh)
  syh = math.sin(yh)

  qw = crh * cyh * cph + srh * sph * syh
  qx = srh * cyh * cph - crh * sph * syh
  qy = crh * cyh * sph + srh * cph * syh
  qz = crh * syh * cph - srh * sph * cyh

  return robot_types_pb2.Quaternion(qw=qw, qx=qx, qy=qy, qz=qz)


def make_quaternion_from_axis_angle(
    axis: tuple[float, float, float], angle: float
) -> robot_types_pb2.Quaternion:
  """Converts an axis-angle representation to a Quaternion proto.

  Args:
    axis: The axis of rotation. Doesn't need to be normalized.
    angle: The angle of rotation, in radians.

  Returns:
    The corresponding Quaternion.
  """
  return _np_to_quaternion(quaternions.axangle2quat(np.asarray(axis), angle))


def get_position_from_transform(
    transform: robot_types_pb2.Transform,
) -> robot_types_pb2.Position:
  """Returns the position from a Transform proto."""
  return robot_types_pb2.Position(
      px=transform.px,
      py=transform.py,
      pz=transform.pz
  )


def get_rotation_from_transform(
    transform: robot_types_pb2.Transform,
) -> robot_types_pb2.Quaternion:
  """Returns the rotation from a Transform proto."""
  return robot_types_pb2.Quaternion(
      qx=transform.qx,
      qy=transform.qy,
      qz=transform.qz,
      qw=transform.qw
  )


def make_transform(
    pos: robot_types_pb2.Position,
    rot: robot_types_pb2.Quaternion,
    scale: robot_types_pb2.Position | None = None,
) -> robotics_ui_pb2.UITransform:
  """Converts Position and Quaternion protos into a UITransform proto.

  Args:
    pos: The position to set in the transform.
    rot: The rotation to set in the transform.
    scale: The scale to set in the rotation, or <1, 1, 1> if not specified.

  Returns:
    A UITransform.
  """
  if scale is None:
    scale = make_scale(1, 1, 1)
  return robotics_ui_pb2.UITransform(position=pos, rotation=rot, scale=scale)


def make_quaternion(
    qx: float, qy: float, qz: float, qw: float
) -> robot_types_pb2.Quaternion:
  """Makes a Quaternion from qw, qx, qy, and qz."""
  return robot_types_pb2.Quaternion(qw=qw, qx=qx, qy=qy, qz=qz)


def make_identity_quaternion() -> robot_types_pb2.Quaternion:
  """Makes an identity Quaternion."""
  return robot_types_pb2.Quaternion(qw=1, qx=0, qy=0, qz=0)


def quaternions_approximately_equal(
    q1: robot_types_pb2.Quaternion,
    q2: robot_types_pb2.Quaternion,
) -> bool:
  """Returns whether two Quaternions are approximately equal."""
  return (
      abs(q1.qw - q2.qw) < _ANGLE_TOLERANCE
      and abs(q1.qx - q2.qx) < _ANGLE_TOLERANCE
      and abs(q1.qy - q2.qy) < _ANGLE_TOLERANCE
      and abs(q1.qz - q2.qz) < _ANGLE_TOLERANCE
  )


def make_position(x: float, y: float, z: float) -> robot_types_pb2.Position:
  """Makes a Position from x, y, and z."""
  return robot_types_pb2.Position(px=x, py=y, pz=z)


def positions_approximately_equal(
    p1: robot_types_pb2.Position,
    p2: robot_types_pb2.Position,
) -> bool:
  """Returns whether two Positions are approximately equal."""
  return (
      abs(p1.px - p2.px) < _POSITION_TOLERANCE
      and abs(p1.py - p2.py) < _POSITION_TOLERANCE
      and abs(p1.pz - p2.pz) < _POSITION_TOLERANCE
  )


def make_scale(x: float, y: float, z: float) -> robot_types_pb2.Position:
  """Makes a Position (for use as a scale) from x, y, and z."""
  return robot_types_pb2.Position(px=x, py=y, pz=z)


def make_identity() -> robotics_ui_pb2.UITransform:
  """Makes an Identity Transform."""
  return robotics_ui_pb2.UITransform(
      position=robot_types_pb2.Position(px=0, py=0, pz=0),
      rotation=robot_types_pb2.Quaternion(qx=0, qy=0, qz=0, qw=1),
      scale=robot_types_pb2.Position(px=1, py=1, pz=1),
  )


def add_joint_state_to_raw_joints(
    raw_joints: robotics_ui_pb2.RawJoints,
    part_id: str,
    joint_state: robot_state_pb2.JointState,
) -> None:
  """Adds a JointState to a RawJoints proto.

  Attempts to find a field with the same name as part_id, and if it exists,
  sets that field to joint_state. Otherwise, sets joint_state in the generic
  map.

  Args:
    raw_joints: The RawJoints proto to add the JointState to.
    part_id: The part id of the JointState.
    joint_state: The JointState to add.
  """
  if part_id not in raw_joints.DESCRIPTOR.fields_by_name:
    raw_joints.generic[part_id].CopyFrom(joint_state)
    return
  field = raw_joints.DESCRIPTOR.fields_by_name[part_id]
  if field.message_type != robot_state_pb2.JointState.DESCRIPTOR:
    raise ValueError(
        f"Field {part_id} is not a JointState: {field.message_type}"
    )
  getattr(raw_joints, part_id).CopyFrom(joint_state)


def assert_kinematic_tree_robot_bodies_approximately_equal(
    got: robotics_ui_pb2.KinematicTreeRobotBody,
    expected: robotics_ui_pb2.KinematicTreeRobotBody,
) -> None:
  """Returns whether two KinematicTreeRobotBodies are approximately equal."""
  assert got.name == expected.name, f"Names are not equal: {got=}; {expected=}"
  assert positions_approximately_equal(
      got.position, expected.position
  ), f"Positions are not equal: {got=}; {expected=}"
  assert quaternions_approximately_equal(
      got.rotation, expected.rotation
  ), f"Rotations are not equal: {got=}; {expected=}"
  assert kinematic_tree_robot_joints_approximately_equal(
      got.joints, expected.joints
  ), f"Joints are not equal: {got.joints=}; {expected.joints=}"
  assert all(
      kinematic_tree_robot_geometries_approximately_equal(g1, g2)
      for g1, g2 in zip(got.geometries, expected.geometries)
  ), f"Geometries are not equal: {got.geometries=}; {expected.geometries=}"
  assert all(
      kinematic_tree_robot_sites_approximately_equal(s1, s2)
      for s1, s2 in zip(got.sites, expected.sites)
  ), f"Sites are not equal: {got=}; {expected=}"
  for c1, c2 in zip(got.children, expected.children):
    assert_kinematic_tree_robot_bodies_approximately_equal(c1, c2)


def kinematic_tree_robot_geometries_approximately_equal(
    g1: robotics_ui_pb2.KinematicTreeRobotGeometry,
    g2: robotics_ui_pb2.KinematicTreeRobotGeometry,
) -> bool:
  """Returns whether two KinematicTreeRobotGeometries are approximately equal."""
  return (
      g1.name == g2.name
      and positions_approximately_equal(g1.position, g2.position)
      and quaternions_approximately_equal(g1.rotation, g2.rotation)
      and g1.hash == g2.hash
  )


def kinematic_tree_robot_joints_approximately_equal(
    j1: robotics_ui_pb2.KinematicTreeRobotJoint,
    j2: robotics_ui_pb2.KinematicTreeRobotJoint,
) -> bool:
  """Returns whether two KinematicTreeRobotJoints are approximately equal."""
  return (
      j1.name == j2.name
      and positions_approximately_equal(j1.position, j2.position)
      and positions_approximately_equal(j1.axis, j2.axis)
      and abs(j1.min_angle_radians - j2.min_angle_radians) < _ANGLE_TOLERANCE
      and abs(j1.max_angle_radians - j2.max_angle_radians) < _ANGLE_TOLERANCE
  )


def kinematic_tree_robot_sites_approximately_equal(
    s1: robotics_ui_pb2.KinematicTreeRobotSite,
    s2: robotics_ui_pb2.KinematicTreeRobotSite,
) -> bool:
  """Returns whether two KinematicTreeRobotSites are approximately equal."""
  return (
      s1.name == s2.name
      and positions_approximately_equal(s1.position, s2.position)
      and quaternions_approximately_equal(s1.rotation, s2.rotation)
  )
