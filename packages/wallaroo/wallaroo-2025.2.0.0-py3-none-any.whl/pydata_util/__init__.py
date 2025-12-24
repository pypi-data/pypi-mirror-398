import logging
import os

from rich.logging import RichHandler

log_level = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=getattr(logging, log_level, logging.INFO),
    handlers=[RichHandler(show_time=False)],
)
