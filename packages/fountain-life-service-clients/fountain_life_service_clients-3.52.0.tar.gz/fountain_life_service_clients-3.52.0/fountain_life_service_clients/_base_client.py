from typing import NotRequired, Unpack, cast

from lifeomic_chatbot_tools.aws.alpha import (
    Alpha,
)
from lifeomic_chatbot_tools.aws.alpha import (
    AlphaConfig as BaseAlphaConfig,
)
from lifeomic_chatbot_tools.aws.alpha import (
    AlphaResponse as BaseAlphaResponse,
)


class AlphaConfig(BaseAlphaConfig):
    # Pull target out as another keyword arg instead of a positional
    # arg, to make it easier to work with.
    target: NotRequired[str]


class BaseClient:
    def __init__(self, **cfg: Unpack[AlphaConfig]):
        self.client = Alpha(**cfg)


# A typed version of AlphaResponse that allows us to access the
# response body as a typed object.
class AlphaResponse[T](BaseAlphaResponse):
    @property
    def body(self):
        return cast(T, super().body)
