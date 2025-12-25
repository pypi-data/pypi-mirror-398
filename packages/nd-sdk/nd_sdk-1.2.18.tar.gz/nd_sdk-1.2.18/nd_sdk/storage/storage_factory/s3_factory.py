from ..storage.storage_clients.s3_client import S3StorageClient
from ..storage.storage_clients.s3_client import download_file, upload_file, delete_file


class S3StorageFactory:
    def __init__(self):
        self.client_wrapper = self._initialize_client()

    def _initialize_client(self):
        try:
            return S3StorageClient().client
        except ImportError as e:
            raise ImportError(f"Module import failed for awss3: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to initialize storage client for awss3: {str(e)}")

    def DOWNLOAD_FILE(self, bucket_name, file_path, local_file_path):
        download_file(self.client_wrapper, bucket_name, file_path, local_file_path)

    def UPLOAD_FILE(self, bucket, file_path, local_file_path):
        upload_file(self.client_wrapper, bucket, file_path, local_file_path)

    def DELETE_FILE(self, bucket, remote_path):
        delete_file(self.client_wrapper, bucket, remote_path)