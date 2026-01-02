"""Test utilities for use case modules."""

import sys
from enum import Enum
from pathlib import Path
from typing import Type, TypeVar

from aiq_platform_api.core.logger import AttackIQLogger

logger = AttackIQLogger.get_logger(__name__)

T = TypeVar("T", bound=Enum)


def require_env(platform_url: str, api_token: str) -> None:
    """Validate required environment variables are set. Exits if missing."""
    if not platform_url or not api_token:
        logger.error("Missing ATTACKIQ_PLATFORM_URL or ATTACKIQ_PLATFORM_API_TOKEN")
        sys.exit(1)


def parse_test_choice(enum_class: Type[T]) -> T:
    """Parse command-line argument as enum value. Exits if invalid."""
    script_name = Path(sys.argv[0]).name
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        try:
            return enum_class(arg.lower())
        except ValueError:
            logger.error(f"Invalid test choice: '{arg}'")
            logger.error(f"Valid choices: {[c.value for c in enum_class]}")
            sys.exit(1)
    else:
        logger.error(f"Usage: python {script_name} <test_choice>")
        logger.error(f"Valid choices: {[c.value for c in enum_class]}")
        sys.exit(1)
