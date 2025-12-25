"""Base Inoopa configuration for python Logging using Logfire."""

import os
from typing import Literal

import logfire
from dotenv import load_dotenv

from inoopa_utils.utils.env_variables_helper import get_env_name

load_dotenv()


LoggingLevel = Literal["CRITICAL", "FATAL", "ERROR", "WARNING", "INFO", "DEBUG"]


def create_logger(
    logger_name: str, logging_level: LoggingLevel | None = None, logs_dir_path: str = "./logs", pretty: bool = False
) -> logfire.Logfire:
    """
    Configure how logging should be done using Logfire.

    :param logger_name: The logger name to return.
    :param logging_level: The level of logging to filter. If none, will deduce from "ENV" env variable:
        'dev' will set logging_level to "DEBUG"
        'staging' will set logging_level to "INFO"
        'prod' will set logging_level to "INFO"
    :param logs_dir_path: The path to the logs directory.
    :param pretty: If True, will use rich to pretty print the logs. Only for development & CLI purpose.
    """
    env = os.getenv("ENV", "LOCAL")
    if logging_level is None:
        logging_level = "DEBUG" if get_env_name() == "dev" else "INFO"

    # Convert logging level to logfire level
    logfire_level = logging_level.lower()

    # Configure logfire with basic settings
    console_options = logfire.ConsoleOptions(
        min_log_level=logfire_level,  # type: ignore
        colors="auto",
        include_timestamps=True,
        verbose=False,
        show_project_link=False,
        include_tags=True,
        span_style="indented",
    )

    logfire.configure(
        service_name=logger_name,
        console=console_options,
        send_to_logfire="if-token-present",  # Only send to Logfire platform if token is available
        min_level=logfire_level,  # type: ignore
        environment=env,
    )

    # Create a logger instance with the service name as a tag
    logger = logfire.with_settings(tags=[logger_name, env])

    return logger


if __name__ == "__main__":
    logger = create_logger("test_logger", logging_level="DEBUG", pretty=True)
    logger.debug("Debug message")
    logger.info("Info message with {data}", data={"hello": "world"})
    logger.warning("Warning message")
    logger.error("Error message")
