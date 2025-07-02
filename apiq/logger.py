import logging
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel


def setup_logger(name: str, debug: bool = False) -> logging.Logger:
    """
    Creates and configures a logger for the given module or class.

    :param name: Logger name.
    :param debug: If True, sets level to DEBUG; otherwise INFO.
    :return: Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    return logger


def log_request(
        logger: logging.Logger,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Any] = None,
        body: Optional[Any] = None,
) -> None:
    """
    Logs outgoing API request details.
    """
    logger.debug("[APIQ DEBUG] Request:")
    logger.debug(f"  Method: {method}")
    logger.debug(f"  URL: {url}")

    if headers:
        logger.debug(f"  Headers: {headers}")
    if params:
        logger.debug(f"  Params: {params}")
    if body:
        logger.debug(f"  Body: {body}")


def log_response(logger: logging.Logger, status: int, content: Any) -> None:
    """
    Logs API response details.
    """
    logger.debug("[APIQ DEBUG] Response:")
    logger.debug(f"  Status: {status}")
    logger.debug(f"  Content: {content}")


def log_endpoint_call(
        logger: logging.Logger,
        method: str,
        path: str,
        model: Optional[Type[BaseModel]] = None,
        headers: Optional[Dict[str, str]] = None,
        args: Optional[Any] = None,
        kwargs: Optional[Any] = None,
) -> None:
    """
    Logs endpoint decorator call information.
    """
    logger.debug("[APIQ DEBUG] Calling endpoint")
    logger.debug(f"  Method: {method}")
    logger.debug(f"  Path: {path}")

    if headers:
        logger.debug(f"  Headers override: {headers}")
    if args:
        logger.debug(f"  Args: {args}")
    if kwargs:
        logger.debug(f"  Kwargs: {kwargs}")

    if model:
        logger.debug(f"  Parsing response as model: {model.__name__}")
    else:
        logger.debug("  Returning raw response (no model)")
