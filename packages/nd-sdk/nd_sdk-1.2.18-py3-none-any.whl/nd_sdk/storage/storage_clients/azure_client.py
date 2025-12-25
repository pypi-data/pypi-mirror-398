import logging
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError, ResourceNotFoundError, HttpResponseError
from nd_sdk.caching.factory import get_cache

class AzureStorageClient:
    def __init__(self):
        try:
            cache = get_cache.get()
            account_url = f"https://{cache.get_by_pattern('*:cassandra:credentials:textract-azure-account-name')}.blob.core.windows.net"
            self.client = BlobServiceClient(account_url=account_url, credential=cache.get_by_pattern('*:cassandra:credentials:textract-azure-account-key'))
            logging.info("Azure Blob client initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Azure Blob client: {str(e)}")
            raise

def download_file(client, container_name, blob_name, local_path):
    try:
        blob_client = client.get_blob_client(container=container_name, blob=blob_name)
        with open(local_path, "wb") as local_file:
            blob_data = blob_client.download_blob()
            blob_data.readinto(local_file)
    except ResourceNotFoundError:
        logging.error(f"Blob not found: {blob_name} in container {container_name}.")
        raise
    except HttpResponseError as e:
        logging.error(f"HTTP error during Azure download: {str(e)}")
        raise
    except AzureError as e:
        logging.error(f"Azure error during download: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during Azure download: {str(e)}")
        raise

def upload_file(client, container_name, blob_name, local_path):
    try:
        blob_client = client.get_blob_client(container=container_name, blob=blob_name)
        with open(local_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
    except AzureError as e:
        logging.error(f"Azure error during upload: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during Azure upload: {str(e)}")
        raise

def delete_file(client, container_name, blob_name):
    try:
        container_client = client.get_container_client(container_name)
        container_client.delete_blob(blob_name)
    except AzureError as e:
        logging.error(f"Azure error during delete: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during Azure delete: {str(e)}")
        raise