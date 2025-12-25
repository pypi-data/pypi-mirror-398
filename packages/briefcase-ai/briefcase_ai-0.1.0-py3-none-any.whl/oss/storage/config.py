"""Storage configuration and management system."""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum

from .compression import CompressionType


class RetentionUnit(str, Enum):
    """Units for retention policies."""
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"


@dataclass
class CompressionConfig:
    """Configuration for compression settings."""
    enabled: bool = True
    threshold_bytes: int = 4096  # 4KB
    algorithm: CompressionType = CompressionType.GZIP
    level: int = 6  # Compression level (1-9 for gzip/zlib, 0-16 for lz4)
    prefer_speed: bool = False  # Prefer speed over compression ratio

    def __post_init__(self):
        """Validate configuration."""
        if self.threshold_bytes < 0:
            raise ValueError("Compression threshold must be non-negative")
        if self.level < 0:
            raise ValueError("Compression level must be non-negative")


@dataclass
class RetentionPolicy:
    """Configuration for data retention policies."""
    enabled: bool = True
    max_age_value: int = 30
    max_age_unit: RetentionUnit = RetentionUnit.DAYS
    max_size_gb: Optional[float] = None  # Maximum storage size in GB
    max_snapshots: Optional[int] = None  # Maximum number of snapshots
    cleanup_interval_hours: int = 24  # How often to run cleanup

    def __post_init__(self):
        """Validate configuration."""
        if self.max_age_value <= 0:
            raise ValueError("Retention age must be positive")
        if self.max_size_gb is not None and self.max_size_gb <= 0:
            raise ValueError("Maximum size must be positive")
        if self.max_snapshots is not None and self.max_snapshots <= 0:
            raise ValueError("Maximum snapshots must be positive")
        if self.cleanup_interval_hours <= 0:
            raise ValueError("Cleanup interval must be positive")

    @property
    def max_age_seconds(self) -> int:
        """Get maximum age in seconds."""
        multipliers = {
            RetentionUnit.HOURS: 3600,
            RetentionUnit.DAYS: 86400,
            RetentionUnit.WEEKS: 604800,
            RetentionUnit.MONTHS: 2592000,  # 30 days
            RetentionUnit.YEARS: 31536000,  # 365 days
        }
        return self.max_age_value * multipliers[self.max_age_unit]


@dataclass
class SecurityConfig:
    """Configuration for security settings."""
    enable_encryption: bool = False
    encryption_key_file: Optional[str] = None
    encryption_algorithm: str = "Fernet"
    key_rotation_days: int = 90
    secure_file_permissions: bool = True  # Set restrictive file permissions
    auto_encrypt_sensitive: bool = True  # Automatically encrypt detected sensitive fields
    custom_sensitive_fields: list = field(default_factory=list)  # Additional fields to encrypt

    def __post_init__(self):
        """Validate configuration."""
        if self.enable_encryption and not self.encryption_key_file:
            self.encryption_key_file = "./encryption.key"  # Default path
        if self.key_rotation_days <= 0:
            raise ValueError("Key rotation interval must be positive")
        if not isinstance(self.custom_sensitive_fields, list):
            raise ValueError("Custom sensitive fields must be a list")

    @property
    def custom_sensitive_fields_set(self) -> set:
        """Get custom sensitive fields as a set."""
        return set(self.custom_sensitive_fields)


@dataclass
class PerformanceConfig:
    """Configuration for performance settings."""
    max_inline_size_kb: int = 1024  # 1MB
    batch_size: int = 100  # Batch size for bulk operations
    connection_pool_size: int = 20
    cache_size_mb: int = 512  # Cache size for frequently accessed data
    async_workers: int = 4  # Number of async workers

    def __post_init__(self):
        """Validate configuration."""
        if self.max_inline_size_kb <= 0:
            raise ValueError("Maximum inline size must be positive")
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")
        if self.connection_pool_size <= 0:
            raise ValueError("Connection pool size must be positive")
        if self.cache_size_mb <= 0:
            raise ValueError("Cache size must be positive")
        if self.async_workers <= 0:
            raise ValueError("Number of async workers must be positive")

    @property
    def max_inline_size_bytes(self) -> int:
        """Get maximum inline size in bytes."""
        return self.max_inline_size_kb * 1024


@dataclass
class StorageConfig:
    """Complete storage configuration."""
    # Basic settings
    storage_path: str = "./briefcase-data"
    database_url: str = "sqlite:///./briefcase.db"

    # Feature configurations
    compression: CompressionConfig = field(default_factory=CompressionConfig)
    retention: RetentionPolicy = field(default_factory=RetentionPolicy)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    # Advanced settings
    enable_deduplication: bool = True
    enable_checksums: bool = True
    enable_monitoring: bool = True
    log_level: str = "INFO"

    def __post_init__(self):
        """Validate and normalize configuration."""
        # Ensure paths are absolute
        self.storage_path = str(Path(self.storage_path).absolute())

        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.log_level}")
        self.log_level = self.log_level.upper()

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StorageConfig':
        """Create configuration from dictionary."""
        # Handle nested configurations
        if 'compression' in data and isinstance(data['compression'], dict):
            data['compression'] = CompressionConfig(**data['compression'])

        if 'retention' in data and isinstance(data['retention'], dict):
            data['retention'] = RetentionPolicy(**data['retention'])

        if 'security' in data and isinstance(data['security'], dict):
            data['security'] = SecurityConfig(**data['security'])

        if 'performance' in data and isinstance(data['performance'], dict):
            data['performance'] = PerformanceConfig(**data['performance'])

        return cls(**data)

    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save configuration to JSON file."""
        config_dict = self.to_dict()

        # Convert enums to strings for JSON serialization
        if 'compression' in config_dict:
            config_dict['compression']['algorithm'] = config_dict['compression']['algorithm'].value
        if 'retention' in config_dict:
            config_dict['retention']['max_age_unit'] = config_dict['retention']['max_age_unit'].value

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2)

    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> 'StorageConfig':
        """Load configuration from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Convert string enums back to enum types
        if 'compression' in data and 'algorithm' in data['compression']:
            data['compression']['algorithm'] = CompressionType(data['compression']['algorithm'])
        if 'retention' in data and 'max_age_unit' in data['retention']:
            data['retention']['max_age_unit'] = RetentionUnit(data['retention']['max_age_unit'])

        return cls.from_dict(data)


