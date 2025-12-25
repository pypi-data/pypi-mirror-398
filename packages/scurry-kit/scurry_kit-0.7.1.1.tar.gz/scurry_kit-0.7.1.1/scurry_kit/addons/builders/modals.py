from scurrypy import (
    Addon,
    TextInput, TextInputStyles
)

class LabelBuilder(Addon):
    """Common Label Helpers."""
    
    @staticmethod
    def _text(
        custom_id: str,
        style: int,
        min_length: int,
        max_length: int,
        required: bool,
        value: str,
        placeholder: str
    ):
        return TextInput(
            custom_id=custom_id,
            style=style,
            min_length=min_length,
            max_length=max_length,
            required=required,
            value=value,
            placeholder=placeholder
        )
    
    @staticmethod
    def short_text(
        custom_id: str,
        min_length: int = None,
        max_length: int = None,
        required: bool = True,
        value: str = None,
        placeholder: str = None
    ):
        """Builds a single-line text input.

        Args:
            custom_id (str): ID for the input
            min_length (int): minimum input length
            max_length (int): maximum input length
            required (bool): Whether this input is required. Defaults to True.
            value (str): Pre-filled content
            placeholder (str): placeholder if text is empty

        Returns:
            (TextInput): the text input object
        """
        return LabelBuilder._text(custom_id, TextInputStyles.SHORT, min_length, max_length, required, value, placeholder)
    
    @staticmethod
    def long_text(
        custom_id: str,
        min_length: int,
        max_length: int,
        required: bool,
        placeholder: str
    ):
        """Builds a multi-line text input.

        Args:
            custom_id (str): ID for the input
            min_length (int): minimum input length
            max_length (int): maximum input length
            required (bool): Whether this input is required. Defaults to True.
            value (str): Pre-filled content
            placeholder (str): placeholder if text is empty

        Returns:
            (TextInput): the text input object
        """
        return LabelBuilder._text(custom_id, TextInputStyles.PARAGRAPH, min_length, max_length, required, placeholder)
