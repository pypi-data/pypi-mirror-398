from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pydantic_settings
import yaml

if TYPE_CHECKING:
    import pydantic


class YAMLSettingsMixin(pydantic_settings.PydanticBaseSettingsSource):
    """Addition to allow YAML instead of JSON inside variables"""

    def decode_complex_value(self, field_name: str, field: pydantic.fields.FieldInfo, value: Any) -> Any:
        return yaml.safe_load(value)


class YAMLedEnvSettingsSource(YAMLSettingsMixin, pydantic_settings.EnvSettingsSource):
    """EnvSettings + YAML"""


class YAMLedDotEnvSettingsSource(YAMLSettingsMixin, pydantic_settings.DotEnvSettingsSource):
    """DotEnvSettings + YAML"""


class YAMLedSecretsSettingsSource(YAMLSettingsMixin, pydantic_settings.SecretsSettingsSource):
    """SecretsSettingsSource + YAML"""
