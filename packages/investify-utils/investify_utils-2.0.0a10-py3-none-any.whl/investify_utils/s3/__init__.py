"""
S3-compatible object storage client.

Usage:
    from investify_utils.s3 import S3Client
"""


def __getattr__(name: str):
    """Lazy import to avoid loading boto3 if not needed."""
    if name == "S3Client":
        from investify_utils.s3.sync_client import S3Client

        return S3Client
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["S3Client"]
