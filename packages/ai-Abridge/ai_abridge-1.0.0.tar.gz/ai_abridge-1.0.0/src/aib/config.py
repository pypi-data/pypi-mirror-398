"""Configuration loading for AI Bridge."""

import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml


DEFAULT_CONFIG = {
    "default_vendor": "gemini",
    "vendors": {}
}

# Environment variable prefixes
ENV_PREFIX = "AIB_"


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file and environment variables.
    
    Priority (highest to lowest):
    1. Environment variables (AIB_<VENDOR>_API_KEY, AIB_<VENDOR>_BASE_URL)
    2. Specified config file
    3. ~/.aib/config.yaml
    4. ./config.yaml
    5. Default values
    
    Args:
        config_path: Optional path to config file.
    
    Returns:
        Configuration dictionary.
    """
    config = DEFAULT_CONFIG.copy()
    config["vendors"] = {}
    
    # Try to load YAML config
    paths_to_try = []
    if config_path:
        paths_to_try.append(Path(config_path))
    paths_to_try.append(Path.home() / ".aib" / "config.yaml")
    paths_to_try.append(Path("config.yaml"))
    
    for path in paths_to_try:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    yaml_config = yaml.safe_load(f)
                    if yaml_config:
                        # Deep merge vendors
                        if "vendors" in yaml_config:
                            config["vendors"].update(yaml_config.pop("vendors"))
                        config.update(yaml_config)
                break
            except Exception as e:
                import warnings
                warnings.warn(f"Failed to parse config file {path}: {e}")
    
    # Override with environment variables
    for vendor in ["kimi", "qwen", "gemini", "openai"]:
        vendor_upper = vendor.upper()
        
        api_key = os.getenv(f"{ENV_PREFIX}{vendor_upper}_API_KEY")
        base_url = os.getenv(f"{ENV_PREFIX}{vendor_upper}_BASE_URL")
        model = os.getenv(f"{ENV_PREFIX}{vendor_upper}_MODEL")
        timeout = os.getenv(f"{ENV_PREFIX}{vendor_upper}_TIMEOUT")
        
        if api_key or base_url or model or timeout:
            if vendor not in config["vendors"]:
                config["vendors"][vendor] = {}
            
            if api_key:
                config["vendors"][vendor]["api_key"] = api_key
            if base_url:
                config["vendors"][vendor]["base_url"] = base_url
            if model:
                config["vendors"][vendor]["model"] = model
            if timeout:
                config["vendors"][vendor]["timeout"] = float(timeout)
    
    return config


def get_vendor_config(config: Dict[str, Any], vendor: str) -> Dict[str, Any]:
    """
    Get configuration for a specific vendor.
    
    Args:
        config: Full configuration dictionary.
        vendor: Vendor name (kimi, qwen, gemini, openai).
    
    Returns:
        Vendor-specific configuration.
    """
    return config.get("vendors", {}).get(vendor.lower(), {})
