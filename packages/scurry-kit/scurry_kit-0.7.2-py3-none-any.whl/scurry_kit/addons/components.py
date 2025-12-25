import logging

logger = logging.getLogger('scurrypy')

def _check_func_params(func: callable):
    import inspect
    
    params_len = len(inspect.signature(func).parameters)

    if params_len != 2:
        raise TypeError(
            f"Component handler '{func.__name__}' must accept exactly two parameters (bot, interaction)."
        )

from scurrypy import (
    Addon,
    Client,
    DiscordError,
    EventTypes,
    InteractionEvent, InteractionTypes
)

class ComponentsAddon(Addon):
    """Addon that implements automatic registering and decorating component interactions."""

    def __init__(self, client: Client):
        """
        Args:
            client (Client): the bot client object
        """
        self.bot = client

        self.component_handlers = {}
        """Mapping of component custom IDs to handler."""

        client.add_startup_hook(self.on_startup) # wait until start to register commands

    def on_startup(self):
        """Sets up the addon with the client."""

        self.bot.add_event_listener(EventTypes.INTERACTION_CREATE, self.dispatch)

    def component(self, custom_id: str):
        def decorator(func):
            _check_func_params(func)
            self.component_handlers[custom_id] = func
        return decorator
    
    # helpers purly for ergonomics
    def button(self, custom_id: str):
        """Decorator to route button interactions.

        Args:
            custom_id (str): custom ID of button
                !!! warning "Important"
                    Must match the `custom_id` set where the component was created.
        """
        return self.component(custom_id)

    def select(self, custom_id: str):
        """Decorator to route select menu interactions.

        Args:
            custom_id (str): custom ID of select menu
                !!! warning "Important"
                    Must match the `custom_id` set where the component was created.
        """
        return self.component(custom_id)

    def modal(self, custom_id: str):
        """Decorator to route modal interactions.

        Args:
            custom_id (str): custom ID of modal
                !!! warning "Important"
                    Must match the `custom_id` set where the component was created.
        """
        return self.component(custom_id)

    def _get_handler(self, name: str):
        """Helper function for fetching a handler by `fnmatch`."""

        import fnmatch
        for k, v in self.component_handlers.items():
            if fnmatch.fnmatch(name, k):
                return v
        return False

    async def dispatch(self, event: InteractionEvent):
        """Dispatch a response to an `INTERACTION_CREATE` event

        Args:
            event (InteractionEvent): interaction event object
        """
        # only respond to component interactions
        if event.type not in [InteractionTypes.MESSAGE_COMPONENT, InteractionTypes.MODAL_SUBMIT]:
            return

        name = event.data.custom_id
        handler = self._get_handler(name)

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
