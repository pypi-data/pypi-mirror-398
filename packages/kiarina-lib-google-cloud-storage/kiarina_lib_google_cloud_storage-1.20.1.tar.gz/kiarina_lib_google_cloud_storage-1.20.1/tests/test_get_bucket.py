from kiarina.lib.google.cloud_storage import get_bucket, settings_manager


def test_get_bucket(data_dir, load_settings, request):
    settings = settings_manager.settings
    assert settings.blob_name_pattern is not None

    blob_name = settings.blob_name_pattern.format(
        tenant_id="kiarina-lib-google-cloud-storage",
        user_id=request.node.name,
        basename="miineko.png",
    )

    bucket = get_bucket()
    blob = bucket.blob(blob_name)

    if not blob.exists():
        blob.upload_from_filename(data_dir / "small" / "miineko_256x256_799b.png")
