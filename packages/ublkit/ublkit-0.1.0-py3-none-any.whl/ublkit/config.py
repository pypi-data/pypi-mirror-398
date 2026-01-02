"""
Configuration management for ublkit.

Handles loading, validation, and access to configuration from ublkit.yaml.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from py_logex import logger


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    file: str = "ublkit.log"
    rotation: str = "500 MB"
    retention: str = "10 days"
    compression: str = "zip"


@dataclass
class ProcessingConfig:
    """Processing configuration."""

    max_workers: int = 4
    encoding: str = "utf-8"


@dataclass
class CSVConfig:
    """CSV output configuration."""

    max_records_per_file: int = 50000
    preservation_method: str = "apostrophe"
    key_separator: str = " | "


@dataclass
class OutputConfig:
    """Output directories configuration."""

    summary_dir: str = "./summaries"
    logs_dir: str = "./logs"


@dataclass
class FeaturesConfig:
    """Feature flags configuration."""

    enable_dry_run: bool = False


@dataclass
class UBLKitConfig:
    """
    Main configuration class for ublkit.

    Loads and validates configuration from ublkit.yaml file.
    """

    logging: LoggingConfig
    processing: ProcessingConfig
    csv: CSVConfig
    output: OutputConfig
    features: FeaturesConfig

    @classmethod
    def from_yaml(cls, config_path: str) -> UBLKitConfig:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to ublkit.yaml configuration file

        Returns:
            UBLKitConfig instance with loaded configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
            ValueError: If config file has invalid values
        """
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        logger.debug(f"Loading configuration from: {config_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid configuration file: {config_path}")

        # Parse logging config
        logging_data = data.get("logging", {})
        logging_config = LoggingConfig(
            level=logging_data.get("level", "INFO"),
            file=logging_data.get("file", "ublkit.log"),
            rotation=logging_data.get("rotation", "500 MB"),
            retention=logging_data.get("retention", "10 days"),
            compression=logging_data.get("compression", "zip"),
        )

        # Parse processing config
        processing_data = data.get("processing", {})
        processing_config = ProcessingConfig(
            max_workers=processing_data.get("max_workers", 4),
            encoding=processing_data.get("encoding", "utf-8"),
        )

        # Validate processing config
        if processing_config.max_workers < 1:
            raise ValueError("processing.max_workers must be >= 1")

        valid_encodings = ["utf-8", "utf-16", "iso-8859-1", "ascii", "cp1252"]
        if processing_config.encoding not in valid_encodings:
            raise ValueError(
                f"processing.encoding must be one of: {', '.join(valid_encodings)}"
            )

        # Parse CSV config
        csv_data = data.get("csv", {})
        csv_config = CSVConfig(
            max_records_per_file=csv_data.get("max_records_per_file", 50000),
            preservation_method=csv_data.get("preservation_method", "apostrophe"),
            key_separator=csv_data.get("key_separator", " | "),
        )

        # Validate CSV config
        if csv_config.max_records_per_file < 1:
            raise ValueError("csv.max_records_per_file must be >= 1")

        valid_methods = ["apostrophe", "quotes", "brackets"]
        if csv_config.preservation_method not in valid_methods:
            raise ValueError(
                f"csv.preservation_method must be one of: {', '.join(valid_methods)}"
            )

        # Parse output config
        output_data = data.get("output", {})
        output_config = OutputConfig(
            summary_dir=output_data.get("summary_dir", "./summaries"),
            logs_dir=output_data.get("logs_dir", "./logs"),
        )

        # Parse features config
        features_data = data.get("features", {})
        features_config = FeaturesConfig(
            enable_dry_run=features_data.get("enable_dry_run", False),
        )

        logger.info(f"Configuration loaded successfully from: {config_path}")

        return cls(
            logging=logging_config,
            processing=processing_config,
            csv=csv_config,
            output=output_config,
            features=features_config,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "logging": {
                "level": self.logging.level,
                "file": self.logging.file,
                "rotation": self.logging.rotation,
                "retention": self.logging.retention,
                "compression": self.logging.compression,
            },
            "processing": {
                "max_workers": self.processing.max_workers,
                "encoding": self.processing.encoding,
            },
            "csv": {
                "max_records_per_file": self.csv.max_records_per_file,
                "preservation_method": self.csv.preservation_method,
                "key_separator": self.csv.key_separator,
            },
            "output": {
                "summary_dir": self.output.summary_dir,
                "logs_dir": self.output.logs_dir,
            },
            "features": {
                "enable_dry_run": self.features.enable_dry_run,
            },
        }
