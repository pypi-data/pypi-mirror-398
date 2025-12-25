from os.path import split, join
import os
from datetime import datetime

from ..observability.factory import get_logger
from ..caching.factory import get_cache
from ..storage.factory import get_storage
from nd_sdk import initialize_sdk, get_initialized_component
from nd_sdk.caching.factory import get_cache

initialize_sdk.init()
logger = get_logger.get()
cache = get_cache.get()
storage = get_storage.get()

class FileHandler:
    __slots__ = [
        'file_path', 'file_name', 'folder_path',
        'local_file_path', 'local_file_name', 'local_folder_path',
        'pattern_dict_folder_path', 'pattern_dict_bucket_name'
    ]

    def __init__(self, file_path):
        self.file_path = FileHandler.pre_processing(file_path)
        self.folder_path = self.get_folder_path()
        # self.storage_config_settings = self.cache.get("")
        self.local_file_path = self.get_local_file_path()
        self.file_name = self.get_file_name()
        self.local_folder_path = self.get_local_folder()
        # self.pattern_dict_bucket_name = "*:Cassandra:credentials:textract-output-bucket-name"
        self.pattern_dict_bucket_name = {
            "service": "*",  # Match any service
            "provider": "cassandra",
            "category": "credentials",
            "identifier": "textract-output-bucket-name"
        }

    def get_file_name(self):
        file_properties = split(self.file_path)
        self.file_name = file_properties[1]
        return self.file_name

    def get_folder_path(self):
        file_properties = split(self.file_path)
        self.local_folder_path = file_properties[0]
        return self.local_folder_path

    def get_parent_folder_path(self):
        folder_path = self.get_folder_path()
        parent_path = os.path.dirname(folder_path)
        return parent_path

    def clear(self):
        if not os.path.exists(self.local_file_path):
            logger.error(f"[FileHandler] Local file not found: {self.local_file_path}")
            return
        try:
            os.remove(self.local_file_path)
            logger.info(f"[FileHandler] Deleted local file: {self.local_file_path}")
        except Exception as e:
            logger.error(f"[FileHandler] Failed to delete file {self.local_file_path}: {str(e)}")

    @staticmethod
    def clear_all(paths):
        logger = get_logger.get()
        errors = []
        for path in paths:
            if not os.path.exists(path):
                errors.append(path)
                continue
            os.remove(path)
        if errors:
            logger.error(f"Local File Paths: {errors} not found")

    def get_local_folder(self):
        pattern = ":cassandra:credentials:local-folder-save-path"
        pattern_dict = {
            "service": "*",  # Match any service
            "provider": "cassandra",
            "category": "file-path",
            "identifier": "local-folder-save-path"
        }
        folder_name = cache.get_by_dict(pattern_dict)
        today = str(datetime.now())
        folder_name = folder_name.replace("[TodaysDate]", today.replace("-", "").replace(":", "").replace(".", "").replace(" ", ""))
        folder_name = join(cache.get_by_dict(pattern_dict), folder_name)
        self.local_folder_path = FileHandler.pre_processing(join(folder_name,self.folder_path))
        self.make_local_directory()
        return self.local_folder_path

    def get_local_file_path(self):
        self.local_file_path = FileHandler.pre_processing(join(self.get_local_folder(), self.get_file_name()))
        return self.local_file_path

    def make_directory(self):
        if not os.path.isdir(self.file_path):
            os.makedirs(self.file_path)

    def make_local_directory(self):
        if not os.path.isdir(self.local_folder_path):
            os.makedirs(self.local_folder_path)

    @staticmethod
    def join_file_path(root, file_name):
        return join(root, file_name)

    @staticmethod
    def pre_processing(path):
        return str(path).replace("\\", "/")

    def download(self):
        # @logger.set_logger(description='Download Function')
        def _inner_download():
            storage.DOWNLOAD_FILE(
                cache.get_by_dict(self.pattern_dict_bucket_name),
                self.file_path,
                self.get_local_file_path()
            )
        return _inner_download()

    def upload(self):
        # @logger.set_logger(description='Upload Function')
        def _inner_upload():
            storage.UPLOAD_FILE(
                cache.get_by_dict(self.pattern_dict_bucket_name),
                FileHandler.pre_processing(self.file_path),
                self.local_file_path
            )
        return _inner_upload()

    def delete(self):
        @logger.set_logger(description='Delete Function')
        def _inner_delete():
            storage.DELETE_FILE(
                cache.get_by_dict(self.pattern_dict_bucket_name),
                self.file_path
            )

        return _inner_delete()

    @classmethod
    def download_standalone(cls, file_path, local_file_path, cache):
        # pattern_dict_bucket_name = ":cassandra:credentials:textract-output-bucket-name"
        pattern_dict_bucket_name = {
            "service": "*",  # Match any service
            "provider": "cassandra",
            "category": "credentials",
            "identifier": "textract-output-bucket-name"
        }
        @logger.set_logger(description='Download Standalone Function')
        def _inner_download():
                storage.DOWNLOAD_FILE(
                cache.get_by_dict(pattern_dict_bucket_name),
                file_path,
                local_file_path
            )
        return _inner_download()

    @classmethod
    def upload_standalone(cls, local_file_path, file_path, cache):
        # pattern_dict_bucket_name = "*:Cassandra:credentials:textract-output-bucket-name"
        pattern_dict_bucket_name = {
            "service": "*",  # Match any service
            "provider": "cassandra",
            "category": "credentials",
            "identifier": "textract-output-bucket-name"
        }
        @logger.set_logger(description='Upload Standalone Function')
        def _inner_upload():
                storage.UPLOAD_FILE(
                cache.get_by_dict(pattern_dict_bucket_name),
                file_path,
                local_file_path
            )
        return _inner_upload()