import fastapi_babel

from ..utils import lazy, use_default_when_none

__all__ = ["lazy_text", "translate", "_"]

logger = None


class lazy_text(lazy[str]):
    """
    Lazily translates a message using FastAPI Babel.
    """

    def __init__(self, message: str, *args, **kwargs):
        """
        Initializes a lazy_text instance that lazily translates the given message.

        Args:
            message (str): the message to be translated.
            *args: positional arguments to format the message.
            **kwargs: keyword arguments to format the message.
        """
        super().__init__(
            lambda: translate(message).format(*args, **kwargs),
            cache=False,
            only_instance=True,
        )

    @classmethod
    def _(cls, message: str, *args, **kwargs):
        """
        Class method to create a lazy_text instance that can be automatically found by `pybabel extract`.

        Args:
            message (str): the message to be translated.
            *args: positional arguments to format the message.
            **kwargs: keyword arguments to format the message.

        Returns:
            lazy_text: an instance of lazy_text that will lazily translate the message.
        """
        return cls(message, *args, **kwargs)

    def __repr__(self):
        """
        When reading it as a string, it should return the formatted message.

        Returns:
            str: the formatted message.
        """
        return self.__call__()


def translate(
    message: str, *args, ensure_context=False, use_settings_translations=True, **kwargs
):
    """
    Translates a message using FastAPI Babel.

    Args:
        message (str): the message to be translated.
        *args: positional arguments to format the message.
        ensure_context (bool): Whether to ensure the context is already set to know which language to use. If false, it will return the message as is if the translation is not found. Defaults to False.
        use_translations (bool): Whether to use the translations defined in `Setting.TRANSLATIONS` as a fallback if the translation is not found. Defaults to True.
        **kwargs: keyword arguments to format the message.

    Returns:
        str: the translated message.
    """
    try:
        translated_message = fastapi_babel._(message)
        if translated_message == message and use_settings_translations:
            translated_message = use_default_when_none(
                _use_settings_translations(message), message
            )
        return translated_message.format(*args, **kwargs)
    except LookupError as e:
        if not ensure_context:
            from ..globals import g

            if g.current_app and g.current_app.started:
                global logger
                if not logger:
                    from ..const import logger as base_logger

                    logger = base_logger.getChild("lang")

                logger.warning(
                    f"Translation not found for '{message}'. Returning the original message."
                )
            return message.format(*args, **kwargs)
        raise e


def _use_settings_translations(message: str):
    """
    Use translations defined in `Setting.TRANSLATIONS` as a fallback if the translation is not found.

    Args:
        message (str): The original message to translate.

    Returns:
        str | None: The translated message, or None if no translation is found.
    """
    from ..globals import g
    from ..setting import Setting

    if Setting.TRANSLATIONS and g.request:
        try:
            translated_message = Setting.TRANSLATIONS.get(
                g.request.state.babel.locale, {}
            ).get(message)
            if translated_message:
                return translated_message
        except Exception:
            pass


_ = translate  # Alias for convenience
