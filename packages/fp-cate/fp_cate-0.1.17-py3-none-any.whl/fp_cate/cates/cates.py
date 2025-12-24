import operator

from fp_cate.utils import assert_and, flip

from ._internal import create_cate


# fmt: off
__all__ = [
    "Semigroup", "register_semigroup", "sconcat",  # Semigroup
    "Monoid", "register_monoid", "semigroup2monoid", "mempty", "mappend",   # Monoid
    "Functor", "register_functor", "fmap",  # Functor
    "Monad", "register_monad", "bind", "join",  # Monad
]
# fmt: on

Semigroup, register_semigroup, sconcat = create_cate("Semigroup", "sconcat")
"""
```
register_semigroup(type, *, sconcat: Callable) -> None
```

Semigroup operation:
```
sconcat(a: T, b: T) -> T
```
"""

register_semigroup(int, sconcat=operator.add)
register_semigroup(float, sconcat=operator.add)
register_semigroup(str, sconcat=operator.add)
register_semigroup(list, sconcat=operator.add)
register_semigroup(tuple, sconcat=operator.add)
register_semigroup(dict, sconcat=lambda a, b: {**a, **b})
register_semigroup(set, sconcat=operator.or_)


Monoid, register_monoid, mempty, mappend = create_cate("Monoid", "mempty", "mappend")
"""
```
register_monoid(type, *, mempty: Callable, mappend: Callable) -> None
```

Monoid operations:
```
mempty(value: T) -> T
mappend(a: T, b: T) -> T
```
"""
semigroup2monoid = lambda t, *, mempty: assert_and(  # noqa: E731
    issubclass(t, Semigroup),
    register_monoid(t, mempty=mempty, mappend=sconcat),
    msg="Type must be a Semigroup",
)

semigroup2monoid(int, mempty=lambda _: 0)
semigroup2monoid(float, mempty=lambda _: 0.0)
semigroup2monoid(str, mempty=lambda _: "")
semigroup2monoid(list, mempty=lambda _: [])
semigroup2monoid(tuple, mempty=lambda _: ())
semigroup2monoid(dict, mempty=lambda _: {})
semigroup2monoid(set, mempty=lambda _: set())

Functor, _register_functor, _fmap = create_cate("Functor", "fmap")
fmap = flip(_fmap)  # fliping arguments since dispatching is on the first argument
register_functor = lambda t, *, fmap: _register_functor(  # noqa: E731
    t, fmap=flip(fmap)
)
"""
```
register_functor(type, *, fmap: Callable) -> None
```

Functor operation:
```
fmap(func: Callable[[A], B], fa: F[A]) -> F[B]
```
"""

register_functor(list, fmap=lambda f, xs: [f(x) for x in xs])
register_functor(tuple, fmap=lambda f, xs: tuple(f(x) for x in xs))
register_functor(dict, fmap=lambda f, d: {k: f(v) for k, v in d.items()})
register_functor(set, fmap=lambda f, s: {f(x) for x in s})


Monad, register_monad, bind, join = create_cate("Monad", "bind", "join")
"""
Monad operations:
```
bind(ma: M[A], f: Callable[[A], M[B]]) -> M[B]
join(mma: M[M[A]]) -> M[A]
```
"""

register_monad(
    list,
    bind=lambda xs, f: [y for x in xs for y in f(x)],
    join=lambda xss: [y for xs in xss for y in xs],
)
register_monad(
    tuple,
    bind=lambda xs, f: tuple(y for x in xs for y in f(x)),
    join=lambda xss: tuple(y for xs in xss for y in xs),
)
register_monad(
    set,
    bind=lambda xs, f: {y for x in xs for y in f(x)},
    join=lambda xss: {y for xs in xss for y in xs},
)
