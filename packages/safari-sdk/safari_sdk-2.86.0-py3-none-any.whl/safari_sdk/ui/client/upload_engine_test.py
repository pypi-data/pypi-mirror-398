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

"""Unit tests for upload_engine.py."""

import hashlib
import pathlib
import tempfile
from unittest import mock
import uuid
import zipfile

from absl.testing import absltest
from safari_sdk.protos.ui import robotics_ui_pb2
from safari_sdk.ui.client import exceptions
from safari_sdk.ui.client import iframework
from safari_sdk.ui.client import types
from safari_sdk.ui.client import ui_callbacks
from safari_sdk.ui.client import upload_engine


TEST_FILE_DATA = b"data"
TEST_FILE_DATA_HASH = hashlib.sha256(TEST_FILE_DATA).digest()
TESTDIR = pathlib.Path(
    "safari_sdk/ui/client/testdata"
)


class UploadEngineTest(absltest.TestCase):
  fake_uuid = 0

  def _generate_fake_uuid(self) -> uuid.UUID:
    self.fake_uuid += 1
    return uuid.UUID(int=self.fake_uuid)

  def setUp(self):
    super().setUp()
    self.enter_context(
        mock.patch.object(uuid, "uuid4", autospec=True)
    ).side_effect = self._generate_fake_uuid

    self.mock_framework = mock.create_autospec(iframework.IFramework)
    self.mock_callbacks = mock.create_autospec(ui_callbacks.UiCallbacks)
    self.mock_framework.get_callbacks.return_value = self.mock_callbacks

  def test_upload_file_not_found(self):

    def _raise_not_found(_: types.PathLike):
      raise FileNotFoundError()

    engine = upload_engine.UploadEngine(
        self.mock_framework, object_data_supplier=_raise_not_found
    )

    with self.assertRaisesRegex(
        exceptions.FileUploadError, "Failed to upload file"
    ):
      engine.upload_file("not_exists.txt")

  def test_upload_file_in_cache(self):
    engine = upload_engine.UploadEngine(
        self.mock_framework,
        object_data_supplier=lambda filename: TEST_FILE_DATA,
    )
    engine.upload_file("filename")
    engine.handle_check_resource_cache_response(
        "",
        ui_message=robotics_ui_pb2.UIMessage(
            check_file_cache_response=robotics_ui_pb2.CheckFileCacheResponse(
                hash=TEST_FILE_DATA_HASH,
                in_cache=True,
            )
        ),
    )

    # Ensure we only sent the check request, and not the upload request.
    self.mock_framework.send_raw_message.assert_called_once_with(
        robotics_ui_pb2.RuiMessage(
            message_id=str(uuid.UUID(int=1)),
            ui_message=robotics_ui_pb2.UIMessage(
                check_file_cache_request=robotics_ui_pb2.CheckFileCacheRequest(
                    hash=TEST_FILE_DATA_HASH,
                )
            ),
        )
    )

    # Ensure we called the file_uploaded callback.
    self.mock_callbacks.resource_uploaded.assert_called_once_with(
        types.ResourceLocator(scheme="file", path="filename"),
        TEST_FILE_DATA_HASH,
    )

  def test_upload_file_not_in_cache(self):
    engine = upload_engine.UploadEngine(
        self.mock_framework,
        object_data_supplier=lambda filename: TEST_FILE_DATA,
    )
    engine.upload_file("filename")
    engine.handle_check_resource_cache_response(
        "",
        ui_message=robotics_ui_pb2.UIMessage(
            check_file_cache_response=robotics_ui_pb2.CheckFileCacheResponse(
                hash=TEST_FILE_DATA_HASH,
                in_cache=False,
            )
        ),
    )

    # Ensure we send the check request and the upload request.
    self.mock_framework.send_raw_message.assert_has_calls([
        mock.call(
            robotics_ui_pb2.RuiMessage(
                message_id=str(uuid.UUID(int=1)),
                ui_message=robotics_ui_pb2.UIMessage(
                    check_file_cache_request=robotics_ui_pb2.CheckFileCacheRequest(
                        hash=TEST_FILE_DATA_HASH,
                    )
                ),
            )
        ),
        mock.call(
            robotics_ui_pb2.RuiMessage(
                message_id=str(uuid.UUID(int=2)),
                ui_message=robotics_ui_pb2.UIMessage(
                    upload_file_request=robotics_ui_pb2.UploadFileRequest(
                        hash=TEST_FILE_DATA_HASH,
                        data=TEST_FILE_DATA,
                    )
                ),
            )
        ),
    ])

    # Ensure we called the file_uploaded callback.
    self.mock_callbacks.resource_uploaded.assert_called_once_with(
        types.ResourceLocator(scheme="file", path="filename"),
        TEST_FILE_DATA_HASH,
    )

  def test_upload_file_from_filename(self):
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as file:
      file.write(TEST_FILE_DATA)
      file.flush()

      engine = upload_engine.UploadEngine(self.mock_framework)
      engine.upload_file(file.name)
      engine.handle_check_resource_cache_response(
          "",
          ui_message=robotics_ui_pb2.UIMessage(
              check_file_cache_response=robotics_ui_pb2.CheckFileCacheResponse(
                  hash=TEST_FILE_DATA_HASH,
                  in_cache=False,
              )
          ),
      )

      # Ensure we send the check request and the upload request.
      self.mock_framework.send_raw_message.assert_has_calls([
          mock.call(
              robotics_ui_pb2.RuiMessage(
                  message_id=str(uuid.UUID(int=1)),
                  ui_message=robotics_ui_pb2.UIMessage(
                      check_file_cache_request=robotics_ui_pb2.CheckFileCacheRequest(
                          hash=TEST_FILE_DATA_HASH,
                      )
                  ),
              )
          ),
          mock.call(
              robotics_ui_pb2.RuiMessage(
                  message_id=str(uuid.UUID(int=2)),
                  ui_message=robotics_ui_pb2.UIMessage(
                      upload_file_request=robotics_ui_pb2.UploadFileRequest(
                          hash=TEST_FILE_DATA_HASH,
                          data=TEST_FILE_DATA,
                      )
                  ),
              )
          ),
      ])

      self.mock_callbacks.resource_uploaded.assert_called_once_with(
          types.ResourceLocator(scheme="file", path=file.name),
          TEST_FILE_DATA_HASH,
      )

  def test_upload_file_from_path(self):
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as file:
      file.write(TEST_FILE_DATA)
      file.flush()

      engine = upload_engine.UploadEngine(self.mock_framework)
      engine.upload_file(pathlib.Path(file.name))
      engine.handle_check_resource_cache_response(
          "",
          ui_message=robotics_ui_pb2.UIMessage(
              check_file_cache_response=robotics_ui_pb2.CheckFileCacheResponse(
                  hash=TEST_FILE_DATA_HASH,
                  in_cache=False,
              )
          ),
      )

      # Ensure we send the check request and the upload request.
      self.mock_framework.send_raw_message.assert_has_calls([
          mock.call(
              robotics_ui_pb2.RuiMessage(
                  message_id=str(uuid.UUID(int=1)),
                  ui_message=robotics_ui_pb2.UIMessage(
                      check_file_cache_request=robotics_ui_pb2.CheckFileCacheRequest(
                          hash=TEST_FILE_DATA_HASH,
                      )
                  ),
              )
          ),
          mock.call(
              robotics_ui_pb2.RuiMessage(
                  message_id=str(uuid.UUID(int=2)),
                  ui_message=robotics_ui_pb2.UIMessage(
                      upload_file_request=robotics_ui_pb2.UploadFileRequest(
                          hash=TEST_FILE_DATA_HASH,
                          data=TEST_FILE_DATA,
                      )
                  ),
              )
          ),
      ])

      self.mock_callbacks.resource_uploaded.assert_called_once_with(
          types.ResourceLocator(scheme="file", path=pathlib.Path(file.name)),
          TEST_FILE_DATA_HASH,
      )

  def test_upload_file_from_zip(self):
    # Create a zip file with a single file.
    with tempfile.NamedTemporaryFile(
        mode="wb", suffix=".zip", delete=False
    ) as zip_file:
      with zipfile.ZipFile(zip_file.name, mode="w") as f:
        f.writestr("filename", TEST_FILE_DATA)

      engine = upload_engine.UploadEngine(self.mock_framework)
      engine.upload_file(zipfile.Path(zip_file.name, "filename"))
      engine.handle_check_resource_cache_response(
          "",
          ui_message=robotics_ui_pb2.UIMessage(
              check_file_cache_response=robotics_ui_pb2.CheckFileCacheResponse(
                  hash=TEST_FILE_DATA_HASH,
                  in_cache=False,
              )
          ),
      )

      # Ensure we send the check request and the upload request.
      self.mock_framework.send_raw_message.assert_has_calls([
          mock.call(
              robotics_ui_pb2.RuiMessage(
                  message_id=str(uuid.UUID(int=1)),
                  ui_message=robotics_ui_pb2.UIMessage(
                      check_file_cache_request=robotics_ui_pb2.CheckFileCacheRequest(
                          hash=TEST_FILE_DATA_HASH,
                      )
                  ),
              )
          ),
          mock.call(
              robotics_ui_pb2.RuiMessage(
                  message_id=str(uuid.UUID(int=2)),
                  ui_message=robotics_ui_pb2.UIMessage(
                      upload_file_request=robotics_ui_pb2.UploadFileRequest(
                          hash=TEST_FILE_DATA_HASH,
                          data=TEST_FILE_DATA,
                      )
                  ),
              )
          ),
      ])

      # Ensure we called the file_uploaded callback. zipfile.Path does not
      # implement __eq__, so we have to unpack the args.
      self.mock_callbacks.resource_uploaded.assert_called_once()
      args, _ = self.mock_callbacks.resource_uploaded.call_args
      called_path: zipfile.Path = args[0].path
      self.assertEqual(called_path.root.filename, zip_file.name)
      self.assertEqual(called_path.name, "filename")
      self.assertEqual(args[1], TEST_FILE_DATA_HASH)

  def test_upload_resource(self):
    engine = upload_engine.UploadEngine(self.mock_framework)
    data = robotics_ui_pb2.WireTriangleFormat().SerializeToString()
    hash_ = hashlib.sha256(data).digest()
    engine.upload_resource(
        types.ResourceLocator(
            scheme="mesh", path="original_stl_path.stl", data=data
        )
    )

    engine.handle_check_resource_cache_response(
        "",
        ui_message=robotics_ui_pb2.UIMessage(
            check_file_cache_response=robotics_ui_pb2.CheckFileCacheResponse(
                hash=hash_,
                in_cache=False,
            )
        ),
    )

    # Ensure we send the check request and the upload request.
    self.mock_framework.send_raw_message.assert_has_calls([
        mock.call(
            robotics_ui_pb2.RuiMessage(
                message_id=str(uuid.UUID(int=1)),
                ui_message=robotics_ui_pb2.UIMessage(
                    check_file_cache_request=robotics_ui_pb2.CheckFileCacheRequest(
                        hash=hash_,
                    )
                ),
            )
        ),
        mock.call(
            robotics_ui_pb2.RuiMessage(
                message_id=str(uuid.UUID(int=2)),
                ui_message=robotics_ui_pb2.UIMessage(
                    upload_file_request=robotics_ui_pb2.UploadFileRequest(
                        hash=hash_,
                        wire_triangle_format=robotics_ui_pb2.WireTriangleFormat(),
                    )
                ),
            )
        ),
    ])

    self.mock_callbacks.resource_uploaded.assert_called_once_with(
        types.ResourceLocator(scheme="mesh", path="original_stl_path.stl"),
        hash_,
    )


if __name__ == "__main__":
  absltest.main()
