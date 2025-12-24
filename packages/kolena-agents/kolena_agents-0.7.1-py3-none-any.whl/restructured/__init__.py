import warnings

from kolena_agents._utils import webhook
from kolena_agents._utils.client import Client

warnings.warn(
    "'restructured' package is deprecated, use 'kolena_agents' instead",
    DeprecationWarning,
    stacklevel=2,
)


class Restructured(Client):
    """Legacy alias for the Client class. Use Client instead."""

    ...


__all__ = ["Restructured", "webhook"]
