"""
Google Cloud Storage handler for video uploads (Standalone version)
"""

import os
import logging
from datetime import timedelta
from google.cloud import storage
from google.api_core import exceptions

logger = logging.getLogger(__name__)


class GCSStorage:
    """Handler for Google Cloud Storage operations"""
    
    def __init__(self, bucket_name: str):
        """Initialize GCS client"""
        try:
            self.client = storage.Client()
            self.bucket_name = bucket_name
            self.bucket = self.client.bucket(self.bucket_name)
            
            # Verify bucket exists
            if not self.bucket.exists():
                logger.error(f"Bucket {self.bucket_name} does not exist!")
                raise ValueError(f"Bucket {self.bucket_name} not found")
            
            logger.info(f"GCS Storage client initialized - Bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {str(e)}")
            raise
    
    def upload_video(
        self,
        video_bytes: bytes,
        filename: str,
        content_type: str = 'video/mp4'
    ) -> str:
        """
        Upload video to Google Cloud Storage
        
        Args:
            video_bytes: Video file as bytes
            filename: Destination filename in GCS (e.g., 'reels/video_123.mp4')
            content_type: MIME type of the video
            
        Returns:
            Signed URL for the uploaded video
        """
        try:
            logger.info(f"Uploading video to GCS: {filename}")
            
            # Create blob
            blob = self.bucket.blob(filename)
            
            # Upload video
            blob.upload_from_string(
                video_bytes,
                content_type=content_type
            )
            
            logger.info(f"Video uploaded successfully: {filename}")
            
            # Generate signed URL (24 hour expiry)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=24),
                method="GET"
            )
            
            logger.info("Video uploaded successfully with signed URL (expires in 24 hours)")
            return url
            
        except exceptions.Forbidden as e:
            logger.error(f"Permission denied uploading to GCS: {e}")
            raise
        except Exception as e:
            logger.error(f"Error uploading video to GCS: {e}")
            raise
    
    def download_video(self, filename: str) -> bytes:
        """
        Download video from Google Cloud Storage
        
        Args:
            filename: Filename in GCS
            
        Returns:
            Video file as bytes
        """
        try:
            logger.info(f"Downloading video from GCS: {filename}")
            
            blob = self.bucket.blob(filename)
            video_bytes = blob.download_as_bytes()
            
            logger.info(f"Video downloaded successfully: {len(video_bytes)} bytes")
            return video_bytes
            
        except Exception as e:
            logger.error(f"Error downloading video from GCS: {e}")
            raise
    
    def delete_video(self, filename: str) -> bool:
        """
        Delete video from Google Cloud Storage
        
        Args:
            filename: Filename in GCS
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Deleting video from GCS: {filename}")
            
            blob = self.bucket.blob(filename)
            blob.delete()
            
            logger.info(f"Video deleted successfully: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting video from GCS: {e}")
            return False
    
    def list_videos(self, prefix: str = '') -> list:
        """
        List videos in GCS bucket
        
        Args:
            prefix: Optional prefix to filter results
            
        Returns:
            List of blob names
        """
        try:
            blobs = self.bucket.list_blobs(prefix=prefix)
            video_list = [blob.name for blob in blobs]
            
            logger.info(f"Found {len(video_list)} videos with prefix '{prefix}'")
            return video_list
            
        except Exception as e:
            logger.error(f"Error listing videos from GCS: {e}")
            return []
