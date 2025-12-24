from ._internal import create_cate
# fmt: off
from .cates import (
    Semigroup, register_semigroup, sconcat,  # Semigroup
    Monoid, register_monoid, semigroup2monoid, mempty, mappend,  # Monoid
    Functor, register_functor, fmap,  # Functor
    Monad, register_monad, bind, join,  # Monad
)

__all__ = [
    "create_cate",
    "Semigroup", "register_semigroup", "sconcat",  # Semigroup
    "Monoid", "register_monoid", "semigroup2monoid", "mempty", "mappend",   # Monoid
    "Functor", "register_functor", "fmap",  # Functor
    "Monad", "register_monad", "bind", "join",  # Monad
]
# fmt: on
