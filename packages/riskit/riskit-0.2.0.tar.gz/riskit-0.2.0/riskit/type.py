try:
    from beartype import beartype  # pyright: ignore[reportMissingImports]

    typechecker = beartype
except ImportError:
    typechecker = None

from typing import Final
from jaxtyping import jaxtyped as jaxtyping_jaxtyped

jaxtyped: Final = jaxtyping_jaxtyped(typechecker=typechecker)
"""Wrapper around `jaxtyping.jaxtyped` that conditionally applies type checking."""
