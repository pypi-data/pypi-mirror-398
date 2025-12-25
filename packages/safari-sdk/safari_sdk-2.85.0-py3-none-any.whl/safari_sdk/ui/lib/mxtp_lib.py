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

"""Library for parsing MVN Xsens streaming data.

https://www.xsens.com/hubfs/Downloads/Manuals/MVN_real-time_network_streaming_protocol_specification.pdf
"""


import dataclasses
import struct
from typing import Any, Callable
import immutabledict

from safari_sdk.protos.ui import robot_types_pb2

immutabledict = immutabledict.immutabledict

HEADER_SIZE = 24
MESSAGE_SIZE: immutabledict[str, int] = immutabledict({
    "01": 28,
    "02": 32,
    "20": 20,
    "24": 12,
})
SEGMENT_NAMES = [
    "Pelvis", "L5", "L3", "T12", "T8", "Neck", "Head", "Right Shoulder",
    "Right Upper Arm", "Right Forearm", "Right Hand", "Left Shoulder",
    "Left Upper Arm", "Left Forearm", "Left Hand", "Right Upper Leg",
    "Right Lower Leg", "Right Foot", "Right Toe", "Left Upper Leg",
    "Left Lower Leg", "Left Foot", "Left Toe"]


def segment_name_to_id(segment_name: str) -> int:
  """Converts a segment name to ID.

  Args:
    segment_name: The segment name to convert.

  Returns:
    The segment ID which starts from 1.
  """
  return SEGMENT_NAMES.index(segment_name) + 1


def segment_id_to_name(segment_id: int) -> str:
  """Converts a segment ID to name."""
  return SEGMENT_NAMES[segment_id - 1]


@dataclasses.dataclass
class XsensHeader:
  """Represents the header of an Xsens message. Size is 24 bytes.

  6 bytes ID String, i.e. MXTP01, where 01 is the message type
  4 bytes sample counter
  1 byte datagram counter
  1 byte number of items
  4 bytes time code
  1 byte character ID
  1 byte number of body segments – from MVN 2019
  1 byte number of props – from MVN 2019
  1 byte number of finger tracking data segments – from MVN 2019
  2 bytes reserved for future use
  2 bytes size of payload
  """
  id_string: str
  message_id: str
  sample_counter: int
  datagram_counter: int
  number_of_items: int
  time_code: str
  character_id: int
  number_body_segments: int
  number_props: int
  number_finger_segments: int
  reserved: int
  payload_size: int


@dataclasses.dataclass
class SegmentDataEuler:
  """Pose data in Position. Size is 28 bytes.

  The coordinates use a Y-Up, right-handed coordinate system for Euler protocol.
  4 bytes segment ID See 2.5.9
  4 bytes x–coordinate of segment position
  4 bytes y–coordinate of segment position
  4 bytes z–coordinate of segment position
  4 bytes x rotation –coordinate of segment rotation
  4 bytes y rotation –coordinate of segment rotation
  4 bytes z rotation –coordinate of segment rotation
  """
  segment_id: int
  x: float
  y: float
  z: float
  rx: float
  ry: float
  rz: float


@dataclasses.dataclass
class SegmentDataQuaternion:
  """Pose data in Quaternion. Size is 32 bytes.

  Absolute position and orientation (Quaternion) of segments.
  Default mode Z-Up, right-handed or Y-Up.
  4 bytes segment ID See 2.5.9
  4 bytes x–coordinate of segment position in cm.
  4 bytes y–coordinate of segment position in cm.
  4 bytes z–coordinate of segment position in cm.
  4 bytes q1 rotation – segment rotation quaternion component 1 (re)
  4 bytes q2 rotation – segment rotation quaternion component 1 (i)
  4 bytes q3 rotation – segment rotation quaternion component 1 (j)
  4 bytes q4 rotation – segment rotation quaternion component 1 (k)
  """
  segment_id: int
  x: float
  y: float
  z: float
  re: float
  i: float
  j: float
  k: float


@dataclasses.dataclass
class JointAngle:
  """Joint angle data. Size is 20 bytes.

  The coordinates use a Z-Up, right-handed coordinate system.
  4 bytes point ID of parent segment connection. See 2.5.10
  4 bytes point ID of child segment connection. See 2.5.10
  4 bytes floating point rotation around segment x–axis
  4 bytes floating point rotation around segment y–axis
  4 bytes floating point rotation around segment z–axis
  """
  parent_id: int
  child_id: int
  rot_x: float
  rot_y: float
  rot_z: float


def point_id_to_name(point_id: int) -> str:
  """Converts a point ID to joint name.

  point ID = 256 * segment ID + local point ID
  TODO: Apply local point ID (point_id % 256) to joint name mapping.
  Args:
    point_id: The point ID to convert.

  Returns:
    The joint name corresponding to the point ID.
  """
  segment_id = point_id // 256
  return SEGMENT_NAMES[segment_id - 1]


