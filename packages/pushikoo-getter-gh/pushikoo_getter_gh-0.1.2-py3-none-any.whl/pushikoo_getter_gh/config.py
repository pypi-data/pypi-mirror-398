from pushikoo_interface import GetterConfig, GetterInstanceConfig
from pydantic import Field


class AdapterConfig(GetterConfig):
    """GitHub adapter-level configuration."""

    auth: dict[str, str] = Field(
        default_factory=lambda: {"default": ""},
        description="GitHub API tokens. Key is the token name, value is the token.",
    )


class InstanceConfig(GetterInstanceConfig):
    """Per-instance configuration for GitHub getter."""

    repo: str = Field(
        default="",
        description="Repository path, e.g. 'github/gitignore'",
    )
    commit: bool = Field(default=True, description="Enable commit monitoring")
    auth: str = Field(
        default="default", description="Token name to use from adapter config"
    )
