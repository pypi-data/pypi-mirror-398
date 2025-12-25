from ..caching.factory import get_cache
from ..utils.singleton import singleton


@singleton
def get_storage():
    file_storage_type_pattern_dict = {
            "service": "*",  # Match any service
            "provider": "cassandra",
            "category": "credentials",
            "identifier": "file-storage-type"
    }
    cache = get_cache.get()
    provider = cache.get_by_dict(file_storage_type_pattern_dict)
    if provider.lower() == "azureblob":
        from .storage_factory.azure_factory import AzureBlobStorageFactory
        return AzureBlobStorageFactory()
    if provider.lower() == "awss3":
        from .storage_factory.s3_factory import S3StorageFactory
        return S3StorageFactory()
    if provider.lower() == "minio":
        from .storage_factory.minio_factory import MinioStorageFactory
        return MinioStorageFactory()
    raise ValueError(f"Unknown storage provider: {provider}")
