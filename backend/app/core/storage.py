import boto3
from botocore.client import Config

from app.config import get_settings


class StorageClient:
    """S3-compatible storage client (works with MinIO and AWS S3)."""

    def __init__(self):
        settings = get_settings()
        self.bucket = settings.minio_bucket

        self.client = boto3.client(
            "s3",
            endpoint_url=f"http{'s' if settings.minio_secure else ''}://{settings.minio_endpoint}",
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version="s3v4"),
        )

        # Ensure bucket exists
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Create bucket if it doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except Exception:
            try:
                self.client.create_bucket(Bucket=self.bucket)
            except Exception:
                pass  # Bucket might already exist

    def upload_file(self, key: str, content: bytes) -> str:
        """Upload a file to storage."""
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
        )
        return key

    def download_file(self, key: str) -> bytes:
        """Download a file from storage."""
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def delete_file(self, key: str) -> None:
        """Delete a file from storage."""
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for downloading a file."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )
