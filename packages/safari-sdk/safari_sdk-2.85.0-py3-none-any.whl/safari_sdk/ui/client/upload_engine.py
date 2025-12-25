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

"""Handles uploads for the RoboticsUI."""

import collections
import hashlib
import logging
import pathlib
import threading
from typing import Callable
import uuid

from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui.client import exceptions
from safari_sdk.ui.client import iframework
from safari_sdk.ui.client import types


class UploadEngine:
  """Handles uploads for the RoboticsUI."""

  framework: iframework.IFramework

  # List of receivers for notification of resource uploads.
  resource_upload_listeners: list[
      Callable[[types.ResourceLocator, bytes], None]
  ]
  resource_upload_listeners_lock: threading.Lock
  pending_uploads: dict[bytes, list[types.ResourceLocator]]
  pending_uploads_lock: threading.Lock

  # For testing.
  _object_data_supplier: Callable[[types.PathLike], bytes] | None

  def __init__(
      self,
      framework: iframework.IFramework,
      object_data_supplier: Callable[[types.PathLike], bytes] | None = None,
  ):
    self.framework = framework
    self.resource_upload_listeners = []
    self.resource_upload_listeners_lock = threading.Lock()
    self.pending_uploads = collections.defaultdict(list)
    self.pending_uploads_lock = threading.Lock()

    if object_data_supplier is None:
      self._object_data_supplier = self._read_file
    else:
      self._object_data_supplier = object_data_supplier

  def _read_file(self, path: types.PathLike) -> bytes:
    """Reads a file from the local disk."""
    if isinstance(path, str):
      path = pathlib.Path(path)
    assert isinstance(path, types.NonStrPathLike)
    with path.open("rb") as f:
      return f.read()

  def add_resource_upload_listener(
      self, receiver: Callable[[types.ResourceLocator, bytes], None]
  ) -> None:
    """Adds a receiver for file uploads."""
    with self.resource_upload_listeners_lock:
      self.resource_upload_listeners.append(receiver)

  def remove_resource_upload_listener(
      self, receiver: Callable[[types.ResourceLocator, bytes], None]
  ) -> None:
    """Removes a receiver for file uploads."""
    with self.resource_upload_listeners_lock:
      self.resource_upload_listeners.remove(receiver)

  def _notify_resource_upload_listeners(
      self, locator: types.ResourceLocator, hash_: bytes
  ) -> None:
    """Notifies all file upload listeners of a file upload."""
    with self.resource_upload_listeners_lock:
      for listener in self.resource_upload_listeners:
        listener(locator, hash_)

  def _check_resource_cache(
      self, locator: types.ResourceLocator, hash_: bytes
  ) -> str:
    """Checks whether the hash of the resource is in the RoboticsUI cache.

    Args:
      locator: The resource locator of the resource to check.
      hash_: The SHA256 hash of the resource data to check.

    Returns:
      The message ID of the sent message.

    The response is automatically handled to get the resource and upload its
    data if not already in the cache.
    """
    with self.pending_uploads_lock:
      # It's possible for two locators to have the same hash, so we need to keep
      # track of all the locators that correspond to the same hash.
      self.pending_uploads[hash_].append(locator)
    return self.framework.send_raw_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                check_file_cache_request=robotics_ui_pb2.CheckFileCacheRequest(
                    hash=hash_,
                )
            ),
        )
    )

  def _upload_data_resource(self, data: bytes) -> None:
    """Uploads data into the RoboticsUI cache."""
    hash_ = hashlib.sha256(data).digest()
    self.framework.send_raw_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                upload_file_request=robotics_ui_pb2.UploadFileRequest(
                    hash=hash_,
                    data=data,
                )
            ),
        )
    )

  def _upload_mesh_resource(self, locator: types.ResourceLocator) -> None:
    """Uploads a mesh resource into the RoboticsUI cache."""
    hash_ = hashlib.sha256(locator.data).digest()
    mesh = robotics_ui_pb2.WireTriangleFormat()
    mesh.ParseFromString(locator.data)
    self.framework.send_raw_message(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.uuid4()),
            ui_message=robotics_ui_pb2.UIMessage(
                upload_file_request=robotics_ui_pb2.UploadFileRequest(
                    hash=hash_,
                    wire_triangle_format=mesh,
                )
            ),
        )
    )

  def _upload_resource(self, locator: types.ResourceLocator) -> None:
    """Uploads a resource into the RoboticsUI cache."""
    if locator.scheme == "file":
      self._upload_data_resource(self._object_data_supplier(locator.path))
      return

    if locator.data is None:
      raise ValueError(
          f"Resource data for {locator.scheme}:{locator.path} is None"
      )

    if locator.scheme == "mesh":
      self._upload_mesh_resource(locator)
      return

    self._upload_data_resource(locator.data)

  def handle_check_resource_cache_response(
      self,
      _: str,
      ui_message: robotics_ui_pb2.UIMessage,
  ) -> None:
    """Handles a CheckObjectCacheResponse."""
    response = ui_message.check_file_cache_response

    # If the locator is not pending, then either we've already uploaded it, or
    # it was never pending in the first place. In either case, we don't need to
    # do anything -- and we don't know what locators to use anyway.
    with self.pending_uploads_lock:
      if response.hash not in self.pending_uploads:
        return
      locators = self.pending_uploads.pop(response.hash)

    # We only need to upload one of the locators, since they have the same hash.
    # This assumption breaks if the data of the locator is modified between the
    # upload request and the cache response, but such modification is not
    # supported by the RoboticsUI, and leads to undefined behavior.
    first_locator = locators[0]

    if not response.in_cache:
      self._upload_resource(first_locator)

    # Strictly speaking, if _upload_resource() was called, the resource hasn't
    # yet been uploaded. But because we send out messages in a queue, anything
    # that the client does after this only takes effect in the RoboticsUI after
    # the RoboticsUI has processed the upload resource request. Therefore, it is
    # safe to tell the client that the resource(s) are uploaded.
    for locator in locators:
      nondata_locator = types.ResourceLocator(
          scheme=locator.scheme, path=locator.path
      )
      self._notify_resource_upload_listeners(nondata_locator, response.hash)
      self.framework.get_callbacks().resource_uploaded(
          nondata_locator, response.hash
      )

  def upload_file(self, path: types.PathLike) -> str:
    """Uploads a file resource into the RoboticsUI cache."""
    locator = types.ResourceLocator(scheme="file", path=path)
    try:
      data = self._object_data_supplier(path)
      hash_ = hashlib.sha256(data).digest()
      return self._check_resource_cache(locator, hash_)
    except FileNotFoundError as e:
      raise exceptions.FileUploadError(
          f"Failed to upload file at {path} (not found)"
      ) from e

  def upload_resource(self, locator: types.ResourceLocator) -> str:
    """Uploads a resource into the RoboticsUI cache.

    If the resource is not of scheme "file", then the data must be provided in
    the locator.

    Args:
      locator: The resource locator of the resource to upload.

    Returns:
      The message ID of the sent message.
    """
    if locator.scheme == "file":
      return self.upload_file(locator.path)
    if locator.data is None:
      raise exceptions.FileUploadError(
          f"Resource data for {locator} cannot be None"
      )
    logging.debug(
        "Uploading resource: %s, length %d", locator, len(locator.data)
    )
    hash_ = hashlib.sha256(locator.data).digest()
    return self._check_resource_cache(locator, hash_)
