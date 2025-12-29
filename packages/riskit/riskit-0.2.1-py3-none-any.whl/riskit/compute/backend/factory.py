from typing import Final

from riskit.compute.backend.basic import NumPyBackend
from riskit.compute.backend.accelerated import JaxBackend


class backend:
    numpy: Final = NumPyBackend
    jax: Final = JaxBackend
