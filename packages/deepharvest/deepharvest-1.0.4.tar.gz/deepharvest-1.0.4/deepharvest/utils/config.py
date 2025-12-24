"""
Configuration management
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    with open(config_path) as f:
        return yaml.safe_load(f)


def save_config(config: Dict[str, Any], config_path: str):
    """Save configuration to YAML file"""
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
