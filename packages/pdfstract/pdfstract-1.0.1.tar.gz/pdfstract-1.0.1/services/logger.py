"""
Centralized logging configuration using Loguru.
All logs go to stdout only (no file logging).
"""
from loguru import logger
import sys

# Remove default handler
logger.remove()

# Add stdout handler with nice formatting
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# Export the logger instance
__all__ = ["logger"]

