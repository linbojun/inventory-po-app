from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import os

from fastapi import HTTPException

from app.database import settings


@dataclass(frozen=True)
class R2Config:
    endpoint_url: str
    bucket_name: str
    access_key_id: str
    secret_access_key: str
    public_base_url: str


def _get_env(name: str) -> Optional[str]:
    try:
        import os

        value = os.getenv(name)
        if value is None:
            return None
        value = value.strip()
        return value or None
    except Exception:
        return None


def _normalize_r2_endpoint_url(endpoint_url: str, bucket_name: str) -> str:
    """
    Accept either:
      - https://<accountid>.r2.cloudflarestorage.com
      - https://<accountid>.r2.cloudflarestorage.com/<bucket>
    and normalize to the bare endpoint URL required by boto3.
    """
    try:
        from urllib.parse import urlsplit, urlunsplit

        parts = urlsplit(endpoint_url)
        # Drop any path/query/fragment; boto3 endpoint_url should not include bucket path.
        normalized = urlunsplit((parts.scheme, parts.netloc, "", "", ""))
        return normalized.rstrip("/")
    except Exception:
        # Best-effort fallback: strip an obvious trailing "/<bucket>" if present.
        trimmed = endpoint_url.strip().rstrip("/")
        suffix = f"/{bucket_name}".rstrip("/")
        if trimmed.endswith(suffix):
            trimmed = trimmed[: -len(suffix)].rstrip("/")
        return trimmed


def _is_local_storage_forced() -> bool:
    flag = os.getenv("FORCE_LOCAL_IMAGE_STORAGE", "")
    app_mode = os.getenv("APP_MODE", "")
    truthy = {"1", "true", "yes", "y"}
    return flag.lower() in truthy or app_mode.lower() == "dev"


def get_r2_config() -> Optional[R2Config]:
    """
    R2 is enabled when ALL required env vars are present:
      - R2_ENDPOINT_URL
      - R2_BUCKET_NAME
      - R2_ACCESS_KEY_ID
      - R2_SECRET_ACCESS_KEY
      - R2_PUBLIC_BASE_URL (typically your https://pub-...r2.dev)
    """
    if _is_local_storage_forced():
        return None
    endpoint_url = _get_env("R2_ENDPOINT_URL")
    bucket_name = _get_env("R2_BUCKET_NAME")
    access_key_id = _get_env("R2_ACCESS_KEY_ID")
    secret_access_key = _get_env("R2_SECRET_ACCESS_KEY")
    public_base_url = _get_env("R2_PUBLIC_BASE_URL")

    if not all([endpoint_url, bucket_name, access_key_id, secret_access_key, public_base_url]):
        return None

    return R2Config(
        endpoint_url=_normalize_r2_endpoint_url(endpoint_url, bucket_name),
        bucket_name=bucket_name,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        public_base_url=public_base_url.rstrip("/"),
    )


_r2_client = None


def _get_r2_client():
    global _r2_client
    if _r2_client is not None:
        return _r2_client

    cfg = get_r2_config()
    if cfg is None:
        return None

    try:
        import boto3
        from botocore.config import Config
    except Exception:
        # R2 is not usable without boto3 installed.
        return None

    # R2 is S3-compatible but does not use AWS regions; "auto" is the common convention.
    _r2_client = boto3.client(
        "s3",
        endpoint_url=cfg.endpoint_url,
        aws_access_key_id=cfg.access_key_id,
        aws_secret_access_key=cfg.secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )
    return _r2_client


def is_r2_enabled() -> bool:
    return get_r2_config() is not None


def build_public_url_for_key(key: str) -> str:
    cfg = get_r2_config()
    if cfg is None:
        raise RuntimeError("R2 is not configured")
    key = key.lstrip("/")
    return f"{cfg.public_base_url}/{key}"


def key_from_public_url(url: str) -> Optional[str]:
    """
    If the URL belongs to our R2 public base, return its object key.
    Otherwise return None.
    """
    cfg = get_r2_config()
    if cfg is None or not url:
        return None

    base = cfg.public_base_url.rstrip("/")
    if not url.startswith(base + "/"):
        return None

    return url[len(base) + 1 :]


def get_image_bytes(image_url: str) -> Optional[bytes]:
    """
    Fetch image bytes from:
      - local /static/... filesystem (dev)
      - R2 public URL (preferred in production) via S3 API
    """
    if not image_url:
        return None

    # Local dev: /static/<filename>
    if image_url.startswith("/static/"):
        from pathlib import Path

        filename = image_url.replace("/static/", "", 1)
        path = Path(settings.image_dir) / filename
        if not path.exists():
            return None
        try:
            return path.read_bytes()
        except OSError:
            return None

    # R2 public URL: https://pub-...r2.dev/<key>
    key = key_from_public_url(image_url)
    if key:
        client = _get_r2_client()
        cfg = get_r2_config()
        if client is None or cfg is None:
            return None
        try:
            response = client.get_object(Bucket=cfg.bucket_name, Key=key)
            body = response.get("Body")
            return body.read() if body is not None else None
        except Exception:
            return None

    # Unknown URL type (could be external). We don't fetch it.
    return None


def put_image_object(key: str, data: bytes, content_type: Optional[str] = None) -> str:
    """
    Upload image bytes.
    Returns the public URL to store in Product.image_url.
    """
    cfg = get_r2_config()
    client = _get_r2_client()
    if cfg is None or client is None:
        raise HTTPException(
            status_code=500,
            detail="R2 storage is not configured on the server",
        )

    key = key.lstrip("/")
    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type

    try:
        client.put_object(Bucket=cfg.bucket_name, Key=key, Body=data, **extra_args)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to upload image to R2: {exc}")

    return build_public_url_for_key(key)


def delete_image(image_url: Optional[str]):
    """Delete an image from storage (local or R2)."""
    if not image_url:
        return

    # Local dev
    if image_url.startswith("/static/"):
        import os

        filename = image_url.replace("/static/", "", 1)
        file_path = os.path.join(settings.image_dir, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return

    # R2
    key = key_from_public_url(image_url)
    if not key:
        return

    cfg = get_r2_config()
    client = _get_r2_client()
    if cfg is None or client is None:
        return
    try:
        client.delete_object(Bucket=cfg.bucket_name, Key=key)
    except Exception:
        pass

