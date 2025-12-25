from subprocess import run

import fastapi_babel

__all__ = ["FastAPIRTKBabelCLI"]


class FastAPIRTKBabelCLI(fastapi_babel.BabelCli):
    """
    Subclass of `fastapi_babel.BabelCli`.

    - Modified `extract` method to handle custom keywords.
    """

    def extract(self, watch_dir, keywords: str | None = None):
        """
        Modified version of the default `extract` method to handle custom keywords too.

        extract all messages that annotated using gettext/_
        in the specified directory.

        for first time will create messages.pot file into the root
        directory.

        Args:
            watch_dir (str): directory to extract messages.
            keywords (str | None): custom keywords to extract separated by space.
        """
        args = [
            self.__module_name__,
            "extract",
            "-F",
            self.babel.config.BABEL_CONFIG_FILE,
            "-o",
            self.babel.config.BABEL_MESSAGE_POT_FILE,
        ]
        if keywords:
            args.extend(["-k", keywords])
        args.append(watch_dir)
        run(args)
