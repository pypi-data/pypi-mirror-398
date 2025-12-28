import functools
import logging

from .exceptions import AppException, CriticalException

logger = logging.getLogger(__name__)


def handle_exceptions(func):
    """Decorator to log exceptions and trace function calls with details."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            logger.warning("Keyboard interrupt is detected.")
            raise
        except AppException:
            raise
        except CriticalException as e:
            logger.critical(AppException(e, func.__name__))
            exit()
        except Exception as e:
            raise AppException(e, func.__name__) from e

    return wrapper


def nullable(func):
    """Decorator to return None on exception and log error."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.warning(AppException(e, func.__name__))

    return wrapper
