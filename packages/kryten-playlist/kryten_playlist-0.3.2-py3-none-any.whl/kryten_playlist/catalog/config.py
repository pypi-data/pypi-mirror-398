import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import click

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATHS = [
    Path("kryten-enrich.config.json"),                  # Local specific fallback (Priority over generic config.json)
    Path("config.json"),                                # Local fallback
    Path.home() / "kryten-enrich.config.json",          # Windows/User home priority
    Path("/etc/kryten/kryten-enrich/config.json"),      # System priority
    Path("/etc/kryten/kryten-playlist/config.json"),    # Legacy system
]

def load_config(ctx: click.Context, param: click.Parameter, value: str | None) -> str | None:
    """Load configuration from JSON file and set context defaults.
    
    This callback is used by click options to load a config file.
    It searches for default paths if no value is provided.
    """
    config_path = None
    
    if value:
        config_path = Path(value)
    else:
        # Check default locations
        for path in DEFAULT_CONFIG_PATHS:
            if path.exists() and path.is_file():
                config_path = path
                break
    
    if not config_path:
        return value

    try:
        logger.debug("Loading config from %s", config_path)
        # print(f"DEBUG: Loading config from {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Merge with existing defaults if any
        if ctx.default_map is None:
            ctx.default_map = {}
        
        # Only update keys that are not already set (though usually default_map is empty at this point)
        # Note: click uses underscores in function arguments but config might use dashes?
        # Standardize on underscores for internal python, but users might write dashes in JSON.
        # Let's normalize keys to underscores.
        normalized_config = {k.replace("-", "_"): v for k, v in config.items()}
        
        ctx.default_map.update(normalized_config)
        
    except Exception as e:
        logger.warning("Failed to load config file %s: %s", config_path, e)
        if value: # If user explicitly provided a file that failed, raise error
            raise click.BadParameter(f"Could not load config file: {e}")

    return str(config_path)
