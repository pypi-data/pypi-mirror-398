import logging
from rich.logging import RichHandler

def setup_default_logger(level=logging.INFO):
    root = logging.getLogger()
    if not root.hasHandlers():
        handler = RichHandler(show_path=False, rich_tracebacks=True)
        logging.basicConfig(level=level, handlers=[handler], format="%(message)s")

    # silence internals
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)

    return root
