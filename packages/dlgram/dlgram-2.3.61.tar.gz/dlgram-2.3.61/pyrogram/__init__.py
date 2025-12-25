
__fork_name__ = "Pygram"
__version__ = "2.3.61"
__license__ = "GNU Lesser General Public License v3.0 (LGPL-3.0)"
__copyright__ = "Copyright (C) 2022-present Mayuri-Chan <https://github.com/Mayuri-Chan>"

from concurrent.futures.thread import ThreadPoolExecutor


class StopTransmission(Exception):
    pass


class StopPropagation(StopAsyncIteration):
    pass


class ContinuePropagation(StopAsyncIteration):
    pass


from . import raw, types, filters, handlers, emoji, enums  # pylint: disable=wrong-import-position
from .client import Client  # pylint: disable=wrong-import-position
from .sync import idle, compose  # pylint: disable=wrong-import-position

crypto_executor = ThreadPoolExecutor(1, thread_name_prefix="CryptoWorker")

__all__ = [
    "Client",
    "idle",
    "compose",
    "crypto_executor",
    "StopTransmission",
    "StopPropagation",
    "ContinuePropagation",
    "raw",
    "types",
    "filters",
    "handlers",
    "emoji",
    "enums",
]
