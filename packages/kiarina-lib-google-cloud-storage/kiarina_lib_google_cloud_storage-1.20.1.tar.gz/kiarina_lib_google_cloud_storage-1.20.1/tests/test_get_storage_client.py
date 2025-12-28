from kiarina.lib.google.cloud_storage import settings_manager, get_storage_client


def test_get_storage_client(data_dir, load_settings, request):
    settings = settings_manager.settings
    assert settings.blob_name_pattern is not None

    bucket_name = settings.bucket_name
    blob_name = settings.blob_name_pattern.format(
        tenant_id="kiarina-lib-google-cloud-storage",
        user_id=request.node.name,
        basename="miineko.png",
    )

    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    if not blob.exists():
        blob.upload_from_filename(data_dir / "small" / "miineko_256x256_799b.png")
