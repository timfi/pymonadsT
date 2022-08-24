from functools import wraps
from inspect import isgeneratorfunction


__all__ = "Identity", "combine", "do"


class Identity:
    def __init__(self, inner):
        self.inner = inner

    @classmethod
    def unit(cls, v):
        return cls(v)

    def map(self, f):
        return Identity.unit(f(self.inner))

    def bind(self, f):
        return f(self.inner)

    @staticmethod
    def lift(m):
        return Identity.unit(m)

    def run(self):
        return self.inner


def combine(*transformers, name="Monad", base=Identity):
    def lift_cons(lift, const):
        def _cons(*args):
            return lift(const(*args))
        return staticmethod(_cons)

    monad = Identity
    constructors = {}
    for transformer in transformers[::-1]:
        monad, new_constructors = transformer(monad)
        constructors = new_constructors | {
            name: lift_cons(monad.lift, constructor)
            for name, constructor in constructors.items()
        }

    return type(name, (monad,), constructors)


def do(m):
    def dec(func):
        @wraps(func)
        def monadic(*args, **kwargs):
            if isgeneratorfunction(func):
                gen = func(*args, **kwargs)
                def proceed(v):
                    try:
                        return gen.send(v).bind(proceed)
                    except StopIteration as e:
                        return m.unit(e.value)
                return proceed(None)
            else:
                return m.unit(func(*args, **kwargs))
        return monadic
    return dec
