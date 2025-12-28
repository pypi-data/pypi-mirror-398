import re
from typing import Any

from google.cloud import storage  # type: ignore[import-untyped]

from .get_bucket import get_bucket
from .._settings import settings_manager


def get_blob(
    blob_name: str | None = None,
    *,
    placeholders: dict[str, Any] | None = None,
    settings_key: str | None = None,
    auth_settings_key: str | None = None,
    **kwargs: Any,
) -> storage.Blob:
    """
    Get a Google Cloud Storage blob.

    Args:
        blob_name: Full blob name (path). If provided, this takes precedence.
        placeholders: Placeholders for blob_name_pattern formatting.
        settings_key: Configuration key for storage settings.
        auth_settings_key: Configuration key for authentication.
        **kwargs: Additional arguments passed to get_bucket().

    Returns:
        Google Cloud Storage blob.

    Raises:
        ValueError: If blob_name cannot be determined or pattern formatting fails.

    Examples:
        # Direct blob name
        blob = get_blob(blob_name="data/file.json")

        # Using pattern with placeholders
        blob = get_blob(placeholders={"user_id": "123", "basename": "profile.json"})
        # With pattern "users/{user_id}/{basename}" -> "users/123/profile.json"

        # Using fixed pattern from settings (no placeholders)
        blob = get_blob()  # Uses settings.blob_name_pattern if it has no placeholders
    """
    settings = settings_manager.get_settings(settings_key)

    # Priority 1: Explicit blob_name
    if blob_name is not None:
        final_blob_name = blob_name

    # Priority 2: Pattern with placeholders
    elif placeholders is not None:
        if settings.blob_name_pattern is None:
            raise ValueError(
                "placeholders provided but blob_name_pattern is not set in settings"
            )

        try:
            final_blob_name = settings.blob_name_pattern.format(**placeholders)
        except KeyError as e:
            raise ValueError(
                f"Missing placeholder {e} in blob_name_pattern: "
                f"{settings.blob_name_pattern}. "
                f"Available placeholders: {list(placeholders.keys())}"
            ) from e

    # Priority 3: Default pattern from settings
    elif settings.blob_name_pattern is not None:
        final_blob_name = settings.blob_name_pattern

    else:
        raise ValueError(
            "blob_name is not provided, placeholders are not provided, "
            "and blob_name_pattern is not set in settings"
        )

    # Safety check: Ensure no unresolved placeholders remain
    if _has_placeholders(final_blob_name):
        raise ValueError(
            f"Unresolved placeholders found in blob name: {final_blob_name}. "
            f"Please provide placeholders argument to resolve them."
        )

    bucket = get_bucket(settings_key, auth_settings_key=auth_settings_key, **kwargs)
    return bucket.blob(final_blob_name)


def _has_placeholders(pattern: str) -> bool:
    """Check if a pattern contains placeholders like {key}."""
    return bool(re.search(r"\{[^}]+\}", pattern))
