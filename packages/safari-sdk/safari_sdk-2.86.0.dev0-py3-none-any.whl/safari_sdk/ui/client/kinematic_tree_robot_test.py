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

"""Unit tests for kinematic_tree_robot.py."""

import math
import pathlib
import tempfile
import zipfile


from absl.testing import absltest
from safari_sdk.protos.ui import robot_frames_pb2
from safari_sdk.protos.ui import robot_types_pb2
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui.client import exceptions
from safari_sdk.ui.client import functions
from safari_sdk.ui.client import kinematic_tree_robot
from safari_sdk.ui.client import types


TESTDIR = pathlib.Path(
    "safari_sdk/ui/client/testdata"
)
ZEROPOS = robot_types_pb2.Position(px=0, py=0, pz=0)
IDENTITY_QUAT = robot_types_pb2.Quaternion(qw=1, qx=0, qy=0, qz=0)


class KinematicTreeRobotTest(absltest.TestCase):

  def test_parse_fails_on_file_not_found(self):
    xml_path = pathlib.Path("/does/not/exist.xml")
    with self.assertRaisesRegex(
        exceptions.KinematicTreeRobotUploadError, "Failed to parse"
    ):
      kinematic_tree_robot.KinematicTree.parse(
          kinematic_tree_robot_id="kinematic_tree_robot",
          xml_path=str(xml_path.as_posix()),
          joint_mapping={},
      )

  def test_parse_fails_on_unparseable_xml(self):
    xml_path = (TESTDIR / "unparseable.xml")
    with self.assertRaisesRegex(
        exceptions.KinematicTreeRobotUploadError, "Failed to parse"
    ):
      kinematic_tree_robot.KinematicTree.parse(
          kinematic_tree_robot_id="kinematic_tree_robot",
          xml_path=xml_path,
          joint_mapping={},
      )

  def test_parse_fails_on_not_mujoco(self):
    xml_path = (TESTDIR / "not_mujoco.xml")
    with self.assertRaisesRegex(
        exceptions.KinematicTreeRobotUploadError, "Failed to parse"
    ):
      kinematic_tree_robot.KinematicTree.parse(
          kinematic_tree_robot_id="kinematic_tree_robot",
          xml_path=xml_path,
          joint_mapping={},
      )

  def test_parse_gathers_meshes(self):
    xml_path = (
        TESTDIR / "kinematic_tree_robot_meshes_only.xml"
    )
    kinematic_tree = kinematic_tree_robot.KinematicTree.parse(
        kinematic_tree_robot_id="kinematic_tree_robot",
        xml_path=xml_path,
        joint_mapping={},
    )
    mesh_paths = {
        name: types.ResourceLocator(locator.scheme, locator.path)
        for name, locator in kinematic_tree.mesh_paths.items()
    }
    self.assertEqual(
        mesh_paths,
        {
            "mesh_left_arm": types.ResourceLocator(
                scheme="mesh", path="mesh_left_arm.stl"
            ),
            "mesh_right_arm": types.ResourceLocator(
                scheme="mesh", path="mesh_right_arm.stl"
            ),
            "mesh_torso": types.ResourceLocator(
                scheme="mesh", path="mesh_torso.stl"
            ),
            "mesh_head": types.ResourceLocator(
                scheme="mesh", path="mesh_head.stl"
            ),
        },
    )

  def test_parse_fails_on_missing_mesh_file(self):
    xml_path = (
        TESTDIR / "kinematic_tree_robot_missing_mesh.xml"
    )
    with self.assertRaisesRegex(
        exceptions.KinematicTreeRobotUploadError, "Failed to parse"
    ):
      kinematic_tree_robot.KinematicTree.parse(
          kinematic_tree_robot_id="kinematic_tree_robot",
          xml_path=xml_path,
          joint_mapping={},
      )

  def test_parse_fails_on_missing_joint(self):
    xml_path = (
        TESTDIR / "kinematic_tree_robot_meshes_only.xml"
    )
    with self.assertRaisesRegex(
        exceptions.KinematicTreeRobotUploadError,
        "Joint joint_left_arm not found in XML file",
    ):
      kinematic_tree_robot.KinematicTree.parse(
          kinematic_tree_robot_id="kinematic_tree_robot",
          xml_path=xml_path,
          joint_mapping={
              robot_frames_pb2.Frame.Enum.LEFT_ARM: ["joint_left_arm"],
          },
      )

  def test_parse_basic_body(self):
    xml_path = (
        TESTDIR / "kinematic_tree_robot_basic.xml"
    )
    kinematic_tree = kinematic_tree_robot.KinematicTree.parse(
        kinematic_tree_robot_id="kinematic_tree_robot",
        xml_path=xml_path,
        joint_mapping={},
    )
    mesh_hashes = {
        "mesh_left_arm": b"1",
        "mesh_right_arm": b"2",
    }
    bodies = [body.to_proto(mesh_hashes) for body in kinematic_tree.bodies]
    print(bodies)
    self.assertLen(bodies, 1)
    expected_body = robotics_ui_pb2.KinematicTreeRobotBody(
        name="left_arm",
        position=robot_types_pb2.Position(px=1, py=2, pz=3),
        rotation=IDENTITY_QUAT,
        geometries=[
            robotics_ui_pb2.KinematicTreeRobotGeometry(
                name="mesh_left_arm",
                position=ZEROPOS,
                rotation=IDENTITY_QUAT,
                hash=b"1",
            )
        ],
        children=[
            robotics_ui_pb2.KinematicTreeRobotBody(
                name="right_arm",
                position=robot_types_pb2.Position(px=-1, py=-2, pz=-3),
                rotation=functions.make_quaternion_from_euler(
                    rx=-180, ry=0, rz=0
                ),
                joints=robotics_ui_pb2.KinematicTreeRobotJoint(
                    name="joint_right_arm",
                    position=ZEROPOS,
                    axis=robot_types_pb2.Position(px=0, py=0, pz=1),
                    max_angle_radians=math.pi,
                ),
                geometries=[
                    robotics_ui_pb2.KinematicTreeRobotGeometry(
                        name="mesh_right_arm",
                        position=ZEROPOS,
                        rotation=IDENTITY_QUAT,
                        hash=b"2",
                    )
                ],
            ),
        ],
    )
    functions.assert_kinematic_tree_robot_bodies_approximately_equal(
        bodies[0], expected_body
    )

  def test_parse_kinematic_tree_robot(self):
    self.maxDiff = None
    xml_path = (
        TESTDIR / "kinematic_tree_robot.xml"
    )
    joint_mapping = {
        robot_frames_pb2.Frame.Enum.LEFT_ARM: ["joint_left_arm"],
        robot_frames_pb2.Frame.Enum.RIGHT_ARM: ["joint_right_arm"],
        robot_frames_pb2.Frame.Enum.HEAD: ["joint_head"],
    }
    kinematic_tree = kinematic_tree_robot.KinematicTree.parse(
        kinematic_tree_robot_id="kinematic_tree_robot",
        xml_path=xml_path,
        joint_mapping=joint_mapping,
    )
    mesh_hashes = {
        "mesh_left_arm": b"1",
        "mesh_right_arm": b"2",
        "mesh_torso": b"3",
        "mesh_head": b"4",
    }
    bodies = [body.to_proto(mesh_hashes) for body in kinematic_tree.bodies]
    print(bodies)
    self.assertLen(bodies, 1)
    expected_body = robotics_ui_pb2.KinematicTreeRobotBody(
        name="body0",
        position=robot_types_pb2.Position(px=1, py=2, pz=3),
        rotation=IDENTITY_QUAT,
        geometries=[
            robotics_ui_pb2.KinematicTreeRobotGeometry(
                name="mesh_torso",
                position=robot_types_pb2.Position(px=0.1, py=0.2, pz=0.3),
                rotation=functions.make_quaternion_from_euler(
                    rx=10, ry=20, rz=30
                ),
                hash=b"3",
            ),
        ],
        children=[
            robotics_ui_pb2.KinematicTreeRobotBody(
                name="right_arm",
                position=robot_types_pb2.Position(px=-1, py=-2, pz=-3),
                rotation=functions.make_quaternion_from_euler(
                    rx=-180, ry=0, rz=0
                ),
                joints=robotics_ui_pb2.KinematicTreeRobotJoint(
                    name="joint_right_arm",
                    position=robot_types_pb2.Position(
                        px=-0.1, py=-0.2, pz=-0.3
                    ),
                    axis=robot_types_pb2.Position(px=0, py=0, pz=1),
                    max_angle_radians=math.pi,
                ),
                geometries=[
                    robotics_ui_pb2.KinematicTreeRobotGeometry(
                        name="mesh_right_arm",
                        position=ZEROPOS,
                        rotation=IDENTITY_QUAT,
                        hash=b"2",
                    )
                ],
            ),
            robotics_ui_pb2.KinematicTreeRobotBody(
                name="left_arm",
                position=robot_types_pb2.Position(px=1, py=-2, pz=-3),
                rotation=robot_types_pb2.Quaternion(qx=1, qy=0, qz=0, qw=0),
                joints=robotics_ui_pb2.KinematicTreeRobotJoint(
                    name="joint_left_arm",
                    position=ZEROPOS,
                    axis=robot_types_pb2.Position(px=0, py=1, pz=0),
                    min_angle_radians=-math.pi,
                ),
                geometries=[
                    robotics_ui_pb2.KinematicTreeRobotGeometry(
                        name="mesh_left_arm",
                        position=ZEROPOS,
                        rotation=IDENTITY_QUAT,
                        hash=b"1",
                    )
                ],
                sites=[
                    robotics_ui_pb2.KinematicTreeRobotSite(
                        name="left_site_a",
                        position=robot_types_pb2.Position(
                            px=0.01, py=0.02, pz=0.03
                        ),
                        rotation=functions.make_quaternion_from_euler(
                            rx=1, ry=2, rz=3
                        ),
                    ),
                    robotics_ui_pb2.KinematicTreeRobotSite(
                        name="left_site_b",
                        position=robot_types_pb2.Position(
                            px=-0.01, py=0.02, pz=0.03
                        ),
                        rotation=functions.make_quaternion_from_euler(
                            rx=-1, ry=2, rz=3
                        ),
                    ),
                ],
            ),
            robotics_ui_pb2.KinematicTreeRobotBody(
                name="head",
                position=ZEROPOS,
                rotation=IDENTITY_QUAT,
                joints=robotics_ui_pb2.KinematicTreeRobotJoint(
                    name="joint_head",
                    position=ZEROPOS,
                    axis=robot_types_pb2.Position(px=0, py=0, pz=1),
                    min_angle_radians=-2 * math.pi,
                    max_angle_radians=2 * math.pi,
                ),
                geometries=[
                    robotics_ui_pb2.KinematicTreeRobotGeometry(
                        name="mesh_head",
                        position=ZEROPOS,
                        # Not sure why mujoco changes the rotation here. We're
                        # not testing mujoco, though, just that we return the
                        # correct proto data.
                        rotation=functions.make_quaternion(
                            qw=0.804464221,
                            qx=0.464457661,
                            qy=0.185146138,
                            qz=-0.320682526,
                        ),
                        hash=b"4",
                    )
                ],
                sites=[
                    robotics_ui_pb2.KinematicTreeRobotSite(
                        name="head_site",
                        position=ZEROPOS,
                        rotation=IDENTITY_QUAT,
                    )
                ],
            ),
            robotics_ui_pb2.KinematicTreeRobotBody(
                name="body1",
                position=ZEROPOS,
                rotation=IDENTITY_QUAT,
                joints=robotics_ui_pb2.KinematicTreeRobotJoint(
                    name="joint2",
                    position=ZEROPOS,
                    axis=robot_types_pb2.Position(px=0, py=0, pz=1),
                    min_angle_radians=-2 * math.pi,
                    max_angle_radians=2 * math.pi,
                ),
                sites=[
                    robotics_ui_pb2.KinematicTreeRobotSite(
                        name="site3",
                        position=ZEROPOS,
                        rotation=IDENTITY_QUAT,
                    )
                ],
            ),
        ],
    )
    functions.assert_kinematic_tree_robot_bodies_approximately_equal(
        bodies[0], expected_body
    )

  def test_find_body_by_name(self):
    xml_path = (
        TESTDIR / "kinematic_tree_robot.xml"
    )
    kinematic_tree = kinematic_tree_robot.KinematicTree.parse(
        kinematic_tree_robot_id="kinematic_tree_robot",
        xml_path=xml_path,
        joint_mapping={},
    )
    self.assertEqual(
        kinematic_tree.find_body_by_name("body0"), kinematic_tree.bodies[0]
    )
    self.assertEqual(
        kinematic_tree.find_body_by_name("left_arm"),
        kinematic_tree.bodies[0].bodies[1],
    )
    self.assertIsNone(kinematic_tree.find_body_by_name("body_not_found"))

  def test_add_origin_site(self):
    xml_path = (
        TESTDIR / "kinematic_tree_robot.xml"
    )
    site_pos = robot_types_pb2.Position(px=1, py=2, pz=3)
    site_rot = robot_types_pb2.Quaternion(qw=0, qx=1, qy=0, qz=0)
    kinematic_tree = kinematic_tree_robot.KinematicTree.parse(
        kinematic_tree_robot_id="kinematic_tree_robot",
        xml_path=xml_path,
        joint_mapping={},
        origin_site=types.BodySiteSpec(
            body="left_arm", pos=site_pos, rot=site_rot
        ),
    )
    self.assertEqual(
        kinematic_tree.find_body_by_name("left_arm").sites[2],
        kinematic_tree_robot.SiteSpec(
            name="Origin Point", pos=site_pos, rot=site_rot
        ),
    )

  def test_add_embody_site(self):
    xml_path = (
        TESTDIR / "kinematic_tree_robot.xml"
    )
    site_pos = robot_types_pb2.Position(px=1, py=2, pz=3)
    site_rot = robot_types_pb2.Quaternion(qw=0, qx=1, qy=0, qz=0)
    kinematic_tree = kinematic_tree_robot.KinematicTree.parse(
        kinematic_tree_robot_id="kinematic_tree_robot",
        xml_path=xml_path,
        joint_mapping={},
        embody_site=types.BodySiteSpec(
            body="left_arm", pos=site_pos, rot=site_rot
        ),
    )
    self.assertEqual(
        kinematic_tree.find_body_by_name("left_arm").sites[2],
        kinematic_tree_robot.SiteSpec(
            name="Embody Point", pos=site_pos, rot=site_rot
        ),
    )

  def test_parse_kinematic_tree_robot_from_path(self):
    xml_path = pathlib.Path(
        (TESTDIR / "kinematic_tree_robot.xml")
    )
    joint_mapping = {}
    kinematic_tree_robot.KinematicTree.parse(
        kinematic_tree_robot_id="kinematic_tree_robot",
        xml_path=xml_path,
        joint_mapping=joint_mapping,
    )

  def test_parse_kinematic_tree_robot_from_zip_not_found(self):
    zip_path = pathlib.Path(TESTDIR / "not_found.zip")
    with self.assertRaisesRegex(
        exceptions.KinematicTreeRobotUploadError,
        "Failed to open ZIP file at",
    ):
      kinematic_tree_robot.KinematicTree.parse_from_zip(
          kinematic_tree_robot_id="kinematic_tree_robot",
          zip_path=zip_path,
          xml_path="kinematic_tree_robot.xml",
      )

  def test_parse_kinematic_tree_robot_from_zip(self):
    with tempfile.NamedTemporaryFile(
        mode="wb", suffix=".zip", delete=False
    ) as zip_file:
      with zipfile.ZipFile(zip_file, "w") as f:
        for file in [
            "kinematic_tree_robot.xml",
            "kinematic_tree_robot_joint_mapping.json",
            "kinematic_tree_robot_sites.json",
            "mesh_left_arm.stl",
            "mesh_right_arm.stl",
            "mesh_torso.stl",
            "mesh_head.stl",
        ]:
          f.write((TESTDIR / file), file)

      kinematic_tree = kinematic_tree_robot.KinematicTree.parse_from_zip(
          kinematic_tree_robot_id="kinematic_tree_robot",
          zip_path=zip_file.name,
          xml_path="kinematic_tree_robot.xml",
      )

      site_pos = robot_types_pb2.Position(px=1, py=0, pz=0)
      site_rot = robot_types_pb2.Quaternion(qw=1, qx=0, qy=0, qz=0)
      self.assertEqual(
          kinematic_tree.find_body_by_name("head").sites[1],
          kinematic_tree_robot.SiteSpec(
              name="Embody Point", pos=site_pos, rot=site_rot
          ),
      )


if __name__ == "__main__":
  absltest.main()
