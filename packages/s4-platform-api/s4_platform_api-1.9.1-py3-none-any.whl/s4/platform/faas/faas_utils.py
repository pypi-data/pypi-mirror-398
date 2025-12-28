# Copyright 2022 Semaphore Solutions
# ---------------------------------------------------------------------------
import atexit
import gzip
import logging
import os
from typing import Optional

log = logging.getLogger(__name__)


class FaasUtils:
        
    @staticmethod
    def get_env_var(name: str, default_value: Optional[str] = None, hide_value: Optional[bool] = False) -> str:
        value = os.environ.get(name)

        if value:
            log.debug("Environment variable %s found. Using value: %s", name, "[Hidden]" if hide_value else value)
        else:
            if default_value is None:
                raise ValueError(f"A required environment variable was not found: {name}")
            log.debug("Environment variable %s not found. Using default value: %s", name, default_value)
            value = default_value

        return value
