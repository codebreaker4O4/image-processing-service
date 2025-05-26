from azure.storage.blob import BlobServiceClient, ContentSettings
from app.config import AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME
import uuid

blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

def upload_image_to_azure(image_stream, filename, content_type):
    unique_filename = f"{uuid.uuid4()}_{filename}"
    blob_client = container_client.get_blob_client(unique_filename)
    blob_client.upload_blob(
        image_stream, 
        blob_type="BlockBlob", 
        overwrite=True,
        content_settings=ContentSettings(
            content_type=content_type,  # or image/png
            cache_control="no-cache"
            )
        )
    return unique_filename

def get_image_url(filename):
    return f"https://{blob_service_client.account_name}.blob.core.windows.net/{AZURE_CONTAINER_NAME}/{filename}"