class MxtpParser:
  """Parses MVN Xsens streaming data."""
  # Maps message ID to parser function.
  parsers: dict[str, Callable[[bytes], Any]]

  def __init__(self):
    self.parsers = {
        "01": self._parse_segment_data_euler,
        "02": self._parse_segment_data_quaternion,
        "20": self._parse_joint_angle,
        "24": self._parse_center_of_mass,
    }

  def _parse_xsens_header(self, header: bytes) -> XsensHeader:
    """Parses an Xsens header.

    Args:
      header: The raw bytes of the Xsens header.

    Returns:
      The parsed Xsens header.
    """
    id_string = header[0:6].decode("utf-8")
    return XsensHeader(
        id_string=id_string,
        message_id=id_string[4:6],
        sample_counter=struct.unpack(">I", header[6:10])[0],
        datagram_counter=struct.unpack(">B", header[10:11])[0],
        number_of_items=struct.unpack(">B", header[11:12])[0],
        time_code=struct.unpack(">I", header[12:16])[0],
        character_id=struct.unpack(">B", header[16:17])[0],
        number_body_segments=struct.unpack(">B", header[17:18])[0],
        number_props=struct.unpack(">B", header[18:19])[0],
        number_finger_segments=struct.unpack(">B", header[19:20])[0],
        reserved=struct.unpack(">H", header[20:22])[0],
        payload_size=struct.unpack(">H", header[22:24])[0],
    )

  def _parse_segment_data_euler(
      self, segment: bytes) -> SegmentDataEuler:
    """Parses an Xsens segment euler data."""
    return SegmentDataEuler(
        segment_id=struct.unpack(">I", segment[0:4])[0],
        x=struct.unpack(">f", segment[4:8])[0],
        y=struct.unpack(">f", segment[8:12])[0],
        z=struct.unpack(">f", segment[12:16])[0],
        rx=struct.unpack(">f", segment[16:20])[0],
        ry=struct.unpack(">f", segment[20:24])[0],
        rz=struct.unpack(">f", segment[24:28])[0],
    )

  def _parse_segment_data_quaternion(
      self, segment: bytes) -> SegmentDataQuaternion:
    """Parses an Xsens segment quaternion data.

    Args:
      segment: The raw bytes of the Xsens segment data quaternion.

    Returns:
      The parsed Xsens segment data quaternion.
    """
    return SegmentDataQuaternion(
        segment_id=struct.unpack(">I", segment[0:4])[0],
        x=struct.unpack(">f", segment[4:8])[0],
        y=struct.unpack(">f", segment[8:12])[0],
        z=struct.unpack(">f", segment[12:16])[0],
        re=struct.unpack(">f", segment[16:20])[0],
        i=struct.unpack(">f", segment[20:24])[0],
        j=struct.unpack(">f", segment[24:28])[0],
        k=struct.unpack(">f", segment[28:32])[0],
    )

  def _parse_joint_angle(self, data: bytes) -> JointAngle:
    """Parses an Xsens joint angle data."""
    return JointAngle(
        parent_id=struct.unpack(">I", data[0:4])[0],
        child_id=struct.unpack(">I", data[4:8])[0],
        rot_x=struct.unpack(">f", data[8:12])[0],
        rot_y=struct.unpack(">f", data[12:16])[0],
        rot_z=struct.unpack(">f", data[16:20])[0],
    )

  def _parse_center_of_mass(self, data: bytes) -> robot_types_pb2.Position:
    """Parses an Xsens center of mass data."""
    return robot_types_pb2.Position(
        px=struct.unpack(">f", data[0:4])[0],
        py=struct.unpack(">f", data[4:8])[0],
        pz=struct.unpack(">f", data[8:12])[0],
    )

  def parse_header(self, data: bytes) -> XsensHeader:
    """Parses an Xsens header."""
    return self._parse_xsens_header(data[0:HEADER_SIZE])

  def parse_message(
      self, data: bytes, callback: Callable[[Any], None]) -> None:
    """Parses an Xsens message."""
    header = self._parse_xsens_header(data[0:HEADER_SIZE])
    payload = data[HEADER_SIZE:]
    message_size = MESSAGE_SIZE[header.message_id]
    num_segments = header.payload_size // message_size
    for i in range(num_segments):
      segment_data = payload[i * message_size : (i + 1) * message_size]
      segment = self.parsers[header.message_id](segment_data)
      callback(segment)

  def parse_messages(self, data: bytes) -> list[Any]:
    """Parses an Xsens message."""
    header = self._parse_xsens_header(data[0:HEADER_SIZE])
    payload = data[HEADER_SIZE:]
    message_size = MESSAGE_SIZE[header.message_id]
    num_segments = header.payload_size // message_size
    segments = []
    for i in range(num_segments):
      segment_data = payload[i * message_size : (i + 1) * message_size]
      segments.append(self.parsers[header.message_id](segment_data))
    return segments
