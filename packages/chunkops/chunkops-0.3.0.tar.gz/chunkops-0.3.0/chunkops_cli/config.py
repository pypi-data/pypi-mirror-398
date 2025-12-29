"""Configuration management for ChunkOps CLI"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class ChunkOpsConfig:
    """ChunkOps configuration"""
    docs_path: str = "./data"
    output_path: str = "./chunkops-reports"
    exact_threshold: float = 1.0
    near_threshold: float = 0.90
    enable_cloud: bool = False
    api_key: Optional[str] = None
    api_url: str = "https://console.chunkops.ai"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChunkOpsConfig":
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


def get_config_path() -> Path:
    """Get the path to chunkops.yaml config file"""
    # Look for config in current directory or parent directories
    current = Path.cwd()
    for path in [current] + list(current.parents):
        config_file = path / "chunkops.yaml"
        if config_file.exists():
            return config_file
    # Default to current directory
    return current / "chunkops.yaml"


def load_config() -> Optional[ChunkOpsConfig]:
    """Load configuration from chunkops.yaml"""
    config_path = get_config_path()
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f) or {}
        return ChunkOpsConfig.from_dict(data)
    except Exception:
        return None


def save_config(config: ChunkOpsConfig) -> Path:
    """Save configuration to chunkops.yaml"""
    config_path = get_config_path()
    
    # Ensure parent directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)
    
    return config_path


def get_credentials_path() -> Path:
    """Get path to credentials file"""
    home = Path.home()
    chunkops_dir = home / ".chunkops"
    chunkops_dir.mkdir(exist_ok=True)
    return chunkops_dir / "credentials"


def load_api_key() -> Optional[str]:
    """Load API key from credentials file"""
    creds_path = get_credentials_path()
    
    if not creds_path.exists():
        return None
    
    try:
        with open(creds_path, 'r') as f:
            data = yaml.safe_load(f) or {}
        return data.get("api_key")
    except Exception:
        return None


def save_api_key(api_key: str) -> None:
    """Save API key to credentials file"""
    creds_path = get_credentials_path()
    
    with open(creds_path, 'w') as f:
        yaml.dump({"api_key": api_key}, f, default_flow_style=False)
    
    # Set restrictive permissions
    os.chmod(creds_path, 0o600)

