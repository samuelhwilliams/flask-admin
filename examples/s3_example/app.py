from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.fileadmin.s3 import S3FileAdmin

app = Flask(__name__)
admin = Admin(app)

# Add S3FileAdmin view
admin.add_view(S3FileAdmin(
    bucket_name='your-bucket-name',
    region='your-region',
    aws_access_key_id='your-access-key-id',
    aws_secret_access_key='your-secret-access-key',
    name='S3 Files'
))

if __name__ == '__main__':
    app.run(debug=True)
