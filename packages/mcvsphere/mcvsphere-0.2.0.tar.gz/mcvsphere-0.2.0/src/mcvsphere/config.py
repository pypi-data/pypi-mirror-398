"""Configuration management using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ESXi MCP Server configuration.

    Settings are loaded from (in order of precedence):
    1. Environment variables (highest priority)
    2. Config file (YAML/JSON)
    3. Default values
    """

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # vCenter/ESXi connection settings
    vcenter_host: str = Field(description="vCenter or ESXi server hostname/IP")
    vcenter_user: str = Field(description="Login username")
    vcenter_password: SecretStr = Field(description="Login password")

    # Optional VMware settings
    vcenter_datacenter: str | None = Field(
        default=None, description="Datacenter name (auto-selects first if not specified)"
    )
    vcenter_cluster: str | None = Field(
        default=None, description="Cluster name (auto-selects first if not specified)"
    )
    vcenter_datastore: str | None = Field(
        default=None, description="Datastore name (auto-selects largest if not specified)"
    )
    vcenter_network: str = Field(default="VM Network", description="Default network for VMs")
    vcenter_insecure: bool = Field(default=False, description="Skip SSL certificate verification")

    # MCP server settings
    mcp_api_key: SecretStr | None = Field(
        default=None, description="API key for authentication (optional)"
    )
    mcp_host: str = Field(default="0.0.0.0", description="Server bind address")
    mcp_port: int = Field(default=8080, description="Server port")
    mcp_transport: Literal["stdio", "sse"] = Field(
        default="stdio", description="MCP transport type"
    )

    # Logging settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )
    log_file: Path | None = Field(
        default=None, description="Log file path (logs to console if not specified)"
    )

    @field_validator("vcenter_insecure", mode="before")
    @classmethod
    def parse_bool(cls, v: str | bool) -> bool:
        if isinstance(v, bool):
            return v
        return v.lower() in ("true", "1", "yes", "on")

    @classmethod
    def from_yaml(cls, path: Path) -> "Settings":
        """Load settings from a YAML file, with env vars taking precedence."""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with path.open() as f:
            config_data = yaml.safe_load(f) or {}

        # Map old config keys to new naming convention
        key_mapping = {
            "vcenter_host": "vcenter_host",
            "vcenter_user": "vcenter_user",
            "vcenter_password": "vcenter_password",
            "datacenter": "vcenter_datacenter",
            "cluster": "vcenter_cluster",
            "datastore": "vcenter_datastore",
            "network": "vcenter_network",
            "insecure": "vcenter_insecure",
            "api_key": "mcp_api_key",
            "log_file": "log_file",
            "log_level": "log_level",
        }

        mapped_data = {}
        for old_key, new_key in key_mapping.items():
            if old_key in config_data:
                mapped_data[new_key] = config_data[old_key]

        return cls(**mapped_data)


@lru_cache
def get_settings(config_path: Path | None = None) -> Settings:
    """Get cached settings instance."""
    if config_path:
        return Settings.from_yaml(config_path)
    return Settings()
