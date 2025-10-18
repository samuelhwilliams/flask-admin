import os
from uuid import uuid4

import pytest

from flask_admin.contrib.fileadmin import azure

from .test_fileadmin import Base


class TestAzureFileAdmin(Base.FileAdminTests):
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, azurite_container):
        """
        Setup Azure Blob Storage test environment.
        Uses azurite_container from parent conftest (testcontainer or CI service).
        """
        # azurite_container ensures AZURE_STORAGE_CONNECTION_STRING is set
        azure_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

        if not azure_connection_string:
            pytest.skip("Azure Storage not available (no Docker or connection string)")

        self._container_name = f"fileadmin-tests-{uuid4()}"

        try:
            self._client = azure.BlobServiceClient.from_connection_string(
                azure_connection_string
            )
            self._client.create_container(self._container_name)
            file_name = "dummy.txt"
            file_path = os.path.join(self._test_files_root, file_name)
            blob_client = self._client.get_blob_client(self._container_name, file_name)
            with open(file_path, "rb") as file:
                blob_client.upload_blob(file)

            yield

            # Cleanup
            self._client.delete_container(self._container_name)
        except Exception as e:
            pytest.skip(f"Azure Blob Storage connection failed: {e}")

    def fileadmin_class(self):
        return azure.AzureFileAdmin

    def fileadmin_args(self):
        return (self._client, self._container_name), {}
