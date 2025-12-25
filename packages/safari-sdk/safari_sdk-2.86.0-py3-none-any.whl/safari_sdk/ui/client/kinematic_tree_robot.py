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

"""Uploads a Mujoco-based robot into the RoboticsUI cache."""

from __future__ import annotations  # For cyclic type annotations in Body.

import dataclasses
import datetime
import json
import logging
import pathlib
import tempfile
import threading
import time
import zipfile

import mujoco

from safari_sdk.protos.ui import robot_frames_pb2
from safari_sdk.protos.ui import robot_types_pb2
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui.client import exceptions
from safari_sdk.ui.client import functions
from safari_sdk.ui.client import iframework
from safari_sdk.ui.client import stl_parser
from safari_sdk.ui.client import types


IFramework = iframework.IFramework


@dataclasses.dataclass
class MeshSpec:
  """Represents a mesh in the XML."""

  name: str
  pos: robot_types_pb2.Position
  rot: robot_types_pb2.Quaternion
  scale: float


@dataclasses.dataclass
class SiteSpec:
  """Represents a site in the XML."""

  name: str
  pos: robot_types_pb2.Position
  rot: robot_types_pb2.Quaternion


@dataclasses.dataclass
class Body:
  """Represents a single body in a kinematic tree.

  See https://mujoco.readthedocs.io/en/stable/XMLreference.html for details.
  """

  name: str
  transform_pos: robot_types_pb2.Position  # local relative to parent
  transform_quat: robot_types_pb2.Quaternion
  has_joint: bool
  is_supported_joint: bool
  joint_name: str
  joint_pos: robot_types_pb2.Position  # relative to transform
  joint_axis: robot_types_pb2.Position
  joint_range: list[float]
  meshes: list[MeshSpec]
  sites: list[SiteSpec]
  bodies: list[Body]  # sub-bodies

  def __init__(self):
    self.transform_pos = functions.make_position(0, 0, 0)
    self.transform_quat = functions.make_identity_quaternion()
    self.has_joint = False
    self.joint_name = "joint"
    self.joint_pos = functions.make_position(0, 0, 0)
    self.joint_axis = functions.make_position(1, 0, 0)
    self.joint_range = [0, 0]
    self.meshes = []
    self.sites = []
    self.bodies = []

  def __eq__(self, other: Body) -> bool:
    return (
        self.name == other.name
        and functions.positions_approximately_equal(
            self.transform_pos, other.transform_pos
        )
        and functions.quaternions_approximately_equal(
            self.transform_quat, other.transform_quat
        )
        and self.has_joint == other.has_joint
        and self.joint_name == other.joint_name
        and functions.positions_approximately_equal(
            self.joint_pos, other.joint_pos
        )
        and functions.positions_approximately_equal(
            self.joint_axis, other.joint_axis
        )
        and self.joint_range == other.joint_range
        and self.meshes == other.meshes
        and self.sites == other.sites
        and self.bodies == other.bodies
    )

  def to_string(self, indent: int = 0) -> str:
    """Returns a string representation of the body."""
    lines = []
    spaces = " " * indent
    lines.append(f"{spaces}<body name='{self.name}'")
    lines.append(
        f"{spaces} "
        f" pos='{self.transform_pos.px:.2f},{self.transform_pos.py:.2f},{self.transform_pos.pz:.2f}'"
    )
    lines.append(
        f"{spaces} "
        f" quat='{self.transform_quat.qx:.2f},{self.transform_quat.qy:.2f},{self.transform_quat.qz:.2f},{self.transform_quat.qw:.2f}'"
    )
    lines.append(f"{spaces}  joint_name='{self.joint_name}'")
    lines.append(
        f"{spaces} "
        f" joint_pos='{self.joint_pos.px:.2f},{self.joint_pos.py:.2f},{self.joint_pos.pz:.2f}'"
    )
    lines.append(
        f"{spaces} "
        f" joint_axis='{self.joint_axis.px:.2f},{self.joint_axis.py:.2f},{self.joint_axis.pz:.2f}'"
    )
    lines.append(
        f"{spaces} "
        f" joint_range='{self.joint_range[0]:.2f},{self.joint_range[1]:.2f}'/>"
    )
    for mesh in self.meshes:
      lines.append(
          f"{spaces}  <mesh name='{mesh.name}'"
          f" pos='{mesh.pos.px:.2f},{mesh.pos.py:.2f},{mesh.pos.pz:.2f}'"
          f" quat='{mesh.rot.qx:.2f},{mesh.rot.qy:.2f},{mesh.rot.qz:.2f},{mesh.rot.qw:.2f}'/>"
      )
    for site in self.sites:
      lines.append(
          f"{spaces}  <site name='{site.name}'"
          f" pos='{site.pos.px:.2f},{site.pos.py:.2f},{site.pos.pz:.2f}'"
          f" quat='{site.rot.qx:.2f},{site.rot.qy:.2f},{site.rot.qz:.2f},{site.rot.qw:.2f}'/>"
      )
    lines.append(f"{spaces}  nbodies: {len(self.bodies)}")
    for body in self.bodies:
      lines.append(body.to_string(indent + 2))
    lines.append(f"{spaces}/>")
    return "\n".join(lines)

  def to_proto(
      self, mesh_hashes: dict[str, bytes]
  ) -> robotics_ui_pb2.KinematicTreeRobotBody:
    """Returns a proto representation of the body."""
    body = robotics_ui_pb2.KinematicTreeRobotBody(
        name=self.name,
        position=self.transform_pos,
        rotation=self.transform_quat,
    )
    if self.has_joint:
      body.joints.CopyFrom(
          robotics_ui_pb2.KinematicTreeRobotJoint(
              name=self.joint_name,
              position=self.joint_pos,
              axis=self.joint_axis,
              min_angle_radians=self.joint_range[0],
              max_angle_radians=self.joint_range[1],
          )
      )
    for mesh in self.meshes:
      body.geometries.append(
          robotics_ui_pb2.KinematicTreeRobotGeometry(
              name=mesh.name,
              position=mesh.pos,
              rotation=mesh.rot,
              hash=mesh_hashes[mesh.name],
          )
      )
    for site in self.sites:
      body.sites.append(
          robotics_ui_pb2.KinematicTreeRobotSite(
              name=site.name,
              position=site.pos,
              rotation=site.rot,
          )
      )
    for child_body in self.bodies:
      body.children.append(child_body.to_proto(mesh_hashes))
    return body


