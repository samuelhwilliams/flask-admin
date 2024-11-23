import os
from unittest import SkipTest
from uuid import uuid4

import pytest

try:
    from flask_admin.contrib.fileadmin import azure
except ImportError:
    azure = None

from .test_fileadmin import Base


class TestAzureFileAdmin(Base.FileAdminTests):
    _test_storage = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        if azure is None:
            raise SkipTest("AzureFileAdmin dependencies not installed")

        self._container_name = f"fileadmin-tests-{uuid4()}"

        if not self._test_storage or not self._container_name:
            raise SkipTest("AzureFileAdmin test credentials not set")

        client = azure.BlobServiceClient.from_connection_string(self._test_storage)
        client.create_container(self._container_name)
        file_name = "dummy.txt"
        file_path = os.path.join(self._test_files_root, file_name)
        blob_client = client.get_blob_client(self._container_name, file_name)
        with open(file_path, "rb") as file:
            blob_client.upload_blob(file)

        yield

        client = azure.BlobServiceClient.from_connection_string(self._test_storage)
        client.delete_container(self._container_name)

    def fileadmin_class(self):
        return azure.AzureFileAdmin

    def fileadmin_args(self):
        return (self._container_name, self._test_storage), {}
