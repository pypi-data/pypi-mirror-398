import asyncio
import json
import logging
import os
from functools import wraps
from itertools import islice
from typing import Callable
from typing import Tuple
from typing import Type

import aiofiles

logger = logging.getLogger(__file__)


def divide_to_chunks(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


async def store_annotation(path: str, postfix: str, annotation: dict):
    os.makedirs(path, exist_ok=True)
    try:
        async with aiofiles.open(
            f"{path}/{annotation['metadata']['name']}{postfix}", "w"
        ) as file:
            await file.write(json.dumps(annotation, ensure_ascii=False))
    except KeyError:
        logger.error(
            f"Failed to store annotation; annotation: {annotation}; path: {path}"
        )
        raise


def async_retry_on_generator(
    exceptions: Tuple[Type[Exception]],
    retries: int = 3,
    delay: float = 0.3,
    backoff: float = 0.3,
):
    """
    An async retry decorator that retries a function only on specific exceptions.

    Parameters:
        exceptions (tuple): Tuple of exception classes to retry on.
        retries (int): Number of retry attempts.
        delay (float): Initial delay between retries in seconds.
        backoff (float): Factor to increase the delay after each failure.
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            raised_exception = None

            while attempt < retries:
                try:
                    async for v in func(*args, **kwargs):
                        yield v
                    return
                except exceptions as e:
                    raised_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{retries} failed with error: {e}. Retrying in {current_delay} seconds..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay += backoff  # Exponential backoff
                finally:
                    attempt += 1
            if raised_exception:
                logger.error(
                    f"All {retries} attempts failed due to {raised_exception}."
                )
                raise raised_exception

        return wrapper

    return decorator