class KinematicTree:
  """Represents a kinematic tree in the XML."""

  kinematic_tree_robot_id: str
  joint_mapping: dict[robot_frames_pb2.Frame.Enum, list[str]]
  xml_path: types.NonStrPathLike
  mujoco_model: mujoco.MjModel
  mesh_paths: dict[str, types.ResourceLocator]
  obj_counter: int
  bodies: list[Body]

  def __init__(
      self,
      kinematic_tree_robot_id: str,
      xml_path: types.NonStrPathLike,
      joint_mapping: dict[robot_frames_pb2.Frame.Enum, list[str]],
      mujoco_model: mujoco.MjModel | None = None,
  ):
    self.kinematic_tree_robot_id = kinematic_tree_robot_id
    self.joint_mapping = joint_mapping
    if isinstance(xml_path, str):
      self.xml_path = pathlib.Path(xml_path)
    else:
      self.xml_path = xml_path
    self.mesh_paths = {}
    self.obj_counter = 0
    self.bodies = []
    self.mujoco_model = mujoco_model or mujoco.MjModel()

  @classmethod
  def parse(
      cls,
      kinematic_tree_robot_id: str,
      xml_path: types.PathLike,
      joint_mapping: dict[robot_frames_pb2.Frame.Enum, list[str]],
      origin_site: types.BodySiteSpec | None = None,
      embody_site: types.BodySiteSpec | None = None,
  ) -> KinematicTree:
    """Parses the kinematic tree from the XML file."""
    if isinstance(xml_path, str):
      path = xml_path
    elif isinstance(xml_path, pathlib.Path):
      path = str(xml_path)
    else:
      raise ValueError(f"Unsupported path type: {type(xml_path)}")

    try:
      mujoco_model = mujoco.MjModel.from_xml_path(path)
    except ValueError as e:
      raise exceptions.KinematicTreeRobotUploadError(
          f"Failed to parse mujoco XML file at {xml_path}"
      ) from e

    tree = KinematicTree(
        kinematic_tree_robot_id,
        pathlib.Path(xml_path),
        joint_mapping,
        mujoco_model,
    )
    tree._gather_all_kinematic_trees_v2()
    tree._validate_joint_mapping()
    if origin_site is not None:
      tree._add_site("Origin Point", origin_site)
    if embody_site is not None:
      tree._add_site("Embody Point", embody_site)
    return tree

  @classmethod
  def _get_joint_mapping(
      cls, xml_path: str
  ) -> dict[robot_frames_pb2.Frame.Enum, list[str]]:
    """Returns the joint mapping for the given XML file."""
    joint_mapping_path = xml_path[:-4] + "_joint_mapping.json"
    try:
      with open(joint_mapping_path, "r", encoding="utf-8") as f:
        joint_json = json.load(f)
    except ValueError as e:
      raise exceptions.KinematicTreeRobotUploadError(
          f"Failed to parse joint mapping file at {joint_mapping_path}"
      ) from e

    joint_mapping = {}
    for frame, joint_names in joint_json.items():
      joint_mapping[robot_frames_pb2.Frame.Enum.Value(frame)] = joint_names
    return joint_mapping

  @classmethod
  def _get_sites(cls, xml_path: str) -> dict[str, types.BodySiteSpec]:
    """Returns the sites from the zip file."""
    sites_path = xml_path[:-4] + "_sites.json"
    try:
      with open(sites_path, "r", encoding="utf-8") as f:
        sites_json = json.load(f)
    except ValueError as e:
      raise exceptions.KinematicTreeRobotUploadError(
          f"Failed to parse sites file at {sites_path}"
      ) from e

    sites = {}
    for site_name, site_json in sites_json.items():
      if "body" not in site_json:
        raise exceptions.KinematicTreeRobotUploadError(
            f"Site {site_name} does not have a body."
        )
      site_body = site_json["body"]
      site_pos = functions.make_position(0, 0, 0)
      site_rot = functions.make_identity_quaternion()
      if "pos" in site_json:
        site_pos = functions.make_position(
            x=site_json["pos"][0],
            y=site_json["pos"][1],
            z=site_json["pos"][2],
        )
      if "rot" in site_json:
        site_rot = functions.make_quaternion(
            qw=site_json["rot"][0],
            qx=site_json["rot"][1],
            qy=site_json["rot"][2],
            qz=site_json["rot"][3],
        )
      sites[site_name] = types.BodySiteSpec(
          body=site_body, pos=site_pos, rot=site_rot
      )
    return sites

  @classmethod
  def parse_from_zip(
      cls,
      kinematic_tree_robot_id: str,
      zip_path: str | pathlib.Path,
      xml_path: str,
  ) -> KinematicTree:
    """Parses the kinematic tree from a zip file.

    The zip file must contain the mujoco XML file, all the assets, and a
    joint mapping file.

    Args:
      kinematic_tree_robot_id: The ID of the kinematic tree robot.
      zip_path: The path to the zip file containing the kinematic tree robot.
      xml_path: The path to the mujoco XML file inside the zip file.

    Returns:
      The kinematic tree robot.
    """
    try:
      with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_path) as zip_file:
          zip_file.extractall(temp_dir)
        xml_path_from_zip = temp_dir + "/" + xml_path
        joint_mapping = cls._get_joint_mapping(xml_path_from_zip)
        sites = cls._get_sites(xml_path_from_zip)

        origin_site = None
        if "Origin Point" in sites:
          origin_site = sites["Origin Point"]
        embody_site = None
        if "Embody Point" in sites:
          embody_site = sites["Embody Point"]
        return cls.parse(
            kinematic_tree_robot_id,
            xml_path_from_zip,
            joint_mapping,
            origin_site,
            embody_site,
        )

    except FileNotFoundError as e:
      raise exceptions.KinematicTreeRobotUploadError(
          f"Failed to open ZIP file at {zip_path} (not found)"
      ) from e

  def _gather_all_kinematic_trees_v2(self) -> None:
    """Returns all kinematic trees in the XML file."""
    bodies = self._parse_kinematic_tree_v2()
    nbody = self.mujoco_model.nbody
    root_body_ids = set(
        self.mujoco_model.body_rootid[i].item() for i in range(nbody)
    ) - set(
        [0]
    )  # Do not count the world body.
    # Only keep the root bodies.
    self.bodies = list([bodies[i] for i in root_body_ids])

  def _parse_kinematic_tree_v2(self) -> list[Body]:
    """Parses the kinematic tree from the XML file into a list of bodies."""
    nbody = self.mujoco_model.nbody
    bodies: list[Body] = list([self._make_mujoco_body(i) for i in range(nbody)])
    self._populate_mujoco_joints(bodies)
    self._populate_mujoco_geoms(bodies)
    self._populate_mujoco_sites(bodies)
    self._link_mujoco_bodies(bodies)
    return bodies

  def _add_hinge_joint(self, body: Body, joint_idx: int) -> None:
    """Adds a hinge joint to the body."""
    if body.has_joint:
      logging.warning("  body %s already has a joint; skipping", body.name)
      return

    body.has_joint = True
    body.is_supported_joint = True
    name_idx = self.mujoco_model.name_jntadr[joint_idx]
    name = self._get_mujoco_name(name_idx)
    if not name:
      name = f"joint{self.obj_counter}"
      self.obj_counter += 1
    body.joint_name = name

    pos_x = self.mujoco_model.jnt_pos[joint_idx].item(0)
    pos_y = self.mujoco_model.jnt_pos[joint_idx].item(1)
    pos_z = self.mujoco_model.jnt_pos[joint_idx].item(2)
    body.joint_pos = functions.make_position(pos_x, pos_y, pos_z)

    axis_x = self.mujoco_model.jnt_axis[joint_idx].item(0)
    axis_y = self.mujoco_model.jnt_axis[joint_idx].item(1)
    axis_z = self.mujoco_model.jnt_axis[joint_idx].item(2)
    body.joint_axis = functions.make_position(axis_x, axis_y, axis_z)

    range_min = self.mujoco_model.jnt_range[joint_idx].item(0)
    range_max = self.mujoco_model.jnt_range[joint_idx].item(1)
    body.joint_range = [range_min, range_max]

  def _add_nonhinge_joint(self, body: Body, joint_idx: int) -> None:
    """Adds a non-hinge joint to the body."""
    if body.has_joint:
      logging.warning("  body %s already has a joint; skipping", body.name)
      return

    body.has_joint = True
    body.is_supported_joint = False
    name_idx = self.mujoco_model.name_jntadr[joint_idx]
    name = self._get_mujoco_name(name_idx)
    if not name:
      name = f"joint{self.obj_counter}"
      self.obj_counter += 1
    body.joint_name = name

    pos_x = self.mujoco_model.jnt_pos[joint_idx].item(0)
    pos_y = self.mujoco_model.jnt_pos[joint_idx].item(1)
    pos_z = self.mujoco_model.jnt_pos[joint_idx].item(2)
    body.joint_pos = functions.make_position(pos_x, pos_y, pos_z)
    body.joint_axis = functions.make_position(0, 0, 0)
    body.joint_range = [0, 0]

  def _populate_mujoco_joints(self, bodies: list[Body]) -> None:
    """Populates the joints in the mujoco model."""
    njnt = self.mujoco_model.njnt
    for i in range(njnt):
      body_id = self.mujoco_model.jnt_bodyid[i]
      body = bodies[body_id]

      joint_type = self.mujoco_model.jnt_type[i]
      if joint_type == mujoco.mjtJoint.mjJNT_FREE.value:
        logging.info(
            "  unsupported joint_type for body %s is free; skipping", body.name
        )
        continue

      if joint_type != mujoco.mjtJoint.mjJNT_HINGE.value:
        logging.info(
            "  unsupported joint_type for body %s not hinge: %s; skipping",
            body.name,
            str(joint_type),
        )
        self._add_nonhinge_joint(body, i)
        continue

      self._add_hinge_joint(body, i)

  def _populate_mujoco_geoms(self, bodies: list[Body]) -> None:
    """Populates the geoms in the mujoco model."""
    ngeom = self.mujoco_model.ngeom

    for i in range(ngeom):
      body_id = self.mujoco_model.geom_bodyid[i]
      body = bodies[body_id]

      # If the body is parented to something with an unsupported joint, then
      # we skip all the geoms in that body.
      if body.has_joint and not body.is_supported_joint:
        logging.info(
            "  body %s has an unsupported joint; skipping its geoms", body.name
        )
        continue

      geom_type = self.mujoco_model.geom_type[i]
      if geom_type != mujoco.mjtGeom.mjGEOM_MESH.value:
        logging.info(
            "  geom_type for body %s not mesh: %s; skipping",
            body.name,
            str(geom_type),
        )
        continue

      mesh_id = self.mujoco_model.geom_dataid[i].item()
      if mesh_id == -1:
        logging.info("  mesh geom has no mesh???; skipping")
        continue

      mesh_pathadr = self.mujoco_model.mesh_pathadr[mesh_id]
      mesh_path = self._get_mujoco_path(mesh_pathadr)

      # We use the mesh name as the name of the geom rather than the geom name.
      mesh_nameadr = self.mujoco_model.name_meshadr[mesh_id]
      name = self._get_mujoco_name(mesh_nameadr)
      if not name:
        name = f"geom{self.obj_counter}"
        self.obj_counter += 1

      pos_x = self.mujoco_model.geom_pos[i].item(0)
      pos_y = self.mujoco_model.geom_pos[i].item(1)
      pos_z = self.mujoco_model.geom_pos[i].item(2)

      quat_w = self.mujoco_model.geom_quat[i].item(0)
      quat_x = self.mujoco_model.geom_quat[i].item(1)
      quat_y = self.mujoco_model.geom_quat[i].item(2)
      quat_z = self.mujoco_model.geom_quat[i].item(3)

      scale_x = self.mujoco_model.mesh_scale[mesh_id].item(0)
      scale_y = self.mujoco_model.mesh_scale[mesh_id].item(1)
      scale_z = self.mujoco_model.mesh_scale[mesh_id].item(2)
      if scale_x != scale_y or scale_y != scale_z:
        logging.info(
            "  mesh %s has non-uniform scale; skipping",
            name,
        )
        continue

      mesh = self._get_mujoco_mesh(mesh_id)
      proto = robotics_ui_pb2.WireTriangleFormat(
          vertices=mesh.vertices,
          triangles=mesh.triangles,
      )
      self.mesh_paths[name] = types.ResourceLocator(
          scheme="mesh", path=mesh_path, data=proto.SerializeToString()
      )

      body.meshes.append(
          MeshSpec(
              name=name,
              pos=functions.make_position(pos_x, pos_y, pos_z),
              rot=functions.make_quaternion(
                  qw=quat_w, qx=quat_x, qy=quat_y, qz=quat_z
              ),
              scale=scale_x,
          )
      )

  def _get_mujoco_mesh(self, mesh_id: int) -> stl_parser.Mesh:
    """Returns the mesh data for a Mujoco mesh ID."""
    mesh = stl_parser.Mesh()

    vert_offset = self.mujoco_model.mesh_vertadr[mesh_id]
    nverts = self.mujoco_model.mesh_vertnum[mesh_id]
    face_offset = self.mujoco_model.mesh_faceadr[mesh_id]
    nfaces = self.mujoco_model.mesh_facenum[mesh_id]

    # mesh_vert is a list of numpy arrays, each of shape (3,)
    vert_data = self.mujoco_model.mesh_vert[vert_offset : vert_offset + nverts]
    # mesh_face is a list of numpy arrays, each of shape (3,)
    face_data = self.mujoco_model.mesh_face[face_offset : face_offset + nfaces]

    expanded_faces: list[float] = vert_data[face_data].flatten().tolist()

    for i in range(0, len(expanded_faces), 9):
      verts = expanded_faces[i : i + 9]
      vertex0 = stl_parser.Vertex(px=verts[0], py=verts[1], pz=verts[2])
      vertex1 = stl_parser.Vertex(px=verts[3], py=verts[4], pz=verts[5])
      vertex2 = stl_parser.Vertex(px=verts[6], py=verts[7], pz=verts[8])
      mesh.add_triangle((vertex0, vertex1, vertex2))

    return mesh

  def _populate_mujoco_sites(self, bodies: list[Body]) -> None:
    """Populates the sites in the mujoco model."""
    nsite = self.mujoco_model.nsite
    for i in range(nsite):
      body_id = self.mujoco_model.site_bodyid[i]
      body = bodies[body_id]

      name_idx = self.mujoco_model.name_siteadr[i]
      name = self._get_mujoco_name(name_idx)
      if not name:
        name = f"site{self.obj_counter}"
        self.obj_counter += 1

      pos_x = self.mujoco_model.site_pos[i].item(0)
      pos_y = self.mujoco_model.site_pos[i].item(1)
      pos_z = self.mujoco_model.site_pos[i].item(2)

      quat_w = self.mujoco_model.site_quat[i].item(0)
      quat_x = self.mujoco_model.site_quat[i].item(1)
      quat_y = self.mujoco_model.site_quat[i].item(2)
      quat_z = self.mujoco_model.site_quat[i].item(3)

      body.sites.append(
          SiteSpec(
              name=name,
              pos=functions.make_position(pos_x, pos_y, pos_z),
              rot=functions.make_quaternion(
                  qw=quat_w, qx=quat_x, qy=quat_y, qz=quat_z
              ),
          )
      )

  def _link_mujoco_bodies(self, bodies: list[Body]) -> None:
    """Links the mujoco bodies."""
    nbody = self.mujoco_model.nbody
    for i in range(nbody):
      body = bodies[i]
      parent_body_id = self.mujoco_model.body_parentid[i]
      # Body ID 0 is the world, which we don't keep track of.
      if not parent_body_id:
        continue
      parent_body = bodies[parent_body_id]
      parent_body.bodies.append(body)

  def _get_mujoco_name(self, name_idx: int) -> str:
    """Returns the name of a mujoco object."""
    z = self.mujoco_model.names.find(b"\x00", name_idx)
    return self.mujoco_model.names[name_idx:z].decode("utf-8")

  def _get_mujoco_path(self, path_idx: int) -> str:
    """Returns the name of a mujoco object."""
    z = self.mujoco_model.paths.find(b"\x00", path_idx)
    return self.mujoco_model.paths[path_idx:z].decode("utf-8")

  def _make_mujoco_body(self, body_id: int) -> Body:
    """Makes a Body object from a Mujoco body ID."""
    body = Body()
    name_idx = self.mujoco_model.name_bodyadr[body_id]
    name = self._get_mujoco_name(name_idx)

    if not name:
      name = f"body{self.obj_counter}"
      self.obj_counter += 1
    body.name = name

    pos_x = self.mujoco_model.body_pos[body_id].item(0)
    pos_y = self.mujoco_model.body_pos[body_id].item(1)
    pos_z = self.mujoco_model.body_pos[body_id].item(2)

    body.transform_pos = functions.make_position(pos_x, pos_y, pos_z)

    quat_w = self.mujoco_model.body_quat[body_id].item(0)
    quat_x = self.mujoco_model.body_quat[body_id].item(1)
    quat_y = self.mujoco_model.body_quat[body_id].item(2)
    quat_z = self.mujoco_model.body_quat[body_id].item(3)

    body.transform_quat = functions.make_quaternion(
        qw=quat_w, qx=quat_x, qy=quat_y, qz=quat_z
    )
    return body

  def _gather_joint_names(self, body: Body) -> set[str]:
    """Gathers all joint names from a body and its children."""
    joint_names = set()
    if body.joint_name:
      joint_names.add(body.joint_name)
    for child_body in body.bodies:
      joint_names.update(self._gather_joint_names(child_body))
    return joint_names

  def _validate_joint_mapping(self) -> None:
    """Validates the joint mapping."""
    # Gather all joint names from bodies.
    joint_name_set = set()
    for body in self.bodies:
      joint_name_set.update(self._gather_joint_names(body))

    # Ensure that all joint names in the mapping are present in the XML file.
    for _, joint_names in self.joint_mapping.items():
      for joint_name in joint_names:
        if joint_name not in joint_name_set:
          raise exceptions.KinematicTreeRobotUploadError(
              f"Joint {joint_name} not found in XML file"
          )

  def find_body_by_name(
      self, name: str, start_body: Body | None = None
  ) -> Body | None:
    """Finds the body with the given name."""
    if start_body is not None and start_body.name == name:
      return start_body

    children = start_body.bodies if start_body is not None else self.bodies
    for child_body in children:
      body = self.find_body_by_name(name, child_body)
      if body is not None:
        return body
    return None

  def _add_site(self, name: str, body_site: types.BodySiteSpec) -> None:
    """Adds the body site to the kinematic tree."""
    body = self.find_body_by_name(body_site.body)
    if body is None:
      raise exceptions.KinematicTreeRobotUploadError(
          f"Body {body_site.body} for site {name} not found in XML file"
      )
    body.sites.append(SiteSpec(name=name, pos=body_site.pos, rot=body_site.rot))


