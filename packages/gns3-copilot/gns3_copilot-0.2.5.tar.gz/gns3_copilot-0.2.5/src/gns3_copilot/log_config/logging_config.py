"""
Unified logging configuration module.

Provides centralized logging configuration for GNS3 Copilot tools package,
eliminating duplicate logging setup code across modules.
"""

import logging
import os


def setup_logger(
    name: str,
    log_file: str | None = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> logging.Logger:
    """
    Set up unified logging configuration.

    Args:
        name (str): Logger name, typically the module name
        log_file (str, optional): Log file path, defaults to log/{name}.log
        console_level (int, optional): Console log level, defaults to INFO
        file_level (int, optional): File log level, defaults to DEBUG

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set logger level to DEBUG for maximum detail

    # Prevent duplicate handlers
    if not logger.handlers:
        # Create unified formatter
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # Configure file handler
        if log_file is None:
            log_file = f"log/{name}.log"

        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Prevent propagation to root logger to avoid duplicate logging
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get configured logger, use default configuration if not configured.

    Args:
        name (str): Logger name

    Returns:
        logging.Logger: Logger instance
    """
    logger = logging.getLogger(name)

    # If logger has no handlers, use default configuration
    if not logger.handlers:
        return setup_logger(name)

    return logger


def configure_package_logging(level: int = logging.INFO) -> None:
    """
    Configure root log level for the entire package.

    Args:
        level (int): Log level
    """
    # Set package root logger
    package_logger = logging.getLogger("tools")
    package_logger.setLevel(level)

    # If no handlers, add a simple console handler
    if not package_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        formatter = logging.Formatter("GNS3 Tools: %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        package_logger.addHandler(console_handler)


# Predefined logging configurations
LOGGER_CONFIGS = {
    "device_config": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "display_tools": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "gns3_topology": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "gns3_create_node": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "gns3_create_link": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "gns3_start_node": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "gns3_template": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "config_tools_nornir": {
        "console_level": logging.ERROR,
        "file_level": logging.DEBUG,
    },
    "display_tools_nornir": {
        "console_level": logging.ERROR,
        "file_level": logging.DEBUG,
    },
    "static_server": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "services_manager": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "vpcs_multi_commands": {
        "console_level": logging.ERROR,
        "file_level": logging.DEBUG,
    },
    "linux_tools_nornir": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "app": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "settings": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "chat": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "prompt_loader": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "whisper_stt": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
    "openai_tts": {"console_level": logging.ERROR, "file_level": logging.DEBUG},
}


def setup_tool_logger(tool_name: str, config_name: str | None = None) -> logging.Logger:
    """
    Set up logger for specific tool using predefined configuration.

    Args:
        tool_name (str): Tool name
        config_name (str, optional): Configuration name, defaults to tool_name

    Returns:
        logging.Logger: Configured logger instance
    """
    if config_name is None:
        config_name = tool_name

    config = LOGGER_CONFIGS.get(config_name, {})

    return setup_logger(
        name=tool_name,
        log_file=f"log/{tool_name}.log",
        console_level=config.get("console_level", logging.ERROR),
        file_level=config.get("file_level", logging.DEBUG),
    )
