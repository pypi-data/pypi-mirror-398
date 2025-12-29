from typing import Final

from riskit.compute.distribution.basic import NumPyGaussian, NumPyUniform
from riskit.compute.distribution.accelerated import JaxGaussian, JaxUniform


class distribution:
    class numpy:
        gaussian: Final = NumPyGaussian.create
        uniform: Final = NumPyUniform.create

    class jax:
        gaussian: Final = JaxGaussian.create
        uniform: Final = JaxUniform.create
