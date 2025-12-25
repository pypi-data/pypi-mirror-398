import sys
import logging
import traceback
from typing import TypeVar, Callable, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("scout_cli")

# Type variable for functions
T = TypeVar("T")


class ScoutCLIError(Exception):
    """Base exception class for Scout CLI errors."""

    pass


class ConfigurationError(ScoutCLIError):
    """Exception raised for configuration errors."""

    pass


class APIError(ScoutCLIError):
    """Exception raised for API-related errors."""

    pass


class ValidationError(ScoutCLIError):
    """Exception raised for validation errors."""

    pass


class FileSystemError(ScoutCLIError):
    """Exception raised for filesystem-related errors."""

    pass


class ModuleError(ScoutCLIError):
    """Exception raised for module-related errors."""

    pass


def handle_exception(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle exceptions in CLI functions.
    Catches exceptions, logs them, and exits with an error code.

    Args:
        func: The function to wrap

    Returns:
        The wrapped function
    """

    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            logger.info("\nOperation cancelled by user")
            sys.exit(130)  # Standard exit code for SIGINT
        except ScoutCLIError as e:
            logger.error(f"{type(e).__name__}: {str(e)}")
            if logger.level <= logging.DEBUG:
                logger.debug(
                    f"Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}"
                )
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {str(e)}")
            if logger.level <= logging.DEBUG:
                logger.exception("Detailed traceback:")
            sys.exit(1)

    return wrapper


def exit_with_error(message: str, exit_code: int = 1) -> None:
    """
    Log an error message and exit with the specified code.
    Deprecated: Use raise ValidationError(message) instead.

    Args:
        message: The error message to log
        exit_code: The exit code to use (default 1)
    """
    raise ValidationError(message)


def set_verbosity(verbose: bool = False) -> None:
    """
    Set the verbosity level of the logger.

    Args:
        verbose: If True, set log level to DEBUG, otherwise INFO
    """
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
