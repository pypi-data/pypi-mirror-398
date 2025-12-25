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

"""Parser for STL files into Wire Triangle Format."""

import io
import pathlib
import re
import struct
from typing import Any, IO

import lark

from safari_sdk.protos.ui import robot_types_pb2
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui.client import exceptions
from safari_sdk.ui.client import resources
from safari_sdk.ui.client import types

# If file starts with this, it's a text file, otherwise it's a binary file.
STL_MAGIC = b"solid"
NUMBER_RE = re.compile(r"([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)\s")


_STL_TEXT_GRAMMAR = r"""
  file: file_header WS* facet* file_footer
  file_header: "solid" TO_EOL
  file_footer: "endsolid" TO_EOL

  facet: facet_header loop "endfacet" WS+
  facet_header: "facet" WS+ "normal" WS+ triple
  facet_footer: "endfacet" WS+

  loop: "outer" WS+ "loop" WS+ triple_vertex "endloop" WS+
  triple_vertex: "vertex" WS+ triple "vertex" WS+ triple "vertex" WS+ triple
  triple: NUM WS+ NUM WS+ NUM WS+

  TO_EOL: /[^\n\r]*[\n\r]/
  NUM: /[-+]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][-+]?[0-9]+)?/
  WS: /[ \t\n\r]/
"""


Vertex = robot_types_pb2.Position
Triangle = robot_types_pb2.TriangleVertexIndices


class Mesh:
  """A mesh of triangles."""

  vertices: list[Vertex]
  triangles: list[Triangle]
  vertex_to_index: dict[tuple[float, float, float], int]

  def __init__(self):
    self.vertices = []
    self.triangles = []
    self.vertex_to_index = {}

  def add_triangle(self, vertices: tuple[Vertex, Vertex, Vertex]) -> None:
    """Adds a triangle to the mesh.

    Each triangle is three vertices. If a vertex is already in the mesh, the
    index of the vertex is used. Otherwise, the vertex is added to the mesh and
    its index is used.

    Vertices are rounded to six decimal places.

    Args:
      vertices: The vertices of the triangle.
    """
    indices: list[int] = []
    for vertex in vertices:
      rounded_vertex = (vertex.px, vertex.py, vertex.pz)
      if rounded_vertex not in self.vertex_to_index:
        self.vertex_to_index[rounded_vertex] = len(self.vertices)
        indices.append(len(self.vertices))
        self.vertices.append(vertex)
      else:
        indices.append(self.vertex_to_index[rounded_vertex])
    self.triangles.append(
        Triangle(index_0=indices[0], index_1=indices[1], index_2=indices[2])
    )


class StlTransformer(lark.Transformer):
  """Transformer for parsing STL files.

  Transformer functions for rules take a list of "things" and return a "thing",
  while transformer functions for terminals take a lark.Token and return a
  "thing".

  Returning lark.visitors.Discard means that the returned thing is discarded
  and will not be present in an argument's list.

  Literal strings in the grammar are discarded.

  If a function for a terminal is not defined, by default it returns its token,
  with the type set to the name of the terminal, and the value set to the text
  of the terminal.

  If a rule is not defined, by default it returns a Tree whose type is a token
  of type "RULE" with value the name of the rule, and whose value is a list of
  "things" in the rule.
  """

  mesh: Mesh

  def __init__(self):
    self.mesh = Mesh()
    print(f"Initialized StlTransformer, tris: {len(self.mesh.triangles)}")

  def file(self, _: Any) -> Any:
    return lark.visitors.Discard

  def facet(self, _: Any) -> Any:
    return lark.visitors.Discard

  def file_header(self, _: Any) -> Any:
    return lark.visitors.Discard

  def file_footer(self, _: Any) -> Any:
    return lark.visitors.Discard

  def facet_header(self, _: list[Any]) -> Any:
    return lark.visitors.Discard

  def loop(self, parts: list[tuple[Vertex, Vertex, Vertex]]) -> Any:
    vertices = parts[0]
    self.mesh.add_triangle(vertices)
    return lark.visitors.Discard

  def triple_vertex(
      self, vertices: list[Vertex]
  ) -> tuple[Vertex, Vertex, Vertex]:
    return tuple(vertices)

  def triple(self, nums: list[float]) -> Vertex:
    assert len(nums) == 3
    return Vertex(
        px=round(nums[0], 6), py=round(nums[1], 6), pz=round(nums[2], 6)
    )

  def WS(self, _: Any) -> Any:
    return lark.visitors.Discard

  def TO_EOL(self, _: Any) -> Any:
    return lark.visitors.Discard

  def NUM(self, token: lark.Token) -> float:
    return float(token)


def _parse_text_stl(f: io.TextIOBase) -> robotics_ui_pb2.WireTriangleFormat:
  r"""Parses an STL file into a list of vertices."""

  parser = lark.Lark(
      _STL_TEXT_GRAMMAR,
      start="file",
      parser="lalr",
  )
  try:
    tree = parser.parse(f.read())
    transformer = StlTransformer()
    transformer.transform(tree)
  except lark.exceptions.LarkError as e:
    raise exceptions.StlParseError("Failed to parse STL file") from e

  return robotics_ui_pb2.WireTriangleFormat(
      vertices=transformer.mesh.vertices,
      triangles=transformer.mesh.triangles,
  )


def _parse_binary_stl(
    f: IO[bytes] | io.BufferedReader,
) -> robotics_ui_pb2.WireTriangleFormat:
  """Parses an STL file into a list of vertices."""
  mesh = Mesh()

  try:
    # Number of triangles is a uint32.
    num_triangles = struct.unpack("I", f.read(4))[0]

    for _ in range(num_triangles):
      # Ignore the normal vector
      f.read(3 * 4)
      # Read the triangle, nine float32s
      data = [struct.unpack("f", f.read(4))[0] for _ in range(9)]
      # Skip the attribute byte count
      f.read(2)
      vertices = (
          Vertex(px=data[0], py=data[1], pz=data[2]),
          Vertex(px=data[3], py=data[4], pz=data[5]),
          Vertex(px=data[6], py=data[7], pz=data[8]),
      )
      mesh.add_triangle(vertices)
  except struct.error as e:
    raise exceptions.StlParseError("Failed to parse STL file") from e

  return robotics_ui_pb2.WireTriangleFormat(
      vertices=mesh.vertices,
      triangles=mesh.triangles,
  )


def parse_stl(path: types.PathLike) -> robotics_ui_pb2.WireTriangleFormat:
  """Parses an STL file into a list of vertices."""
  if isinstance(path, str):
    path = pathlib.Path(path)
  assert isinstance(path, types.NonStrPathLike)

  with path.open(mode="rb") as f:
    if f.read(5) != STL_MAGIC:
      # skip 75 bytes of header
      f.read(75)
      return _parse_binary_stl(f)
  with path.open(mode="rt") as f:
    return _parse_text_stl(f)


def parse_stl_from_locator(
    locator: robotics_ui_pb2.ResourceLocator,
) -> robotics_ui_pb2.WireTriangleFormat:
  """Parses an STL file into a list of vertices."""

  with resources.open_resource(locator) as f:
    header = f.read(5)
    if header != STL_MAGIC:
      # It's a binary STL file. Skip 75 bytes of header.
      f.read(75)
      return _parse_binary_stl(f)
    if f.seekable():
      f.seek(0)
      return _parse_text_stl(io.TextIOWrapper(f))

  # We re-open the non-seekable file.
  with resources.open_resource(locator) as f:
    return _parse_text_stl(io.TextIOWrapper(f))
