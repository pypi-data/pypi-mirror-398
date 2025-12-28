import platform
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class RunContextSettings(BaseSettings):
    """
    Run Context Settings
    """

    model_config = SettingsConfigDict(env_prefix="KIARINA_LLM_RUN_CONTEXT_")

    app_author: str = "kiarina"
    """
    Default value for the application author.

    Alphanumeric characters, dots, underscores, hyphens, and spaces are allowed.
    Leading and trailing dots, as well as spaces, are not allowed.
    """

    app_name: str = "kiarina-llm"
    """
    Default value for the application name.

    Alphanumeric characters, dots, underscores, hyphens, and spaces are allowed.
    Leading and trailing dots, as well as spaces, are not allowed.
    """

    tenant_id: str = ""
    """
    Default value for the tenant ID.

    Alphanumeric characters, underscores, and hyphens are allowed.
    """

    user_id: str = ""
    """
    Default value for the user ID.

    Alphanumeric characters, underscores, and hyphens are allowed.
    """

    agent_id: str = ""
    """
    Default value for the agent ID.

    Alphanumeric characters, underscores, and hyphens are allowed.
    """

    runner_id: str = Field(default_factory=lambda: platform.system().lower())
    """
    Default value for the runner ID.

    Alphanumeric characters, underscores, and hyphens are allowed.
    """

    time_zone: str = "UTC"
    """
    Default value for the time zone.

    IANA time zone names are used.
    Example: "Asia/Tokyo"
    """

    language: str = "en"
    """
    Default value for the language.

    ISO 639-1 codes are used.
    Example: "ja"
    """

    currency: str = "USD"
    """
    Default value for the currency code.

    ISO 4217 currency code (3 letters).
    Example: "USD" (US Dollar), "JPY" (Japanese Yen), "EUR" (Euro)
    """

    metadata: dict[str, Any] = Field(default_factory=dict)
    """Default value for the metadata."""


settings_manager = SettingsManager(RunContextSettings)
