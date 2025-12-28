from typing import Any

from google.cloud import storage  # type: ignore[import-untyped]

from .get_storage_client import get_storage_client
from .._settings import settings_manager


def get_bucket(
    settings_key: str | None = None,
    *,
    auth_settings_key: str | None = None,
    **kwargs: Any,
) -> storage.Bucket:
    settings = settings_manager.get_settings(settings_key)
    client = get_storage_client(auth_settings_key, **kwargs)
    return client.bucket(settings.bucket_name)
