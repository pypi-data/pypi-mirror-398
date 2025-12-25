"""
S3-compatible object storage client using boto3.

Features:
- Works with AWS S3, Ceph RGW, MinIO, and other S3-compatible services
- Lazy client initialization (safe for Celery prefork)
- Common operations: upload, download, get, put, delete, list

Usage:
    from investify_utils.s3 import S3Client

    client = S3Client(
        endpoint_url="https://s3.example.com",
        access_key="access_key",
        secret_key="secret_key",
    )

    # Upload file
    client.upload_file("local.pdf", bucket="my-bucket", key="remote.pdf")

    # Get object as bytes
    data = client.get_object("my-bucket", "remote.pdf")

    # Put object from bytes/string
    client.put_object("my-bucket", "file.txt", b"content", content_type="text/plain")
"""

import io
import os
from typing import IO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class S3Client:
    """
    S3-compatible object storage client with lazy initialization.

    Args:
        endpoint_url: S3 endpoint URL (e.g., https://s3.amazonaws.com)
        access_key: AWS access key ID
        secret_key: AWS secret access key
        region: AWS region (default: None)
        **kwargs: Additional boto3 client options
    """

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region: str | None = None,
        **kwargs,
    ):
        self._endpoint_url = endpoint_url
        self._access_key = access_key
        self._secret_key = secret_key
        self._region = region
        self._kwargs = kwargs
        self._client = None

    @property
    def client(self):
        """Lazy client initialization - created on first access."""
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self._endpoint_url,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                region_name=self._region,
                config=Config(signature_version="s3v4"),
                **self._kwargs,
            )
        return self._client

    def list_buckets(self) -> list[str]:
        """List all buckets."""
        response = self.client.list_buckets()
        return [bucket["Name"] for bucket in response["Buckets"]]

    def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        max_keys: int | None = None,
    ) -> list[dict]:
        """
        List objects in a bucket with optional prefix filter.

        Args:
            bucket: Bucket name
            prefix: Filter objects by prefix (e.g., "folder/")
            max_keys: Maximum number of objects to return (None = all)

        Returns:
            List of object metadata dicts with keys: Key, Size, LastModified
        """
        objects = []
        paginator = self.client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                objects.append({
                    "Key": obj["Key"],
                    "Size": obj["Size"],
                    "LastModified": obj["LastModified"],
                })
                if max_keys and len(objects) >= max_keys:
                    return objects

        return objects

    def upload_file(self, file_path: str, bucket: str, key: str | None = None) -> None:
        """
        Upload a local file to S3.

        Args:
            file_path: Local file path
            bucket: Bucket name
            key: Object key (default: basename of file_path)
        """
        if key is None:
            key = os.path.basename(file_path)
        self.client.upload_file(file_path, bucket, key)

    def download_file(self, bucket: str, key: str, file_path: str) -> None:
        """
        Download an object to a local file.

        Args:
            bucket: Bucket name
            key: Object key
            file_path: Local file path to save to
        """
        self.client.download_file(bucket, key, file_path)

    def get_object(self, bucket: str, key: str) -> IO[bytes]:
        """
        Get object content as a file-like BytesIO object.

        Args:
            bucket: Bucket name
            key: Object key

        Returns:
            BytesIO object with object content
        """
        response = self.client.get_object(Bucket=bucket, Key=key)
        return io.BytesIO(response["Body"].read())

    def put_object(
        self,
        bucket: str,
        key: str,
        data: str | bytes | IO[bytes],
        content_type: str | None = None,
        content_disposition: str | None = None,
    ) -> None:
        """
        Upload data directly to S3.

        Args:
            bucket: Bucket name
            key: Object key
            data: Content as string, bytes, or file-like object
            content_type: MIME type (e.g., "application/pdf")
            content_disposition: Content-Disposition header value
        """
        params = {"Bucket": bucket, "Key": key, "Body": data}
        if content_type:
            params["ContentType"] = content_type
        if content_disposition:
            params["ContentDisposition"] = content_disposition
        self.client.put_object(**params)

    def delete_object(self, bucket: str, key: str) -> None:
        """Delete a single object."""
        self.client.delete_object(Bucket=bucket, Key=key)

    def delete_prefix(self, bucket: str, prefix: str) -> int:
        """
        Delete all objects with a given prefix.

        Args:
            bucket: Bucket name
            prefix: Prefix to match (e.g., "folder/" deletes all in folder)

        Returns:
            Number of objects deleted
        """
        deleted_count = 0
        paginator = self.client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            contents = page.get("Contents", [])
            if not contents:
                continue

            delete_keys = [{"Key": obj["Key"]} for obj in contents]
            self.client.delete_objects(Bucket=bucket, Delete={"Objects": delete_keys})
            deleted_count += len(delete_keys)

        return deleted_count

    def exists(self, bucket: str, key: str) -> bool:
        """
        Check if an object exists.

        Args:
            bucket: Bucket name
            key: Object key

        Returns:
            True if object exists, False otherwise
        """
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

