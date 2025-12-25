from scurrypy import (
    Addon,
    UserModel,
    EmbedAuthor
)

class EmbedBuilder(Addon):
    """Common Embed helpers."""
    
    @staticmethod
    def user_author(user: UserModel):
        """Embed author builder.

        Args:
            user (UserModel): user author

        Returns:
            (EmbedAuthor): the EmbedAuthor object
        """
        if not user:
            raise ValueError("Missing user.")
        
        return EmbedAuthor(
            name=user.username,
            icon_url=f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar}.png"
        )
    
    @staticmethod
    def timestamp():
        """Embed timestamp builder. Adheres to ISO8601 format.

        Returns:
            (str): message timestamp
        """
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
