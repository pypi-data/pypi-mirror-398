# scurry_kit/addons

from .commands import CommandsAddon
from .components import ComponentsAddon
from .events import EventsAddon
from .hooks import HooksAddon
from .prefix import PrefixAddon
from .logging import setup_default_logger

__all__ = [
    "CommandsAddon",
    "ComponentsAddon",
    "EventsAddon",
    "HooksAddon",
    "PrefixAddon",
    "setup_default_logger"
]
