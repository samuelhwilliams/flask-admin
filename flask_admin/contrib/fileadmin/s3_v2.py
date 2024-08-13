import time
from types import ModuleType
from typing import Optional

try:
    import boto3
except ImportError:
    raise ValueError(
        'Could not import `boto3`. '
        'Enable `s3` integration by installing `flask-admin[s3]`'
    )

from flask import redirect
from flask_admin.babel import gettext

from . import BaseFileAdmin


class S3V2Storage(object):
    """
        Storage object representing files on an Amazon S3 bucket.

        Usage::

            from flask_admin.contrib.fileadmin import BaseFileAdmin
            from flask_admin.contrib.fileadmin.s3 import S3Storage

            class MyS3V2Admin(BaseFileAdmin):
                # Configure your class however you like
                pass

            fileadmin_view = MyS3V2Admin(storage=S3V2Storage(...))

    """

    def __init__(self, boto3_s3_bucket, max_objects=50_000):
        """
            Constructor

                :param boto3_s3_bucket:
                    An instance of `boto3.client('s3', ...)`

            Make sure the credentials have the correct permissions set up on
            Amazon or else S3 will return a 403 FORBIDDEN error.
        """
        self.bucket = boto3_s3_bucket
        self.client = self.bucket.meta.client
        self.max_objects = max_objects
        self.separator = '/'

    def get_files(self, path, directory):
        def _strip_path(name, path):
            if name.startswith(path):
                return name.replace(path, '', 1)
            return name

        files = []
        directories = []

        if path and not path.endswith(self.separator):
            path += self.separator

        page_size = 1_000
        response = self.client.list_objects_v2(
            Bucket=self.bucket.name,
            Prefix=path,
            Delimiter=self.separator,
            MaxKeys=page_size
        )

        while response['KeyCount'] > 0:
            # Collect all the 'directories'
            if 'CommonPrefixes' in response:
                for prefix in response['CommonPrefixes']:
                    name = _strip_path(prefix['Prefix'], path).rstrip(self.separator)
                    key_name = prefix['Prefix'].rstrip(self.separator)
                    dir_tuple = (name, key_name, True, 0, 0)
                    if dir_tuple not in directories:
                        directories.append(dir_tuple)

            # Collect all the 'files'
            for object_data in response.get('Contents', []):
                key = object_data['Key']
                object_size = object_data['Size']
                last_modified = object_data['LastModified']
                name = _strip_path(key, path)
                files.append((name, key, False, object_size, last_modified))

            # Continue collection if there are more objects in the bucket
            if 'NextToken' in response and response['KeyCount'] == page_size:
                response = self.client.list_objects_v2(
                    Bucket=self.bucket.name,
                    Prefix=path,
                    Delimiter=self.separator,
                    MaxKeys=page_size,
                    ContinuationToken=response['NextToken']
                )
            else:
                break

        return directories + files

    def _get_path_keys(self, path):
        pass

    def is_dir(self, path):
        pass

    def path_exists(self, path):
        pass

    def get_base_path(self):
        return ''

    def get_breadcrumbs(self, path):
        pass

    def send_file(self, file_path):
        pass

    def save_file(self, path, file_data):
        pass

    def delete_tree(self, directory):
        pass

    def delete_file(self, file_path):
        pass

    def make_dir(self, path, directory):
        pass

    def rename_path(self, src, dst):
        pass

    def read_file(self, path):
        pass

    def write_file(self, path, content):
        pass


class S3V2FileAdmin(BaseFileAdmin):
    """
        Simple Amazon Simple Storage Service file-management interface.

            :param boto3_s3_bucket:
                An instance of `boto3.resource('s3', ...).Bucket(bucket_name)`

        Sample usage::

            from flask_admin import Admin
            from flask_admin.contrib.fileadmin.s3 import S3FileAdmin

            admin = Admin()

            admin.add_view(S3FileAdmin(boto3_s3_bucket=boto3_s3_bucket))
    """

    def __init__(self, boto3_s3_bucket, *args, **kwargs):
        storage = S3V2Storage(boto3_s3_bucket=boto3_s3_bucket)
        super(S3V2FileAdmin, self).__init__(*args, storage=storage, **kwargs)
