"""
Google Cloud Storage client utilities with proper error handling

This module provides GCS client functionality and common operations that can be
used across all DARX services.
"""
import os
import logging
from typing import Optional, List, IO
from google.cloud import storage
from google.cloud.storage import Bucket, Blob

# Module-level logger
logger = logging.getLogger(__name__)

# Storage client (singleton pattern)
_storage_client: Optional[storage.Client] = None


def get_storage_client(project_id: Optional[str] = None) -> Optional[storage.Client]:
    """
    Get or create Google Cloud Storage client (singleton).

    Args:
        project_id: Optional GCP project ID. If not provided, uses GOOGLE_CLOUD_PROJECT env var.

    Returns:
        Client: Google Cloud Storage client instance, or None if initialization fails

    Raises:
        Exception: If client initialization fails
    """
    global _storage_client

    if _storage_client is None:
        if not project_id:
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT')

        if not project_id:
            logger.warning("GCP project ID not found in environment")
            return None

        try:
            _storage_client = storage.Client(project=project_id)
            logger.info(
                "Cloud Storage client initialized successfully",
                extra={'project_id': project_id}
            )
        except Exception as e:
            logger.error(
                "Failed to initialize Cloud Storage client",
                exc_info=True,
                extra={'error': str(e), 'project_id': project_id}
            )
            raise

    return _storage_client


def upload_to_gcs(
    bucket_name: str,
    destination_blob_name: str,
    content: str,
    content_type: str = 'text/plain'
) -> bool:
    """
    Upload string content to Google Cloud Storage.

    Args:
        bucket_name: Name of the GCS bucket
        destination_blob_name: Destination path in bucket (e.g., 'folder/file.txt')
        content: String content to upload
        content_type: MIME type of the content

    Returns:
        True if upload successful, False otherwise
    """
    client = get_storage_client()
    if not client:
        logger.error("Storage client not initialized - cannot upload")
        return False

    try:
        logger.info(
            "Uploading to GCS",
            extra={
                'bucket': bucket_name,
                'blob': destination_blob_name,
                'size': len(content)
            }
        )

        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(content, content_type=content_type)

        logger.info(
            "Upload successful",
            extra={
                'bucket': bucket_name,
                'blob': destination_blob_name,
                'public_url': blob.public_url
            }
        )
        return True

    except Exception as e:
        logger.error(
            "Failed to upload to GCS",
            exc_info=True,
            extra={
                'bucket': bucket_name,
                'blob': destination_blob_name
            }
        )
        return False


def upload_file_to_gcs(
    bucket_name: str,
    destination_blob_name: str,
    source_file_path: str
) -> bool:
    """
    Upload a local file to Google Cloud Storage.

    Args:
        bucket_name: Name of the GCS bucket
        destination_blob_name: Destination path in bucket
        source_file_path: Local file path to upload

    Returns:
        True if upload successful, False otherwise
    """
    client = get_storage_client()
    if not client:
        logger.error("Storage client not initialized - cannot upload file")
        return False

    try:
        logger.info(
            "Uploading file to GCS",
            extra={
                'bucket': bucket_name,
                'blob': destination_blob_name,
                'source': source_file_path
            }
        )

        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_path)

        logger.info(
            "File upload successful",
            extra={
                'bucket': bucket_name,
                'blob': destination_blob_name,
                'public_url': blob.public_url
            }
        )
        return True

    except Exception as e:
        logger.error(
            "Failed to upload file to GCS",
            exc_info=True,
            extra={
                'bucket': bucket_name,
                'blob': destination_blob_name,
                'source': source_file_path
            }
        )
        return False


def download_from_gcs(
    bucket_name: str,
    source_blob_name: str
) -> Optional[str]:
    """
    Download blob content from Google Cloud Storage as string.

    Args:
        bucket_name: Name of the GCS bucket
        source_blob_name: Source blob path in bucket

    Returns:
        String content of the blob, or None if download fails
    """
    client = get_storage_client()
    if not client:
        logger.error("Storage client not initialized - cannot download")
        return None

    try:
        logger.info(
            "Downloading from GCS",
            extra={
                'bucket': bucket_name,
                'blob': source_blob_name
            }
        )

        bucket = client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        content = blob.download_as_text()

        logger.info(
            "Download successful",
            extra={
                'bucket': bucket_name,
                'blob': source_blob_name,
                'size': len(content)
            }
        )
        return content

    except Exception as e:
        logger.error(
            "Failed to download from GCS",
            exc_info=True,
            extra={
                'bucket': bucket_name,
                'blob': source_blob_name
            }
        )
        return None


def list_blobs(
    bucket_name: str,
    prefix: Optional[str] = None,
    delimiter: Optional[str] = None
) -> Optional[List[str]]:
    """
    List blobs in a GCS bucket with optional prefix filter.

    Args:
        bucket_name: Name of the GCS bucket
        prefix: Optional prefix filter (e.g., 'folder/')
        delimiter: Optional delimiter for directory-like listing

    Returns:
        List of blob names, or None if operation fails
    """
    client = get_storage_client()
    if not client:
        logger.error("Storage client not initialized - cannot list blobs")
        return None

    try:
        logger.info(
            "Listing blobs in GCS",
            extra={
                'bucket': bucket_name,
                'prefix': prefix,
                'delimiter': delimiter
            }
        )

        bucket = client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix, delimiter=delimiter)
        blob_names = [blob.name for blob in blobs]

        logger.info(
            "List successful",
            extra={
                'bucket': bucket_name,
                'count': len(blob_names)
            }
        )
        return blob_names

    except Exception as e:
        logger.error(
            "Failed to list blobs in GCS",
            exc_info=True,
            extra={'bucket': bucket_name}
        )
        return None


def delete_blob(
    bucket_name: str,
    blob_name: str
) -> bool:
    """
    Delete a blob from Google Cloud Storage.

    Args:
        bucket_name: Name of the GCS bucket
        blob_name: Name of the blob to delete

    Returns:
        True if deletion successful, False otherwise
    """
    client = get_storage_client()
    if not client:
        logger.error("Storage client not initialized - cannot delete blob")
        return False

    try:
        logger.info(
            "Deleting blob from GCS",
            extra={
                'bucket': bucket_name,
                'blob': blob_name
            }
        )

        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()

        logger.info(
            "Delete successful",
            extra={
                'bucket': bucket_name,
                'blob': blob_name
            }
        )
        return True

    except Exception as e:
        logger.error(
            "Failed to delete blob from GCS",
            exc_info=True,
            extra={
                'bucket': bucket_name,
                'blob': blob_name
            }
        )
        return False


def reset_storage_client():
    """
    Reset the storage client singleton.

    Useful for testing or when project changes.
    """
    global _storage_client
    _storage_client = None
    logger.info("Storage client reset")
