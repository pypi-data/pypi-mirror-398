import boto3
from botocore.exceptions import BotoCoreError, ClientError
from botocore.config import Config
import logging
from ....caching.factory import get_cache

class S3StorageClient:
    def __init__(self):
        try:
            cache = get_cache.get()
            config = Config(max_pool_connections=int(cache.get_by_pattern("*:cassandra:retry:max-thread-count")))
            self.client = boto3.client(
                's3',
                region_name=cache.get_by_pattern("*:cassandra:credentials:textract-output-bucket-region"),
                aws_access_key_id=cache.get_by_pattern("*:cassandra:credentials:textract-output-access-key-id"),
                aws_secret_access_key=cache.get_by_pattern("*:cassandra:credentials:textract-output-secret-access-key-id"),
                config=config
            )
            logging.info("AWS S3 client initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize AWS S3 client: {str(e)}")
            raise

def download_file(client, bucket_name, file_key, local_path):
    try:
        client._download_file(bucket_name, file_key, local_path)
    except ClientError as e:
        logging.error(f"S3 download failed: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during S3 download: {str(e)}")
        raise

def upload_file(client, bucket_name, file_key, local_path):
    try:
        client.upload_file(local_path, bucket_name, file_key)
    except ClientError as e:
        logging.error(f"S3 upload failed: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during S3 upload: {str(e)}")
        raise

def delete_file(client, bucket_name, file_key):
    try:
        client.delete_object(Bucket=bucket_name, Key=file_key)
    except ClientError as e:
        logging.error(f"S3 delete failed: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during S3 delete: {str(e)}")
        raise