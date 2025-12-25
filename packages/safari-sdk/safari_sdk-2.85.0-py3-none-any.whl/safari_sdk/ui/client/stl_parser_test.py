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

"""Unit tests for stl_parser.py."""

import io
import struct
import tempfile

from absl.testing import absltest
from safari_sdk.protos.ui import robot_types_pb2
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui.client import exceptions
from safari_sdk.ui.client import functions
from safari_sdk.ui.client import stl_parser


TEST_STL = """solid argle bargle!
  facet normal 1 1 1
    outer loop
      vertex 1.1 2 3
      vertex 4 5 6
      vertex 7 8 -9.9e9
    endloop
  endfacet
  facet normal 1 1 1
    outer loop
      vertex 1.1 2 3
      vertex 4 5 6
      vertex -1 -2 -3
    endloop
  endfacet
endsolid
"""


EXPECTED_DATA = robotics_ui_pb2.WireTriangleFormat(
    vertices=[
        functions.make_position(1.1, 2, 3),
        functions.make_position(4, 5, 6),
        functions.make_position(7, 8, -9.9e9),
        functions.make_position(-1, -2, -3),
    ],
    triangles=[
        robot_types_pb2.TriangleVertexIndices(index_0=0, index_1=1, index_2=2),
        robot_types_pb2.TriangleVertexIndices(index_0=0, index_1=1, index_2=3),
    ],
)


class StlParserTest(absltest.TestCase):

  def test_text_stl(self):
    with tempfile.NamedTemporaryFile(mode="w") as file:
      file.write(TEST_STL)
      file.flush()
      actual = stl_parser.parse_stl(file.name)
    self.assertEqual(EXPECTED_DATA, actual)

  def test_text_stl_parse_failure(self):
    with tempfile.NamedTemporaryFile(mode="w") as file:
      file.write("solid\n????")
      file.flush()
      with self.assertRaises(exceptions.StlParseError):
        stl_parser.parse_stl(file.name)

  def test_binary_stl(self):
    # Setup a binary buffer which we will write to.
    buffer = io.BytesIO()
    buffer.write(bytes(80))
    # Write the number of triangles.
    buffer.write(struct.pack("I", 2))

    # First triangle
    # Write the normal vector.
    buffer.write(struct.pack("f", 1))
    buffer.write(struct.pack("f", 1))
    buffer.write(struct.pack("f", 1))
    # Vertices.
    buffer.write(struct.pack("f", 1.1))
    buffer.write(struct.pack("f", 2))
    buffer.write(struct.pack("f", 3))
    buffer.write(struct.pack("f", 4))
    buffer.write(struct.pack("f", 5))
    buffer.write(struct.pack("f", 6))
    buffer.write(struct.pack("f", 7))
    buffer.write(struct.pack("f", 8))
    buffer.write(struct.pack("f", -9.9e9))
    # Write the attribute byte count.
    buffer.write(struct.pack("h", 0))

    # Second triangle
    # Normal vector
    buffer.write(struct.pack("f", 1))
    buffer.write(struct.pack("f", 1))
    buffer.write(struct.pack("f", 1))
    # Vertices
    buffer.write(struct.pack("f", 1.1))
    buffer.write(struct.pack("f", 2))
    buffer.write(struct.pack("f", 3))
    buffer.write(struct.pack("f", 4))
    buffer.write(struct.pack("f", 5))
    buffer.write(struct.pack("f", 6))
    buffer.write(struct.pack("f", -1))
    buffer.write(struct.pack("f", -2))
    buffer.write(struct.pack("f", -3))
    # Attribute byte count
    buffer.write(struct.pack("h", 0))

    # Read the buffer back and check the result.
    buffer.seek(0)

    with tempfile.NamedTemporaryFile(mode="wb") as file:
      file.write(buffer.read())
      file.flush()
      actual = stl_parser.parse_stl(file.name)
    self.assertEqual(EXPECTED_DATA, actual)

  def test_binary_stl_file_not_found(self):
    with self.assertRaises(FileNotFoundError):
      stl_parser.parse_stl("not_found.stl")

  def test_binary_stl_file_empty(self):
    with tempfile.NamedTemporaryFile(mode="wb") as file:
      file.flush()
      with self.assertRaises(exceptions.StlParseError):
        stl_parser.parse_stl(file.name)

  def test_binary_stl_parse_failure(self):
    buffer = io.BytesIO()
    buffer.write(bytes(80))
    buffer.write(b"????")
    buffer.seek(0)
    with tempfile.NamedTemporaryFile(mode="wb") as file:
      file.write(buffer.read())
      file.flush()
      with self.assertRaises(exceptions.StlParseError):
        stl_parser.parse_stl(file.name)


if __name__ == "__main__":
  absltest.main()
