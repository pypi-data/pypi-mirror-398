import pytest

from kiarina.lib.google.cloud_storage import get_blob, settings_manager


def test_get_blob_with_blob_name(data_dir, load_settings, request):
    settings = settings_manager.settings

    assert settings.blob_name_pattern is not None

    blob_name = settings.blob_name_pattern.format(
        tenant_id="kiarina-lib-google-cloud-storage",
        user_id=request.node.name,
        basename="miineko.png",
    )

    blob = get_blob(blob_name)

    if not blob.exists():
        blob.upload_from_filename(data_dir / "small" / "miineko_256x256_799b.png")


def test_get_blob_with_placeholders(data_dir, load_settings, request):
    blob = get_blob(
        placeholders={
            "tenant_id": "kiarina-lib-google-cloud-storage",
            "user_id": request.node.name,
            "basename": "miineko.png",
        }
    )

    if not blob.exists():
        blob.upload_from_filename(data_dir / "small" / "miineko_256x256_799b.png")


def test_get_blob_with_placeholders_but_no_pattern(data_dir, load_settings, request):
    with pytest.raises(
        ValueError,
        match="placeholders provided but blob_name_pattern is not set in settings",
    ):
        get_blob(
            placeholders={
                "user_id": request.node.name,
                "basename": "miineko.png",
            },
            settings_key="no_blob_name_pattern",
        )


def test_get_blob_with_not_enough_placeholders(data_dir, load_settings, request):
    with pytest.raises(
        ValueError, match="Missing placeholder 'basename' in blob_name_pattern"
    ):
        get_blob(
            placeholders={
                "tenant_id": "kiarina-lib-google-cloud-storage",
                "user_id": request.node.name,
            }
        )


def test_get_blob_with_fixed_pattern(data_dir, load_settings, request):
    blob = get_blob(settings_key="fixed")

    if not blob.exists():
        blob.upload_from_filename(data_dir / "small" / "miineko_256x256_799b.png")


def test_not_enough_placeholders(data_dir, load_settings, request):
    with pytest.raises(
        ValueError,
        match="Unresolved placeholders found in blob name",
    ):
        get_blob()


def test_no_blob_name_provided(data_dir, load_settings, request):
    with pytest.raises(
        ValueError,
        match="blob_name is not provided, placeholders are not provided, and blob_name_pattern is not set in settings",
    ):
        get_blob(settings_key="no_blob_name_pattern")
