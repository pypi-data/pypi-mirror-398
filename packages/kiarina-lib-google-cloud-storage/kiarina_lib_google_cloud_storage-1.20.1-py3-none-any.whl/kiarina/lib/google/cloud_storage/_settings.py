from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class GoogleCloudStorageSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KIARINA_LIB_GOOGLE_CLOUD_STORAGE_")

    bucket_name: str

    blob_name_pattern: str | None = None
    """
    Blob name pattern with placeholders.

    Examples:
        - "data.json" (fixed name)
        - "files/{basename}" (single placeholder)
        - "my-service/{tenant_id}/users/{user_id}/files/{basename}" (multiple placeholders)
    """


settings_manager = SettingsManager(GoogleCloudStorageSettings, multi=True)
