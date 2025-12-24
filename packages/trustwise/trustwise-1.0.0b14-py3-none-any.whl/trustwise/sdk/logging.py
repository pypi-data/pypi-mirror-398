"""
Logging configuration for Trustwise SDK.

This module handles the setup of debug logging based on environment variables.
"""

import logging
import os


def setup_logging(logger_name: str = "trustwise.sdk") -> logging.Logger:
    """
    Set up logging for the Trustwise SDK.
    
    Args:
        logger_name: Name of the logger to create.
    
    Returns:
        Logger instance configured based on LOG_LEVEL environment variable.
        
    Environment Variables:
        LOG_LEVEL: Set to "debug" (case-insensitive) to enable debug logging.
                  When set, shows detailed API request/response information.
    """
    logger = logging.getLogger(logger_name)
    
    # Check for LOG_LEVEL environment variable
    if os.getenv("LOG_LEVEL", "").lower() == "debug":
        logger.setLevel(logging.DEBUG)
        # Add console handler for debug logging
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        # Prevent propagation to root logger if no handlers are configured
        logger.addHandler(logging.NullHandler())
    
    return logger


# Create the logger instance for the client
logger = setup_logging("trustwise.sdk")
