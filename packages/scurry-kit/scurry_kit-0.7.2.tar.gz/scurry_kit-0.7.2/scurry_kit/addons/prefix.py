import logging

logger = logging.getLogger('scurrypy')

from scurrypy import (
    Addon,
    Client,
    Intents,
    DiscordError,
    EventTypes,
    MessageCreateEvent,
)

import inspect

class PrefixAddon(Addon):
    """Addon that implements automatic registering and decorating prefix commands."""

    def __init__(self, client: Client, application_id: int, prefix: str):
        """
        Args:
            client (Client): the Client object
            prefix (str): message prefix for commands
        """
        if not Intents.has(client.intents, Intents.MESSAGE_CONTENT):
            raise ValueError("Missing Intent.MESSAGE_CONTENT for scanning messages.")
        
        self.bot = client

        self.application_id = application_id

        self._prefix = prefix

        self._commands = {}
        """Maps prefix command names to handler."""
        
        client.add_event_listener(EventTypes.MESSAGE_CREATE, self.dispatch)

    def listen(self, name: str):
        """Listen for a prefix command.

        Args:
            name (str): name of the command
                !!! warning "Important"
                    Prefix commands are CASE-INSENSITIVE.
        """
        def decorator(func):
            params_len = len(inspect.signature(func).parameters)

            if params_len != 2:
                raise TypeError(
                    f"Prefix handler '{func.__name__}' must accept exactly two parameters (bot, message)."
                )
            self._commands[name.lower()] = func
            logger.info(f"Prefix command '{self._prefix + name}' registered.")
        return decorator

    async def dispatch(self, event: MessageCreateEvent):
        """Dispatch event to user-defined handler.
            Ignore bot responding to self and messages without the desired prefix.

        Args:
            event (MessageCreateEvent): message create event object
        """
        if not event.content:
            return
        
        # ignore bot responding to itself
        if event.author.id == self.application_id:
            return
        
        has_prefix = event.content.lower().startswith(self._prefix.lower())

        # ignore messages without prefix
        if not has_prefix:
            return
        
        command, *args = event.content[len(self._prefix):].strip().lower().split()
        handler = self._commands.get(command)

        # warn if this command doesnt have a known handler
        if not handler:
            logger.warning(f"Prefix Event '{command}' not found.")
            return

        # now prefix info can be confidently set
        try:
            res = self.bot.message(event.channel_id, event.id, context=event)
            await handler(self.bot, res)
            
            logger.info(f"Prefix Event '{self._prefix + command}' acknowledged with args: {list(args) or 'No args'}")
        except DiscordError as e:
            logger.error(f"Error in prefix command '{self._prefix + command}': {e}")        
        except Exception as e:
            logger.error(f"Unhandled error in prefix command '{self._prefix + command}': {e}")
