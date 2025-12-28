"""
PayloadForge Logger Module

⚠️  ETHICAL USE ONLY ⚠️

This module provides opt-in action logging for traceability and educational purposes.
Logging helps users understand their testing activities and maintain audit trails.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from payloadforge.disclaimer import get_config_dir


class PayloadLogger:
    """
    Opt-in logger for PayloadForge actions.
    
    This logger helps users:
    - Track their testing activities
    - Maintain audit trails for authorized testing
    - Learn about their payload generation patterns
    """
    
    def __init__(self, enabled: bool = False, log_file: Optional[str] = None):
        """
        Initialize the PayloadForge logger.
        
        Args:
            enabled: Whether logging is enabled (opt-in).
            log_file: Custom log file path. If None, uses default location.
        """
        self.enabled = enabled
        self._logger: Optional[logging.Logger] = None
        
        if log_file:
            self.log_file = Path(log_file)
        else:
            self.log_file = get_config_dir() / "logs" / "payloadforge.log"
        
        if self.enabled:
            self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Set up the Python logger."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._logger = logging.getLogger("payloadforge")
        self._logger.setLevel(logging.INFO)
        
        # File handler
        handler = logging.FileHandler(self.log_file, encoding="utf-8")
        handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        
        self._logger.addHandler(handler)
    
    def enable(self) -> None:
        """Enable logging."""
        self.enabled = True
        if not self._logger:
            self._setup_logger()
    
    def disable(self) -> None:
        """Disable logging."""
        self.enabled = False
    
    def log_action(
        self,
        action: str,
        payload_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a payload generation action.
        
        Args:
            action: The action performed (e.g., "generate", "encode").
            payload_type: Type of payload (e.g., "xss", "sqli").
            details: Additional details about the action.
        """
        if not self.enabled or not self._logger:
            return
        
        log_entry = {
            "action": action,
            "payload_type": payload_type,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self._logger.info(json.dumps(log_entry))
    
    def log_xss(self, subtype: str, encoding: Optional[str] = None) -> None:
        """Log XSS payload generation."""
        self.log_action("generate", "xss", {"subtype": subtype, "encoding": encoding})
    
    def log_sqli(self, db_type: str, attack_type: str) -> None:
        """Log SQL injection payload generation."""
        self.log_action("generate", "sqli", {"db_type": db_type, "attack_type": attack_type})
    
    def log_ssti(self, engine: str) -> None:
        """Log SSTI payload generation."""
        self.log_action("generate", "ssti", {"engine": engine})
    
    def log_cmdi(self, os_type: str, encoding: Optional[str] = None) -> None:
        """Log command injection payload generation."""
        self.log_action("generate", "cmdi", {"os_type": os_type, "encoding": encoding})
    
    def log_encode(self, encoding_type: str, input_length: int) -> None:
        """Log encoding operation."""
        self.log_action("encode", encoding_type, {"input_length": input_length})
    
    def get_log_path(self) -> Path:
        """Get the path to the log file."""
        return self.log_file


# Global logger instance (disabled by default)
logger = PayloadLogger(enabled=False)


def enable_logging(log_file: Optional[str] = None) -> None:
    """
    Enable opt-in logging.
    
    Args:
        log_file: Custom log file path.
    """
    global logger
    if log_file:
        logger = PayloadLogger(enabled=True, log_file=log_file)
    else:
        logger.enable()


def disable_logging() -> None:
    """Disable logging."""
    global logger
    logger.disable()


def is_logging_enabled() -> bool:
    """Check if logging is enabled."""
    return logger.enabled
