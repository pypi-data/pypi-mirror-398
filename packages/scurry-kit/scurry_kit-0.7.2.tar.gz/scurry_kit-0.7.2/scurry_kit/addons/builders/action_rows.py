from scurrypy import (
    Addon,
    ActionRowPart, ActionRowChild,
    EmojiModel,
    Button, ButtonStyles
)

class ActionRowBuilder(Addon):
    """Common button helpers."""
    
    @staticmethod
    def _basic_button(
        style: int, 
        custom_id: str, 
        label: str = None, 
        emoji: str | EmojiModel = None, 
        disabled: bool = False
    ):
        if emoji:
            if isinstance(emoji, str):
                emoji = EmojiModel(name=emoji)
            elif not isinstance(emoji, EmojiModel):
                raise TypeError(f"EasyBot.primary expects type str or EmojiModel, got {type(emoji).__name__}")
        
        return Button(
            style=style,
            custom_id=custom_id,
            label=label,
            emoji=emoji ,
            disabled=disabled
        )
    
    @staticmethod
    def primary(
        custom_id: str, 
        label: str = None, 
        emoji: str | EmojiModel = None, 
        disabled: bool = False
    ):
        """Builds a primary button

        Args:
            custom_id (str): unique button identifier
            label (str, optional): user-facing label
            emoji (str | EmojiModel, optional): emoji icon as str or EmojiModel if custom
            disabled (bool, optional): Whether the button should be disabled. Defaults to False.

        Returns:
            (Button): the button object
        """
        return ActionRowBuilder._basic_button(ButtonStyles.PRIMARY, custom_id, label, emoji, disabled)
    
    @staticmethod
    def secondary(
        custom_id: str, 
        label: str = None, 
        emoji: str | EmojiModel = None, 
        disabled: bool = False
    ):
        """Builds a secondary button

        Args:
            custom_id (str): unique button identifier
            label (str, optional): user-facing label
            emoji (str | EmojiModel, optional): emoji icon as str or EmojiModel if custom
            disabled (bool, optional): Whether the button should be disabled. Defaults to False.

        Returns:
            (Button): the button object
        """
        return ActionRowBuilder._basic_button(ButtonStyles.SECONDARY, custom_id, label, emoji, disabled)
    
    @staticmethod
    def success(
        custom_id: str, 
        label: str = None, 
        emoji: str | EmojiModel = None, 
        disabled: bool = False
    ):
        """Builds a success button

        Args:
            custom_id (str): unique button identifier
            label (str, optional): user-facing label
            emoji (str | EmojiModel, optional): emoji icon as str or EmojiModel if custom
            disabled (bool, optional): Whether the button should be disabled. Defaults to False.

        Returns:
            (Button): the button object
        """
        return ActionRowBuilder._basic_button(ButtonStyles.SUCCESS, custom_id, label, emoji, disabled)
    
    @staticmethod
    def danger(
        custom_id: str, 
        label: str = None, 
        emoji: str | EmojiModel = None, 
        disabled: bool = False
    ):
        """Builds a danger button

        Args:
            custom_id (str): unique button identifier
            label (str, optional): user-facing label
            emoji (str | EmojiModel, optional): emoji icon as str or EmojiModel if custom
            disabled (bool, optional): Whether the button should be disabled. Defaults to False.

        Returns:
            (Button): the button object
        """
        return ActionRowBuilder._basic_button(ButtonStyles.DANGER, custom_id, label, emoji, disabled)
    
    @staticmethod
    def link(
        url: str, 
        label: str = None, 
        emoji: str | EmojiModel = None, 
        disabled: bool = False
    ):
        """Builds a link button

        Args:
            url (str): button URL to open
            label (str, optional): user-facing label
            emoji (str | EmojiModel, optional): emoji icon as str or EmojiModel if custom
            disabled (bool, optional): Whether the button should be disabled. Defaults to False.

        Returns:
            (Button): the button object
        """
        btn = ActionRowBuilder._basic_button(ButtonStyles.LINK, label, emoji, disabled)
        btn.url = url
        return btn

    @staticmethod
    def row(components: list[ActionRowChild]):
        """Builds an action row.

        Args:
            components (list[ActionRowChild]): components to be placed in the row

        Returns:
            (ActionRowPart): the action row object
        """
        if not isinstance(components, list):
            components = [components]
        
        return ActionRowPart(components)
