import logging
from typing import Any

import boto3
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict
from pydantic_settings.sources import PydanticBaseEnvSettingsSource

from apppy.env import Env


class AwsSettingsSource(PydanticBaseEnvSettingsSource):
    _logger = logging.getLogger("apppy.aws.AwsSettingsSource")

    def __init__(
        self,
        delegate: PydanticBaseSettingsSource,
    ) -> None:
        """
        This is effectively a wrapper around any settings
        source delegate, which will perform lookups into
        AWS SecretsManager as necessary.
        """
        super().__init__(delegate.settings_cls)
        self._delegate = delegate
        # Note that we blindly attempt to load the secretsmanager
        # client here. We make no guarantees about the authorization
        # of this client. Code which uses this mechanism must take care
        # of the permissions necessary to access the secrets manager.
        self._secrets_client = boto3.client("secretsmanager")

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        value, key, value_is_complex = self._delegate.get_field_value(field, field_name)

        # If the value of the configuration is actually a secretsmanager arn...
        if str(value).startswith("arn:aws:secretsmanager:"):
            # ...lookup the secret
            secret_resp = self._secrets_client.get_secret_value(SecretId=value)
            return secret_resp["SecretString"], key, value_is_complex

        # Otherwise, delegate to the delegate
        return value, key, value_is_complex


class AwsEnv(Env):
    def __init__(self, delegate: Env):
        self._delegate = delegate

    def exists(self) -> bool:
        return self._delegate.exists()

    @property
    def settings_config(self) -> SettingsConfigDict:
        return self._delegate.settings_config

    def settings_sources(
        self,
        env_prefix: str,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return self._delegate.settings_sources(
            env_prefix,
            settings_cls,
            AwsSettingsSource(init_settings),
            AwsSettingsSource(env_settings),
            AwsSettingsSource(dotenv_settings),
            file_secret_settings,
        )
