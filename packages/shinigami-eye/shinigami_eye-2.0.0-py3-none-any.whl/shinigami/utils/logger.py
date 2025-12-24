"""
Logger Module - Advanced logging with color support
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from shinigami.utils.ascii_art import Colors


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support"""
    
    COLORS = {
        'DEBUG': Colors.BLUE,
        'INFO': Colors.CYAN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.BOLD + Colors.RED
    }
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Colors.END}"
        return super().format(record)


class ShinigamiLogger:
    """Advanced logger for SHINIGAMI-EYE framework"""
    
    def __init__(self, name: str = "SHINIGAMI", log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            fmt='%(levelname)s | %(asctime)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                fmt='%(levelname)s | %(asctime)s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)
    
    def success(self, message: str):
        """Log success message"""
        self.logger.info(f"{Colors.GREEN}✓{Colors.END} {message}")
    
    def scan(self, message: str):
        """Log scan activity"""
        self.logger.info(f"{Colors.MAGENTA}◉{Colors.END} {message}")


# Global logger instance
logger = ShinigamiLogger()


def get_logger(name: str = "SHINIGAMI", log_file: Optional[str] = None) -> ShinigamiLogger:
    """Get or create a logger instance"""
    return ShinigamiLogger(name, log_file)
