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

"""Image-related classes."""

import time

import imageio

from safari_sdk.protos.ui import robot_state_pb2
from safari_sdk.protos.ui import robot_types_pb2


class JpegCameraImageData:
  """A class that holds the data for a jpeg-encoded camera image."""

  jpeg_image: bytes
  cols: int
  rows: int
  sensor_id: int | None
  sample_timestamp_nsec: int
  seq: int

  def __init__(
      self,
      jpeg_image: bytes,
      cols: int = 0,
      rows: int = 0,
      sensor_id: int | None = None,
      sample_timestamp_nsec: int = 0,
      seq: int = 0,
  ):
    """Initializes a JpegCameraImageData instance.

    Args:
      jpeg_image: The JPEG-encoded data.
      cols: The width of the image in pixels. If not given, the RoboticsUI will
        decode the image and its size will be determined.
      rows: The height of the image in pixels. If not given, the RoboticsUI will
        decode the image and its size will be determined.
      sensor_id: Identifier for which camera sensor this is. See the
        SensorHeader.sensor_id field in robot_types.proto for details. Defaults
        to camera_index.
      sample_timestamp_nsec: The timestamp of the image in nanoseconds. Defaults
        to the current time.
      seq: The sequence number of the image. Defaults to 0.
    """
    self.jpeg_image = jpeg_image
    self.cols = cols
    self.rows = rows
    self.sensor_id = sensor_id
    self.sample_timestamp_nsec = sample_timestamp_nsec
    self.seq = seq

  def construct_camera_data(self) -> robot_state_pb2.CameraImage:
    """Constructs a CameraImage proto from this JpegCameraImageData.

    If the sensor_id is left unset, the camera_index will be used when sending
    this image via send_jpeg_image(s).

    Returns:
      A CameraImage proto.
    """
    if self.sample_timestamp_nsec == 0:
      self.sample_timestamp_nsec = time.time_ns()
    pixel_type = robot_state_pb2.CameraImage.PixelType(
        compression=robot_state_pb2.CameraImage.PixelType.JPEG
    )
    if self.cols == 0 or self.rows == 0:
      self.rows, self.cols, *_ = imageio.v2.imread(self.jpeg_image).shape
    sensor_header = robot_types_pb2.SensorHeader(
        sample_timestamp_nsec=self.sample_timestamp_nsec,
        sequence_number=self.seq,
        sensor_id=self.sensor_id if self.sensor_id is not None else -1,
    )
    return robot_state_pb2.CameraImage(
        header=sensor_header,
        pixel_type=pixel_type,
        cols=self.cols,
        rows=self.rows,
        data=self.jpeg_image,
    )