class UploadRobotJob(threading.Thread):
  """Represents a single mujoco-based robotupload job."""

  framework: IFramework
  upload_timeout: datetime.timedelta
  kinematic_tree: KinematicTree
  all_resources_uploaded: threading.Event
  locator_to_hash: dict[types.ResourceLocatorKey, bytes]
  mesh_locator_to_name: dict[types.ResourceLocatorKey, str]
  mesh_name_to_hash: dict[str, bytes]

  def __init__(
      self,
      framework: IFramework,
      upload_timeout: datetime.timedelta,
      kinematic_tree: KinematicTree,
  ):
    super().__init__(name="UploadRobotJob", daemon=True)
    self.framework = framework
    self.upload_timeout = upload_timeout
    self.kinematic_tree = kinematic_tree
    self.all_resources_uploaded = threading.Event()
    # Map from mesh path to hash.
    self.locator_to_hash = {}
    # Map from mesh path to mesh name.
    self.mesh_locator_to_xml_name = {}
    # Map from mesh name to hash.
    self.mesh_xml_name_to_hash = {}

  def resource_uploaded(
      self, locator: types.ResourceLocator, hash_: bytes
  ) -> None:
    """Callback for when a resource is confirmed as uploaded.

    Sets all_resources_uploaded if all the files that we need have been
    uploaded.

    Args:
      locator: The locator of the resource that was uploaded.
      hash_: The hash of the file that was uploaded.
    """
    logging.debug("Resource uploaded: %s:%s", locator.scheme, locator.path)
    self.locator_to_hash[locator.key()] = hash_
    self.mesh_xml_name_to_hash[self.mesh_locator_to_xml_name[locator.key()]] = (
        hash_
    )
    if all(hash_ for hash_ in self.locator_to_hash.values()):
      self.all_resources_uploaded.set()

  def _upload_and_await_uploaded(
      self, meshes: dict[str, types.ResourceLocator]
  ) -> bool:
    """Uploads all resources referenced in the mujoco XML file.

    Args:
      meshes: A dictionary of mesh names to locators.

    Returns:
      True if all resource were uploaded before the timeout expired, False
      otherwise.
    """
    if not meshes:
      return True

    self.mesh_locator_to_xml_name = {
        locator.key(): name for name, locator in meshes.items()
    }
    self.locator_to_hash = {locator.key(): b"" for locator in meshes.values()}

    self.framework.add_resource_upload_listener(self.resource_uploaded)
    start_time_ns = time.time_ns()
    try:
      for locator in meshes.values():
        self.framework.upload_resource(locator)
      done = self.all_resources_uploaded.wait(
          timeout=self.upload_timeout.total_seconds()
      )
    finally:
      self.framework.remove_resource_upload_listener(self.resource_uploaded)

    upload_time_ns = time.time_ns() - start_time_ns
    logging.info(
        "Done waiting for uploads: %s, %d msec",
        done,
        upload_time_ns // 1000_000,
    )
    return done

  def run(self):
    """Uploads all files referenced in the mujoco XML file."""
    meshes = self.kinematic_tree.mesh_paths
    if not self._upload_and_await_uploaded(meshes):
      return  # Timed out waiting for uploads.

    joint_mapping = robotics_ui_pb2.KinematicTreeRobotJointMapping()
    for frame, joint_names in self.kinematic_tree.joint_mapping.items():
      joint_mapping.joint_mapping[frame].joint_names.extend(joint_names)

    request = robotics_ui_pb2.UploadKinematicTreeRobotRequest(
        kinematic_tree_robot_id=self.kinematic_tree.kinematic_tree_robot_id,
        bodies=[
            body.to_proto(self.mesh_xml_name_to_hash)
            for body in self.kinematic_tree.bodies
        ],
        joint_mapping=joint_mapping,
    )

    logging.info(
        "Assembling kinematic tree robot %s",
        self.kinematic_tree.kinematic_tree_robot_id,
    )
    self.framework.send_raw_message(
        robotics_ui_pb2.RuiMessage(
            ui_message=robotics_ui_pb2.UIMessage(
                upload_kinematic_tree_robot_request=request
            )
        )
    )
