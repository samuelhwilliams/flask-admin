import os.path as op
from os import getenv
from unittest import SkipTest
from uuid import uuid4

import pytest

from flask_admin.contrib.fileadmin import s3

from .test_fileadmin import Base


class TestS3FileAdmin(Base.FileAdminTests):
    _test_storage = getenv("AWS_ACCESS_KEY_ID")

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        if not s3.boto3:
            raise SkipTest("S3FileAdmin dependencies not installed")

        self._bucket_name = f"fileadmin-tests-{uuid4()}"

        if not self._test_storage or not self._bucket_name:
            raise SkipTest("S3FileAdmin test credentials not set")

        client = s3.boto3.client(
            "s3",
            aws_access_key_id=self._test_storage,
            aws_secret_access_key=getenv("AWS_SECRET_ACCESS_KEY"),
        )
        client.create_bucket(Bucket=self._bucket_name)
        dummy = op.join(self._test_files_root, "dummy.txt")
        client.upload_file(dummy, self._bucket_name, "dummy.txt")

        yield

        client.delete_bucket(Bucket=self._bucket_name)

    def fileadmin_class(self):
        return s3.S3FileAdmin

    def fileadmin_args(self):
        return (
            self._bucket_name,
            "us-east-1",
            self._test_storage,
            getenv("AWS_SECRET_ACCESS_KEY"),
        ), {}
