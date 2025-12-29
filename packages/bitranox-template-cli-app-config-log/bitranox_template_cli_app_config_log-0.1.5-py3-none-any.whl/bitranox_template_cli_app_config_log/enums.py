"""Enum definitions for type-safe configuration and CLI options.

Provides enumerated types for all fixed string values used throughout the
application, ensuring type safety and eliminating magic string literals.

This module contains:
    - :class:`OutputFormat`: Output format options (human-readable vs JSON).
    - :class:`DeployTarget`: Configuration deployment target layers.

Note:
    Lives in the domain layer. All modules that accept format or target
    parameters should use these enums instead of raw strings.
"""

from __future__ import annotations

from enum import Enum


class OutputFormat(str, Enum):
    """Output format options for configuration display.

    Determines how configuration data is rendered to the user.

    Attributes:
        HUMAN: Human-readable TOML-like format for interactive use.
        JSON: Machine-readable JSON format for scripting and automation.
    """

    HUMAN = "human"
    JSON = "json"


class DeployTarget(str, Enum):
    """Configuration deployment target layers.

    Specifies where configuration files should be deployed in the
    platform-specific directory hierarchy.

    Attributes:
        APP: System-wide application config (requires elevated privileges).
        HOST: System-wide host-specific config (requires elevated privileges).
        USER: User-specific config in the current user's home directory.
    """

    APP = "app"
    HOST = "host"
    USER = "user"


__all__ = [
    "DeployTarget",
    "OutputFormat",
]
