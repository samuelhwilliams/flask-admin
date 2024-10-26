# S3 Example

This example demonstrates how to set up and use Flask-Admin with Amazon S3 for file management.

## Prerequisites

- Python 3.8 or higher
- Flask
- Flask-Admin
- boto3

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/samuelhwilliams/flask-admin.git
   cd flask-admin/examples/s3_example
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Update the `app.py` file with your AWS credentials and S3 bucket details:
   ```python
   admin.add_view(S3FileAdmin(
       bucket_name='your-bucket-name',
       region='your-region',
       aws_access_key_id='your-access-key-id',
       aws_secret_access_key='your-secret-access-key',
       name='S3 Files'
   ))
   ```

## Running the Application

1. Run the Flask application:
   ```bash
   flask run
   ```

2. Open your web browser and navigate to `http://127.0.0.1:5000/admin/` to access the Flask-Admin interface with S3 file management.

## Usage

- You can upload, download, rename, and delete files in your S3 bucket using the Flask-Admin interface.
