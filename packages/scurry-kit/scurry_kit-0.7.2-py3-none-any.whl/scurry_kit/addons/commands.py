import logging

logger = logging.getLogger('scurrypy')

def _check_func_params(func: callable):
    import inspect
    
    params_len = len(inspect.signature(func).parameters)

    if params_len != 2:
        raise TypeError(
            f"Command handler '{func.__name__}' must accept exactly two parameters (bot, interaction)."
        )
    
from scurrypy import (
    Addon,
    Client,
    DiscordError,
    SlashCommand, UserCommand, MessageCommand, CommandOption,
    EventTypes, 
    InteractionEvent, InteractionTypes, InteractionDataTypes
)

class CommandsAddon(Addon):
    """Addon that implements automatic registering and decorating command interactions."""

    def __init__(self, client: Client, application_id: int, sync_commands: bool = True):
        """
        Args:
            client (Client): the bot client object
            sync_commands (bool): whether to sync commands. Defaults to `True`.
        """
        self.bot = client

        self.application_id = application_id

        self.sync_commands = sync_commands

        self._global_commands = []
        """List of all Global commands."""

        self._guild_commands = {}
        """Guild commands mapped by guild ID."""

        self.slash_handlers = {}
        """Mapping of command names to handler."""

        self.message_handlers = {}
        """Mapping of message command names to handler."""

        self.user_handlers = {}
        """Mapping of user command names to handler."""

        self.autocomplete_handlers = {}
        """Mapping of autocomplete keys to handler."""

        client.add_startup_hook(self.on_startup) # wait until start to register commands

    def on_startup(self):
        """Sets up the addon with the client."""

        self.bot.add_event_listener(EventTypes.INTERACTION_CREATE, self.dispatch)
        if self.sync_commands:
            self.bot.add_startup_hook(self._register_commands)
    
    def slash_command(self, 
        name: str, 
        description: str, 
        *, 
        options: list[CommandOption] = None, 
        guild_ids: list[int] = None
    ):
        """Register and route a slash command.

        Args:
            name (str): command name
            description (str): command description
            options (list[CommandOption], optional): list of command options
            guild_ids (list[int], optional): list of guild IDs for guild commands or omit for global
        """
        self._queue_command(SlashCommand(name, description, options), guild_ids)

        def decorator(func):
            _check_func_params(func)
            self.slash_handlers[name] = func
            logger.info(f"Slash command '/{name}' registered.")
        return decorator
    
    def user_command(self, name: str, *, guild_ids: list[int] = None):
        """Register and route a user command.

        Args:
            name (str): command name
            guild_ids (list[int], optional): list of guild IDs for guild commands or omit for global
        """
        self._queue_command(UserCommand(name), guild_ids)

        def decorator(func):
            _check_func_params(func)
            self.user_handlers[name] = func
            logger.info(f"User command '{name}' registered.")
        return decorator

    def message_command(self, name: str, *, guild_ids: list[int] = None):
        """Register and route a message command.

        Args:
            name (str): command name
            guild_ids (list[int], optional): list of guild IDs for guild commands or omit for global
        """
        self._queue_command(MessageCommand(name), guild_ids)

        def decorator(func):
            _check_func_params(func)
            self.message_handlers[name] = func
            logger.info(f"Message command '{name}' registered.")
        return decorator
    
    def autocomplete(self, command_name: str, option_name: str):
        """Register and route an autocomplete interaction.

        Args:
            command_name (str): name of command to autocomplete
            option_name (str): name of option to autocomplete
        """
        key = f"{command_name}:{option_name}"

        def decorator(func):
            _check_func_params(func)
            self.autocomplete_handlers[key] = func
            logger.info(f"Autocomplete '{key}' registered.")
        return decorator
    
    async def _register_commands(self):
        """Register both guild and global commands to the client."""

        await self.bot.register_global_commands(self.application_id, self._global_commands)

        for guild_id, cmds in self._guild_commands.items():
            await self.bot.register_guild_commands(self.application_id, cmds, guild_id)
    
    def _queue_command(self, 
        command: SlashCommand | MessageCommand | UserCommand, 
        guild_ids: list[int] = None
    ):
        """Queue a decorated command to be registered on startup.

        Args:
            command (SlashCommand | MessageCommand | UserCommand): the command object
            guild_ids (list[int], optional): list of guild IDs for guild commands or omit for global
        """
        if guild_ids:
            gids = [guild_ids] if not isinstance(guild_ids, list) else guild_ids

            for gid in gids:
                self._guild_commands.setdefault(gid, []).append(command)
        
        else:
            self._global_commands.append(command)

    def clear_commands(self, guild_ids: list[int] = None):
        """Clear a guild's or global commands (slash, message, and user).

        Args:
            guild_ids (list[int], optional): list of guild IDs for guild commands or omit for global
        """
        if guild_ids:
            gids = [guild_ids] if isinstance(guild_ids, int) else guild_ids
            for gid in gids:
                removed = self._guild_commands.pop(gid, None)
                if removed is None:
                    logger.warning(f"Guild ID {gid} not found; skipping...")
                else:
                    logger.info(f"Guild commands for ID {gid} have been cleared.")
        else:
            self._global_commands.clear()
            logger.info("Global commands have been cleared.")

    async def dispatch(self, event: InteractionEvent):
        """Dispatch a response to an `INTERACTION_CREATE` event

        Args:
            event (InteractionEvent): interaction event object
        """
        # only respond to command interactions
        if event.type not in [InteractionTypes.APPLICATION_COMMAND, InteractionTypes.APPLICATION_COMMAND_AUTOCOMPLETE]:
            return
        
        handler = None
        name = None

        if event.type == InteractionTypes.APPLICATION_COMMAND:
            name = event.data.name
            match event.data.type:
                case InteractionDataTypes.SLASH_COMMAND:
                    handler = self.slash_handlers.get(name)
                case InteractionDataTypes.USER_COMMAND:
                    handler = self.user_handlers.get(name)
                case InteractionDataTypes.MESSAGE_COMMAND:
                    handler = self.message_handlers.get(name)

        elif event.type == InteractionTypes.APPLICATION_COMMAND_AUTOCOMPLETE:
            # Extract option being autocompleted

            focused = next((opt for opt in event.data.options if opt.focused), None)

            if not focused:
                logger.error("No focused option found for autocomplete!")
                return

            name = f"{event.data.name}:{focused.name}"
            handler = self.autocomplete_handlers.get(name)

        if not handler:
            logger.warning(f"No handler registered for interaction '{name}'")
            return

        try:
            res = self.bot.interaction(event.id, event.token, context=event)
            await handler(self.bot, res)
            logger.info(f"Interaction '{name}' Acknowledged.")
        except DiscordError as e:
            logger.error(f"Error in interaction '{name}': {e}")
        except Exception as e:
            logger.error(f"Unhandled error in interaction '{name}': {e}")
