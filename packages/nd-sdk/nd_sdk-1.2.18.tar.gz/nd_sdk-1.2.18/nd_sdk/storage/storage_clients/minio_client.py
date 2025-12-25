import logging
from minio import Minio
from minio.error import S3Error
from ....caching.factory import get_cache

class MinioStorageClient:
    def __init__(self):
        try:
            cache = get_cache.get()
            self.client = Minio(
                cache.get_by_pattern("*:cassandra:ip:minio-ip"),
                access_key=cache.get_by_pattern("*:cassandra:credentials:minio-access-key"),
                secret_key=cache.get_by_pattern("*:cassandra:credentials:minio-secret-key"),
                secure=cache.get_by_pattern(":cassandra:credentials:minio-secure-flag")
            )
            logging.info("MinIO client initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize MinIO client: {str(e)}")
            raise

def _download_file(client, bucket_name, file_key, local_path):
    try:
        client.fget_object(bucket_name, file_key, local_path)
    except S3Error as e:
        logging.error(f"MinIO error during download: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during MinIO download: {str(e)}")
        raise

def _upload_file(client, bucket_name, file_key, local_path):
    try:
        client.fput_object(bucket_name, file_key, local_path)
    except S3Error as e:
        logging.error(f"MinIO error during upload: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during MinIO upload: {str(e)}")
        raise

def _delete_file(client, bucket_name, file_key):
    try:
        client.remove_object(bucket_name, file_key)
    except S3Error as e:
        logging.error(f"MinIO error during delete: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during MinIO delete: {str(e)}")
        raise