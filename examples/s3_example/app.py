from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.fileadmin.s3 import S3FileAdmin
from testcontainers.localstack import LocalStackContainer
import boto3

app = Flask(__name__)
admin = Admin(app)

if __name__ == '__main__':
    # Start LocalStack container
    with LocalStackContainer(image="localstack/localstack:latest") as localstack:
        # Get LocalStack S3 endpoint
        s3_endpoint = localstack.get_url()

        # Create S3 client
        s3_client = boto3.client(
            "s3",
            endpoint_url=s3_endpoint,
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )

        # Create S3 bucket
        bucket_name = "your-bucket-name"
        s3_client.create_bucket(Bucket=bucket_name)

        # Add S3FileAdmin view
        admin.add_view(S3FileAdmin(
            bucket_name=bucket_name,
            region="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            name="S3 Files"
        ))

        app.run(debug=True)
