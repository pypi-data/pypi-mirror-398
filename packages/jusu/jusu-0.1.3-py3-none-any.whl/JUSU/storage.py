"""Storage helpers: presign helpers for cloud uploads (S3 support).

This module provides a tiny optional helper that wraps AWS S3 presign calls.
It does NOT store uploaded content — the server only issues temporary presigned
upload credentials and may only store returned object keys/URLs if strictly
necessary (and per the project's privacy policy).
"""
from __future__ import annotations

from typing import Any, Dict


def generate_s3_presigned_post(client: Any, bucket: str, key: str, expires_in: int = 3600) -> Dict[str, Any]:
    """Generate a presigned POST dict for uploading directly to S3.

    `client` is expected to be a boto3 S3 client-like object with
    `generate_presigned_post` method. This function intentionally does not
    import boto3 so it remains optional.
    """
    try:
        return client.generate_presigned_post(bucket, key, ExpiresIn=expires_in)
    except AttributeError as exc:
        raise RuntimeError("provided client does not support generate_presigned_post") from exc


__all__ = ["generate_s3_presigned_post"]