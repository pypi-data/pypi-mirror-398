import logging

logger = logging.getLogger('scurrypy')

from scurrypy import (
    Addon,
    Client,
    DiscordError,
    Event
)

import inspect

class EventsAddon(Addon):
    """Addon that implements automatic registering and decorating events."""

    def __init__(self, client: Client):
        """
        Args:
            client (Client): the Client object
        """
        self.bot = client

        self._events = {}
        """Maps EVENT_NAME to handlers."""

        client.add_startup_hook(self.on_startup)

    def on_startup(self):
        """Adds registered events to client's event listener."""

        # lead all registered events to this dispatch
        for dispatch_type in self._events.keys():
            self.bot.add_event_listener(dispatch_type, self.dispatch)
        
    def listen(self, event_name: str):
        """Listen for an event in which to listen.

        Args:
            event_name (str): event name
        """
        def decorator(func):
            params_len = len(inspect.signature(func).parameters)
            if params_len != 2:
                raise TypeError(f"Event handler '{func.__name__}' must accept exactly two parameters (bot, event).")
            
            self._events.setdefault(event_name, []).append(func)
        return decorator

    async def dispatch(self, event: Event):
        """Addon's entry point.

        Args:
            event (Event): event data object
        """
        handlers = self._events.get(event.name)

        if not handlers:
            return
        try:
            for handler in handlers:
                await handler(self.bot, event)
        except DiscordError as e:
            logger.error(f"Error in event '{handler}': {e}")
        except Exception as e:
            logger.error(f"Unhandled error in event '{handler.__name__}': {e}")
