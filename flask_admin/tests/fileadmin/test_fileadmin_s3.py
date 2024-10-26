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

    def test_file_upload(self, app, admin):
        fileadmin_class = self.fileadmin_class()
        fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

        class MyFileAdmin(fileadmin_class):
            editable_extensions = ("txt",)

        view_kwargs = dict(fileadmin_kwargs)
        view_kwargs.setdefault("name", "Files")
        view = MyFileAdmin(*fileadmin_args, **view_kwargs)

        admin.add_view(view)

        client = app.test_client()

        # upload
        rv = client.get("/admin/myfileadmin/upload/")
        assert rv.status_code == 200

        rv = client.post(
            "/admin/myfileadmin/upload/",
            data=dict(upload=(BytesIO(b"test content"), "test_upload.txt")),
        )
        assert rv.status_code == 302

        rv = client.get("/admin/myfileadmin/")
        assert rv.status_code == 200
        assert "path=test_upload.txt" in rv.data.decode("utf-8")

    def test_file_download(self, app, admin):
        fileadmin_class = self.fileadmin_class()
        fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

        class MyFileAdmin(fileadmin_class):
            editable_extensions = ("txt",)

        view_kwargs = dict(fileadmin_kwargs)
        view_kwargs.setdefault("name", "Files")
        view = MyFileAdmin(*fileadmin_args, **view_kwargs)

        admin.add_view(view)

        client = app.test_client()

        # download
        rv = client.get("/admin/myfileadmin/download/?path=dummy.txt")
        assert rv.status_code == 302
        assert "dummy.txt" in rv.headers["Location"]

    def test_file_rename(self, app, admin):
        fileadmin_class = self.fileadmin_class()
        fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

        class MyFileAdmin(fileadmin_class):
            editable_extensions = ("txt",)

        view_kwargs = dict(fileadmin_kwargs)
        view_kwargs.setdefault("name", "Files")
        view = MyFileAdmin(*fileadmin_args, **view_kwargs)

        admin.add_view(view)

        client = app.test_client()

        # rename
        rv = client.get("/admin/myfileadmin/rename/?path=dummy.txt")
        assert rv.status_code == 200
        assert "dummy.txt" in rv.data.decode("utf-8")

        rv = client.post(
            "/admin/myfileadmin/rename/?path=dummy.txt",
            data=dict(name="dummy_renamed.txt", path="dummy.txt"),
        )
        assert rv.status_code == 302

        rv = client.get("/admin/myfileadmin/")
        assert rv.status_code == 200
        assert "path=dummy_renamed.txt" in rv.data.decode("utf-8")
        assert "path=dummy.txt" not in rv.data.decode("utf-8")

    def test_file_delete(self, app, admin):
        fileadmin_class = self.fileadmin_class()
        fileadmin_args, fileadmin_kwargs = self.fileadmin_args()

        class MyFileAdmin(fileadmin_class):
            editable_extensions = ("txt",)

        view_kwargs = dict(fileadmin_kwargs)
        view_kwargs.setdefault("name", "Files")
        view = MyFileAdmin(*fileadmin_args, **view_kwargs)

        admin.add_view(view)

        client = app.test_client()

        # delete
        rv = client.post(
            "/admin/myfileadmin/delete/", data=dict(path="dummy.txt")
        )
        assert rv.status_code == 302

        rv = client.get("/admin/myfileadmin/")
        assert rv.status_code == 200
        assert "path=dummy.txt" not in rv.data.decode("utf-8")
