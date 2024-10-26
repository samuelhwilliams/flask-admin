import time
from types import ModuleType
from typing import Optional

from flask import redirect

from flask_admin.babel import gettext

from . import BaseFileAdmin

s3: Optional[ModuleType]

try:
    import boto3
except ImportError:
    s3 = None


class S3Storage:
    """
    Storage object representing files on an Amazon S3 bucket.

    Usage::

        from flask_admin.contrib.fileadmin import BaseFileAdmin
        from flask_admin.contrib.fileadmin.s3 import S3Storage

        class MyS3Admin(BaseFileAdmin):
            # Configure your class however you like
            pass

        fileadmin_view = MyS3Admin(storage=S3Storage(...))

    """

    def __init__(self, bucket_name, region, aws_access_key_id, aws_secret_access_key):
        """
        Constructor

            :param bucket_name:
                Name of the bucket that the files are on.

            :param region:
                Region that the bucket is located

            :param aws_access_key_id:
                AWS Access Key ID

            :param aws_secret_access_key:
                AWS Secret Access Key

        Make sure the credentials have the correct permissions set up on
        Amazon or else S3 will return a 403 FORBIDDEN error.
        """

        if not s3:
            raise ValueError(
                "Could not import `boto3`. "
                "Enable `s3` integration by installing `flask-admin[s3]`"
            )

        self.s3_client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        self.bucket_name = bucket_name
        self.separator = "/"

    def get_files(self, path, directory):
        def _strip_path(name, path):
            if name.startswith(path):
                return name.replace(path, "", 1)
            return name

        def _remove_trailing_slash(name):
            return name[:-1]

        def _iso_to_epoch(timestamp):
            dt = time.strptime(timestamp.split(".")[0], "%Y-%m-%dT%H:%M:%S")
            return int(time.mktime(dt))

        files = []
        directories = []
        if path and not path.endswith(self.separator):
            path += self.separator
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name, Prefix=path, Delimiter=self.separator
        )
        for content in response.get("Contents", []):
            name = _strip_path(content["Key"], path)
            last_modified = _iso_to_epoch(content["LastModified"].isoformat())
            files.append((name, content["Key"], False, content["Size"], last_modified))
        for prefix in response.get("CommonPrefixes", []):
            name = _remove_trailing_slash(_strip_path(prefix["Prefix"], path))
            directories.append((name, prefix["Prefix"], True, 0, 0))
        return directories + files

    def _get_bucket_list_prefix(self, path):
        parts = path.split(self.separator)
        if len(parts) == 1:
            search = ""
        else:
            search = self.separator.join(parts[:-1]) + self.separator
        return search

    def _get_path_keys(self, path):
        search = self._get_bucket_list_prefix(path)
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name, Prefix=search, Delimiter=self.separator
        )
        return {content["Key"] for content in response.get("Contents", [])}

    def is_dir(self, path):
        keys = self._get_path_keys(path)
        return path + self.separator in keys

    def path_exists(self, path):
        if path == "":
            return True
        keys = self._get_path_keys(path)
        return path in keys or (path + self.separator) in keys

    def get_base_path(self):
        return ""

    def get_breadcrumbs(self, path):
        accumulator = []
        breadcrumbs = []
        for n in path.split(self.separator):
            accumulator.append(n)
            breadcrumbs.append((n, self.separator.join(accumulator)))
        return breadcrumbs

    def send_file(self, file_path):
        url = self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": file_path},
            ExpiresIn=3600,
        )
        return redirect(url)

    def save_file(self, path, file_data):
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=path,
            Body=file_data.stream,
            ContentType=file_data.content_type,
        )

    def delete_tree(self, directory):
        self._check_empty_directory(directory)
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=directory + self.separator)

    def delete_file(self, file_path):
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)

    def make_dir(self, path, directory):
        dir_path = self.separator.join([path, (directory + self.separator)])
        self.s3_client.put_object(Bucket=self.bucket_name, Key=dir_path, Body="")

    def _check_empty_directory(self, path):
        if not self._is_directory_empty(path):
            raise ValueError(gettext("Cannot operate on non empty " "directories"))
        return True

    def rename_path(self, src, dst):
        if self.is_dir(src):
            self._check_empty_directory(src)
            src += self.separator
            dst += self.separator
        copy_source = {"Bucket": self.bucket_name, "Key": src}
        self.s3_client.copy_object(CopySource=copy_source, Bucket=self.bucket_name, Key=dst)
        self.delete_file(src)

    def _is_directory_empty(self, path):
        keys = self._get_path_keys(path + self.separator)
        return len(keys) == 1

    def read_file(self, path):
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=path)
        return response["Body"].read()

    def write_file(self, path, content):
        self.s3_client.put_object(Bucket=self.bucket_name, Key=path, Body=content)


class S3FileAdmin(BaseFileAdmin):
    """
    Simple Amazon Simple Storage Service file-management interface.

        :param bucket_name:
            Name of the bucket that the files are on.

        :param region:
            Region that the bucket is located

        :param aws_access_key_id:
            AWS Access Key ID

        :param aws_secret_access_key:
            AWS Secret Access Key

    Sample usage::

        from flask_admin import Admin
        from flask_admin.contrib.fileadmin.s3 import S3FileAdmin

        admin = Admin()

        admin.add_view(S3FileAdmin('files_bucket', 'us-east-1', 'key_id', 'secret_key')
    """

    def __init__(
        self,
        bucket_name,
        region,
        aws_access_key_id,
        aws_secret_access_key,
        *args,
        **kwargs,
    ):
        storage = S3Storage(
            bucket_name, region, aws_access_key_id, aws_secret_access_key
        )
        super().__init__(*args, storage=storage, **kwargs)
