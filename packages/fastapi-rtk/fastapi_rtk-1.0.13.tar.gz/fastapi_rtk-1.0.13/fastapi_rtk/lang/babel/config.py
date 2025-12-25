import os

import fastapi_babel

__all__ = ["FastAPIRTKBabelConfigs"]


class FastAPIRTKBabelConfigs(fastapi_babel.BabelConfigs):
    """
    Subclass of `fastapi_babel.BabelConfigs`.

    - Modified `ROOT_DIR` to not use its parent directory.
    """

    def __post_init__(self):
        self.ROOT_DIR = os.path.join(self.ROOT_DIR, "dummy")
        return super().__post_init__()
