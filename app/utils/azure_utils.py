from distutils import extension
from hmac import new
from azure.storage.blob import BlobServiceClient, ContentSettings
from app.config import AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME
from PIL import Image
import uuid
import io

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

def downlaod_image_from_azure(filename):
    blob_client = container_client.get_blob_client(filename)
    blob_data = blob_client.download_blob().readall()
    return Image.open(io.BytesIO(blob_data))

def upload_pil_image_to_azure(pil_image, filename, format='JPEG', quality=95):
    """ Upload a PIL Image to Azure Blob Storage."""
    
    img_byte_arr = io.BytesIO()
    if format.upper() == 'PNG':
        pil_image.save(img_byte_arr, format='PNG')
        content_type = 'image/png'
    else:
        pil_image.save(img_byte_arr, format='JPEG', quality=quality)
        content_type = 'image/jpeg'
        
    img_byte_arr.seek(0)
    
    # Upload the image byte array to Azure Blob Storage
    blob_client = container_client.get_blob_client(filename)
    blob_client.upload_blob(
        img_byte_arr.getvalue(),
        blob_type="BlockBlob",
        overwrite=True,
        content_settings=ContentSettings(
            content_type=content_type,
            cache_control="no-cache"
        )
    )
    return filename

def delete_image_from_azure(filename):
    """Delete an image from Azure Blob Storage."""
    blob_client = container_client.get_blob_client(filename)
    try:
        blob_client.delete_blob()
        return True
    except Exception as e:
        print(f"Error deleting blob: {e}")
        return False
    
def rename_image_in_azure(old_filename, new_filename):
    """Rename an image in Azure Blob Storage."""
    old_blob_client = container_client.get_blob_client(old_filename)
    new_blob_client = container_client.get_blob_client(new_filename)
    
    try:
        # Download the old blob
        blob_data = old_blob_client.download_blob().readall()
        
        # Upload it as a new blob with the new name
        new_blob_client.upload_blob(
            blob_data,
            blob_type="BlockBlob",
            overwrite=True,
            content_settings=old_blob_client.get_blob_properties().content_settings
        )
        
        # Delete the old blob
        old_blob_client.delete_blob()
        return new_filename
    except Exception as e:
        print(f"Error renaming blob: {e}")
        return None
        
def list_user_images(user_prefix=""):
    """List all images in the Azure Blob Storage container."""
    try:
        blobs = container_client.list_blobs(name_starts_with=user_prefix)
        return [blob.name for blob in blobs]
    except Exception as e:
        print(f"Error listing blobs: {e}")
        return []
    
def transform_image_in_cloud(filename, width=None, height=None, angle=0):
    """Transform an image in Azure Blob Storage."""
    try:
        # Download the image
        pil_image = downlaod_image_from_azure(filename)
        
        # Resize if width and height are provided
        if width and height:
            pil_image = pil_image.resize((width, height), Image.Resampling.LANCZOS)
        
        # Rotate if angle is provided
        if angle and angle != 0:
            pil_image = pil_image.rotate(angle, expand=True,fillcolor='white')  
            

        base_name = filename.rsplit('.', 1)[0]
        extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
        
        new_filename = f"{base_name}_transformed_{uuid.uuid4().hex[:8]}.{extension}"

        
        # Upload the transformed image back to Azure Blob Storage
        upload_pil_image_to_azure(pil_image, new_filename)
        
        return new_filename
    except Exception as e:
        print(f"Error transforming image: {e}")
        return ""