class StorageConfigManager:
    """Manages storage configuration with environment variable support."""

    DEFAULT_CONFIG_PATHS = [
        "./briefcase-config.json",
        "~/.briefcase/config.json",
        "/etc/briefcase/config.json"
    ]

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._config: Optional[StorageConfig] = None

    def load_config(self) -> StorageConfig:
        """Load configuration from file or environment variables."""
        if self._config is not None:
            return self._config

        config_data = {}

        # Try to load from file
        config_file = self._find_config_file()
        if config_file:
            try:
                self._config = StorageConfig.load_from_file(config_file)
                config_data = self._config.to_dict()
            except Exception as e:
                print(f"Warning: Failed to load config from {config_file}: {e}")

        # Override with environment variables
        env_overrides = self._load_from_environment()
        self._deep_update(config_data, env_overrides)

        # Create final configuration
        if config_data:
            self._config = StorageConfig.from_dict(config_data)
        else:
            self._config = StorageConfig()

        return self._config

    def save_config(self, config: StorageConfig, file_path: Optional[str] = None) -> None:
        """Save configuration to file."""
        save_path = file_path or self.config_path or self.DEFAULT_CONFIG_PATHS[0]
        config.save_to_file(save_path)
        self._config = config

    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file in standard locations."""
        if self.config_path:
            path = Path(self.config_path).expanduser()
            if path.exists():
                return path

        for config_path in self.DEFAULT_CONFIG_PATHS:
            path = Path(config_path).expanduser()
            if path.exists():
                return path

        return None

    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration overrides from environment variables."""
        env_config = {}

        # Basic settings
        if os.getenv('BRIEFCASE_STORAGE_PATH'):
            env_config['storage_path'] = os.getenv('BRIEFCASE_STORAGE_PATH')

        if os.getenv('BRIEFCASE_DATABASE_URL'):
            env_config['database_url'] = os.getenv('BRIEFCASE_DATABASE_URL')

        if os.getenv('BRIEFCASE_LOG_LEVEL'):
            env_config['log_level'] = os.getenv('BRIEFCASE_LOG_LEVEL')

        # Compression settings
        compression = {}
        if os.getenv('BRIEFCASE_COMPRESSION_ENABLED'):
            compression['enabled'] = os.getenv('BRIEFCASE_COMPRESSION_ENABLED').lower() == 'true'

        if os.getenv('BRIEFCASE_COMPRESSION_ALGORITHM'):
            compression['algorithm'] = CompressionType(os.getenv('BRIEFCASE_COMPRESSION_ALGORITHM'))

        if os.getenv('BRIEFCASE_COMPRESSION_THRESHOLD'):
            compression['threshold_bytes'] = int(os.getenv('BRIEFCASE_COMPRESSION_THRESHOLD'))

        if compression:
            env_config['compression'] = compression

        # Security settings
        security = {}
        if os.getenv('BRIEFCASE_ENCRYPTION_ENABLED'):
            security['enable_encryption'] = os.getenv('BRIEFCASE_ENCRYPTION_ENABLED').lower() == 'true'

        if os.getenv('BRIEFCASE_ENCRYPTION_KEY_FILE'):
            security['encryption_key_file'] = os.getenv('BRIEFCASE_ENCRYPTION_KEY_FILE')

        if security:
            env_config['security'] = security

        # Performance settings
        performance = {}
        if os.getenv('BRIEFCASE_MAX_INLINE_SIZE_KB'):
            performance['max_inline_size_kb'] = int(os.getenv('BRIEFCASE_MAX_INLINE_SIZE_KB'))

        if os.getenv('BRIEFCASE_CACHE_SIZE_MB'):
            performance['cache_size_mb'] = int(os.getenv('BRIEFCASE_CACHE_SIZE_MB'))

        if performance:
            env_config['performance'] = performance

        return env_config

    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
        """Deep update dictionary with nested values."""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value


# Global configuration manager instance
_config_manager: Optional[StorageConfigManager] = None


def get_config_manager(config_path: Optional[str] = None) -> StorageConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = StorageConfigManager(config_path)
    return _config_manager


def get_storage_config() -> StorageConfig:
    """Get the current storage configuration."""
    return get_config_manager().load_config()


def create_default_config_file(file_path: str = "./briefcase-config.json") -> None:
    """Create a default configuration file with example settings."""
    config = StorageConfig()

    # Set some example values
    config.compression.enabled = True
    config.compression.algorithm = CompressionType.GZIP
    config.retention.max_age_value = 30
    config.retention.max_size_gb = 10.0
    config.security.enable_encryption = False
    config.performance.max_inline_size_kb = 1024

    config.save_to_file(file_path)
    print(f"Default configuration created at: {file_path}")