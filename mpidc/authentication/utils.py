import boto3
from botocore.exceptions import NoCredentialsError
from django.conf import settings



def UploadDocAWS(file_path):
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    s3_file_name = file_path
    # AWS credentials
    AWS_ACCESS_KEY = settings.AWS_ACCESS_KEY_ID
    AWS_SECRET_KEY = settings.AWS_SECRET_ACCESS_KEY
    AWS_REGION = settings.AWS_S3_REGION_NAME

    # Create S3 client with credentials
    # is used to create an S3 client object that your Python code uses to communicate with AWS S3.
    s3 = boto3.client('s3', 
                      aws_access_key_id=AWS_ACCESS_KEY,
                      aws_secret_access_key=AWS_SECRET_KEY,
                      region_name=AWS_REGION)

    try:
        # Upload the file
        print(file_path,"23")
        s3.upload_fileobj(file_path, bucket_name, str(s3_file_name))

        print(f"Uploaded to https://{bucket_name}.s3.{AWS_REGION}.amazonaws.com/{s3_file_name}")
        return (f"Uploaded to https://{bucket_name}.s3.{AWS_REGION}.amazonaws.com/{s3_file_name}")
    except FileNotFoundError:
        print("The file was not found")
    except NoCredentialsError:
        print("Credentials not available")
