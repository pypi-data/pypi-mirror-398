import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open
import pytest
import xml.etree.ElementTree as ET
from regscale.core.app.internal.file_uploads import file_upload, upload_file
from regscale.models.regscale_models.file import File
from regscale.core.app.api import Api


class TestFileUploadsAndFileModel(unittest.TestCase):
    @patch("regscale.core.app.internal.file_uploads.File.upload_file_to_regscale")
    @patch("regscale.core.app.internal.file_uploads.encode_file_to_base64")
    @patch("regscale.core.app.internal.file_uploads.decode_base64_to_bytesio")
    def test_file_upload_success(self, mock_decode_b64, mock_encode_b64, mock_upload):
        mock_encode_b64.return_value = "ZmFrZV9iYXNlNjQ="
        mock_decode_b64.return_value = MagicMock(getvalue=lambda: b"fake_bytes")
        mock_upload.return_value = {"result": "success"}
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name
        try:
            result = file_upload(123, "test_module", tmp_path)
            self.assertEqual(result, {"result": "success"})
            mock_encode_b64.assert_called_once_with(tmp_path)
            mock_upload.assert_called_once()
        finally:
            os.remove(tmp_path)

    def test_file_upload_missing_file(self):
        result = file_upload(123, "test_module", "nonexistent_file.txt")
        self.assertIsNone(result)

    @patch("regscale.core.app.internal.file_uploads.File.upload_file_to_regscale")
    @patch("regscale.core.app.internal.file_uploads.decode_base64_to_bytesio")
    def test_upload_file_success(self, mock_decode_b64, mock_upload):
        mock_decode_b64.return_value = MagicMock(getvalue=lambda: b"fake_bytes")
        mock_upload.return_value = {"id": 1, "result": "success"}
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name
        try:
            result = upload_file(
                ssp_id=123,
                parent_module="test_module",
                file_path=tmp_path,
                filestring="ZmFrZV9iYXNlNjQ=",
                filename="test.txt",
            )
            self.assertEqual(result, {"id": 1, "result": "success"})
            mock_decode_b64.assert_called_once_with("ZmFrZV9iYXNlNjQ=")
            mock_upload.assert_called_once()
        finally:
            os.remove(tmp_path)

    @patch("regscale.core.app.internal.file_uploads.File.upload_file_to_regscale")
    @patch("regscale.core.app.internal.file_uploads.decode_base64_to_bytesio")
    def test_upload_file_exception(self, mock_decode_b64, mock_upload):
        mock_decode_b64.return_value = MagicMock(getvalue=lambda: b"fake_bytes")
        mock_upload.side_effect = Exception("upload failed")
        result = upload_file(
            ssp_id=123,
            parent_module="test_module",
            file_path="fake_path",
            filestring="ZmFrZV9iYXNlNjQ=",
            filename="test.txt",
        )
        self.assertFalse(result)

    @patch("regscale.core.app.internal.file_uploads.process_base64_tags_in_xml")
    @patch("regscale.core.app.internal.file_uploads.upload_file")
    @patch("regscale.core.app.internal.file_uploads.encode_file_to_base64")
    def test_process_base64_in_xml(self, mock_encode_b64, mock_upload_file, mock_process_tags):
        from regscale.core.app.internal.file_uploads import process_base64_in_xml

        mock_process_tags.return_value = [
            {"filename": "file1.txt", "base64": "b64str1"},
            {"filename": "file2.txt", "base64": "b64str2"},
        ]
        mock_upload_file.side_effect = ["result1", "result2", "xml_result"]
        mock_encode_b64.return_value = "xml_b64"
        results = process_base64_in_xml(
            regscale_id=123,
            regscale_module="test_module",
            file_path="fake.xml",
            file_name="optional.xml",
        )
        self.assertEqual(results, ["result1", "result2", "xml_result"])
        self.assertEqual(mock_upload_file.call_count, 3)

    def test_process_base64_tags_in_xml(self):
        from regscale.core.app.internal.file_uploads import process_base64_tags_in_xml

        xml_content = """<root>
            <base64 filename=\"file1.txt\">YmFzZTY0X2NvbnRlbnQx</base64>
            <base64 filename=\"file2.txt\">YmFzZTY0X2NvbnRlbnQy</base64>
        </root>"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml", mode="w", encoding="utf-8") as tmp:
            tmp.write(xml_content)
            tmp_path = tmp.name
        try:
            results = process_base64_tags_in_xml(tmp_path)
            self.assertEqual(
                results,
                [
                    {"filename": "file1.txt", "base64": "YmFzZTY0X2NvbnRlbnQx"},
                    {"filename": "file2.txt", "base64": "YmFzZTY0X2NvbnRlbnQy"},
                ],
            )
        finally:
            os.remove(tmp_path)

    @patch(
        "regscale.models.regscale_models.file.File.upload_file_to_regscale",
        return_value={"id": 42, "result": "success"},
    )
    def test_upload_file_to_regscale_success(self, mock_upload):
        result = File.upload_file_to_regscale(
            file_name="test.txt", parent_id=123, parent_module="test_module", file_data=b"fake_bytes", api=MagicMock()
        )
        self.assertEqual(result, {"id": 42, "result": "success"})
        mock_upload.assert_called_once()

    @patch("regscale.models.regscale_models.file.Api")
    def test_upload_file_to_regscale_failure(self, mock_api):
        mock_api_instance = mock_api.return_value
        mock_api_instance.upload_file.side_effect = Exception("upload failed")
        result = File.upload_file_to_regscale(
            file_name="fail.txt",
            parent_id=999,
            parent_module="fail_module",
            file_data=b"fail_bytes",
            api=mock_api_instance,
        )
        self.assertFalse(result)

    @patch("regscale.models.regscale_models.file.Api")
    def test_download_file_from_regscale_to_memory(self, mock_api_class):
        mock_api = mock_api_class.return_value
        mock_api.config = {"domain": "https://test.com"}
        mock_response = MagicMock()
        mock_response.content = b"file content"
        mock_api.get.return_value = mock_response

        result = File.download_file_from_regscale_to_memory(
            api=mock_api, record_id=123, module="test_module", stored_name="test.txt", file_hash="abc123"
        )

        self.assertEqual(result, b"file content")

    @patch("regscale.models.regscale_models.file.Api")
    def test_get_files_for_parent_from_regscale(self, mock_api_class):
        mock_api = mock_api_class.return_value
        mock_api.config = {"domain": "https://test.com"}
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": "1",
                "trustedDisplayName": "test1.txt",
                "trustedStorageName": "test1.txt",
                "size": 100,
                "fullPath": "/test1.txt",
            }
        ]
        mock_api.get.return_value = mock_response

        result = File.get_files_for_parent_from_regscale(parent_id=123, parent_module="test_module", api=mock_api)

        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], File)

    @patch("regscale.models.regscale_models.file.Api")
    def test_delete_file(self, mock_api_class):
        mock_api = mock_api_class.return_value
        mock_app = MagicMock()
        mock_app.config = {"domain": "https://test.com"}
        mock_response = MagicMock()
        mock_response.ok = True
        mock_api.delete.return_value = mock_response

        file_obj = File(
            id="123", trustedDisplayName="test.txt", trustedStorageName="test.txt", size=100, fullPath="/test.txt"
        )

        result = File.delete_file(app=mock_app, file=file_obj)

        self.assertTrue(result)

    def test_determine_mime_type(self):
        self.assertEqual(
            File.determine_mime_type(".xlsx"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        self.assertEqual(File.determine_mime_type(".nessus"), "text/xml")
        self.assertEqual(File.determine_mime_type(".msg"), "application/vnd.ms-outlook")
        self.assertIsNone(File.determine_mime_type(".unknown"))

        gz_mime = File.determine_mime_type(".gz")
        self.assertIn(gz_mime, ["application/gzip", "application/x-gzip"])

    def test_file_model_creation(self):
        file_data = {
            "id": "123",
            "trustedDisplayName": "test.txt",
            "trustedStorageName": "test.txt",
            "size": 1024,
            "fullPath": "/test.txt",
        }

        file_obj = File(**file_data)

        self.assertEqual(file_obj.id, "123")
        self.assertEqual(file_obj.trustedDisplayName, "test.txt")
        self.assertEqual(file_obj.size, 1024)

    @patch("regscale.models.regscale_models.file.Api")
    def test_get_files_for_parent_general_error(self, mock_api_class):
        mock_api = mock_api_class.return_value
        mock_api.config = {"domain": "https://test.com"}
        mock_api.get.side_effect = Exception("General error")

        with self.assertRaises(SystemExit):
            File.get_files_for_parent_from_regscale(parent_id=123, parent_module="test_module", api=mock_api)

    @patch("regscale.models.regscale_models.file.File._create_regscale_file")
    @patch("regscale.models.regscale_models.file.Api")
    def test_upload_file_to_regscale_no_file_created(self, mock_api_class, mock_create_file):
        mock_create_file.return_value = None
        mock_api = MagicMock()

        result = File.upload_file_to_regscale(
            file_name="test.txt", parent_id=123, parent_module="test_module", api=mock_api, file_data=b"test content"
        )

        self.assertFalse(result)

    @patch("regscale.models.regscale_models.file.File._create_regscale_file")
    @patch("regscale.models.regscale_models.file.Api")
    def test_upload_file_to_regscale_no_id_in_response(self, mock_api_class, mock_create_file):
        mock_api = mock_api_class.return_value
        mock_api.config = {"domain": "https://test.com", "token": "test_token", "userId": "user123"}
        mock_create_file.return_value = {
            "fullPath": "/test.txt",
            "trustedDisplayName": "test.txt",
            "trustedStorageName": "test.txt",
            "uploadDate": "2024-01-01",
            "fileHash": "hash123",
            "shaHash": "sha123",
            "size": 100,
        }

        result = File.upload_file_to_regscale(
            file_name="test.txt", parent_id=123, parent_module="test_module", api=mock_api, file_data=b"test content"
        )

        self.assertFalse(result)

    @patch("regscale.models.regscale_models.file.File._create_regscale_file")
    @patch("regscale.models.regscale_models.file.Api")
    def test_upload_file_to_regscale_unsupported_mime_type(self, mock_api_class, mock_create_file):
        mock_api = mock_api_class.return_value
        mock_api.config = {"domain": "https://test.com", "token": "test_token", "userId": "user123"}
        mock_create_file.return_value = {
            "id": "file123",
            "fullPath": "/test.txt",
            "trustedDisplayName": "test.txt",
            "trustedStorageName": "test.txt",
            "uploadDate": "2024-01-01",
            "fileHash": "hash123",
            "shaHash": "sha123",
            "size": 100,
        }

        with patch.object(File, "determine_mime_type", return_value=None):
            result = File.upload_file_to_regscale(
                file_name="test.txt",
                parent_id=123,
                parent_module="test_module",
                api=mock_api,
                file_data=b"test content",
            )

            self.assertFalse(result)

    @patch("regscale.models.regscale_models.file.Tag")
    def test_get_existing_tags_dict(self, mock_tag_class):
        mock_tag1 = MagicMock()
        mock_tag1.title = "tag1"
        mock_tag1.id = "1"
        mock_tag2 = MagicMock()
        mock_tag2.title = "tag2"
        mock_tag2.id = "2"
        mock_tag_class.get_list.return_value = [mock_tag1, mock_tag2]

        result = File.get_existing_tags_dict()

        self.assertEqual(result, {"tag1": "1", "tag2": "2"})
        mock_tag_class.get_list.assert_called_once()

    @patch("regscale.models.regscale_models.file.TagMapping")
    def test_process_tag_with_existing_tag(self, mock_tag_mapping_class):
        mock_tag_mapping = MagicMock()
        mock_tag_mapping_class.return_value = mock_tag_mapping
        tags_dict = {"test_tag": "123"}

        File.process_tag("test_tag", "file123", tags_dict)

        mock_tag_mapping_class.assert_called_once_with(parentId="file123", parentModule="files", tagId="123")
        mock_tag_mapping.create.assert_called_once()

    @patch("regscale.models.regscale_models.file.File.get_existing_tags_dict")
    @patch("regscale.models.regscale_models.file.File.process_tag")
    def test_create_tag_mappings(self, mock_process_tag, mock_get_tags_dict):
        mock_get_tags_dict.return_value = {"tag1": "1", "tag2": "2"}
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "file123", "tags": "tag1,tag2"}

        File.create_tag_mappings(mock_response)

        mock_get_tags_dict.assert_called_once()
        self.assertEqual(mock_process_tag.call_count, 2)

    @patch("regscale.models.regscale_models.file.Application")
    def test_check_compression_file_not_found(self, mock_app_class):
        mock_app = mock_app_class.return_value
        mock_app.logger.debug = MagicMock()
        mock_app.logger.warning = MagicMock()

        file_data = b"test content"
        result_path, result_size = File._check_compression(file_path="nonexistent.txt", file_data=file_data)

        self.assertEqual(result_path, "nonexistent.txt")
        import sys

        expected_size = sys.getsizeof(file_data) / 1024
        self.assertEqual(result_size, expected_size)

    def test_compress_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as input_file:
            input_file.write(b"test content for compression")
            input_path = input_file.name

        output_path = input_path + ".gz"

        try:
            result = File._compress_file(input_path, output_path)

            self.assertEqual(result, output_path)
            self.assertTrue(os.path.exists(output_path))
            self.assertGreater(os.path.getsize(output_path), 0)
        finally:
            os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)

    @patch("regscale.models.regscale_models.file.Api")
    def test_create_regscale_file_success(self, mock_api_class):
        mock_api = mock_api_class.return_value
        mock_api.config = {"domain": "https://test.com", "token": "test_token"}
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": "file123",
            "fullPath": "/test.txt",
            "trustedDisplayName": "test.txt",
            "trustedStorageName": "test.txt",
            "uploadDate": "2024-01-01",
            "fileHash": "hash123",
            "shaHash": "sha123",
        }
        mock_api.post.return_value = mock_response

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name

        try:
            with patch("os.path.getsize", return_value=1024):
                result = File._create_regscale_file(
                    file_path=tmp_path, parent_id=123, parent_module="test_module", api=mock_api
                )

                self.assertIsNotNone(result)
                self.assertEqual(result["id"], "file123")
                self.assertEqual(result["size"], 1024)
        finally:
            os.remove(tmp_path)

    def test_create_regscale_file_zero_size(self):
        mock_api = MagicMock()

        with self.assertRaises(ValueError):
            with patch("os.path.getsize", return_value=0):
                File._create_regscale_file(
                    file_path="test.txt", parent_id=123, parent_module="test_module", api=mock_api
                )

    @patch("regscale.models.regscale_models.file.Api")
    def test_create_regscale_file_api_failure(self, mock_api_class):
        mock_api = mock_api_class.return_value
        mock_api.config = {"domain": "https://test.com", "token": "test_token"}
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_api.post.return_value = mock_response

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name

        try:
            with patch("os.path.getsize", return_value=1024):
                result = File._create_regscale_file(
                    file_path=tmp_path, parent_id=123, parent_module="test_module", api=mock_api
                )

                self.assertIsNone(result)
                mock_api.logger.warning.assert_called()
        finally:
            os.remove(tmp_path)

    @patch("regscale.models.regscale_models.file.Tag")
    def test_process_tag_nonexistent_tag(self, mock_tag_class):
        mock_tag_mapping_class = MagicMock()
        with patch("regscale.models.regscale_models.file.TagMapping", mock_tag_mapping_class):
            tags_dict = {"existing_tag": "123"}

            File.process_tag("nonexistent_tag", "file123", tags_dict)

            mock_tag_mapping_class.assert_not_called()

    @patch("regscale.models.regscale_models.file.File.get_existing_tags_dict")
    @patch("regscale.models.regscale_models.file.File.process_tag")
    def test_create_tag_mappings_no_id(self, mock_process_tag, mock_get_tags_dict):
        mock_get_tags_dict.return_value = {"tag1": "1", "tag2": "2"}
        mock_response = MagicMock()
        mock_response.json.return_value = {"tags": "tag1,tag2"}

        File.create_tag_mappings(mock_response)

        mock_process_tag.assert_not_called()

    def test_determine_mime_type_known_types(self):
        with patch("mimetypes.types_map", {".txt": "text/plain"}):
            result = File.determine_mime_type(".txt")
            self.assertEqual(result, "text/plain")

    def test_determine_mime_type_unknown_type(self):
        with patch("mimetypes.types_map", {}):
            with patch("logging.getLogger") as mock_logger:
                mock_logger_instance = MagicMock()
                mock_logger.return_value = mock_logger_instance

                result = File.determine_mime_type(".unknown")

                self.assertIsNone(result)
                mock_logger_instance.warning.assert_called_once()

    @patch("regscale.models.regscale_models.file.Api")
    def test_create_regscale_file_no_response(self, mock_api_class):
        mock_api = mock_api_class.return_value
        mock_api.config = {"domain": "https://test.com", "token": "test_token"}
        mock_api.post.return_value = None

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name

        try:
            with patch("os.path.getsize", return_value=1024):
                result = File._create_regscale_file(
                    file_path=tmp_path, parent_id=123, parent_module="test_module", api=mock_api
                )
                self.assertIsNone(result)
                mock_api.logger.warning.assert_called_once()
        finally:
            os.remove(tmp_path)

    @patch("regscale.models.regscale_models.file.Api")
    def test_create_regscale_file_with_file_data(self, mock_api_class):
        mock_api = mock_api_class.return_value
        mock_api.config = {"domain": "https://test.com", "token": "test_token"}
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "id": "file123",
            "fullPath": "/test.txt",
            "trustedDisplayName": "test.txt",
            "trustedStorageName": "test.txt",
            "uploadDate": "2024-01-01",
            "fileHash": "hash123",
            "shaHash": "sha123",
        }
        mock_api.post.return_value = mock_response

        file_data = b"test file content"
        with patch("os.path.getsize", return_value=len(file_data)):
            result = File._create_regscale_file(
                file_path="test.txt", parent_id=123, parent_module="test_module", api=mock_api, file_data=file_data
            )

            self.assertIsNotNone(result)
            self.assertEqual(result["id"], "file123")
            self.assertEqual(result["size"], len(file_data))
