from abc import ABC, abstractmethod

class StorageFactory(ABC):
    def __init__(self, credentials: dict):
        self.credentials = credentials
        self.client_wrapper = self._initialize_client()

    @abstractmethod
    def _initialize_client(self):
        pass

    @abstractmethod
    def DOWNLOAD_FILE(self, bucket_name, file_path, local_file_path):
        pass

    @abstractmethod
    def UPLOAD_FILE(self, bucket, file_path, local_file_path):
        pass

    @abstractmethod
    def DELETE_FILE(self, bucket, remote_path):
        pass