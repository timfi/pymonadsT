from .base import combine


__all__ = "ContT", "Cont"


def ContT(M):
    class Cont:
        def __init__(self, inner):
            self.inner = inner

        @staticmethod
        def unit(v):
            return Cont(lambda k: M.unit(k(v)))

        def map(self, f):
            return self.bind(lambda v: self.unit(f(v)))

        def bind(self, f):
            return Cont(
                lambda k: self.inner(lambda v: f(v).inner(k))
            )

        @staticmethod
        def lift(m):
            return Cont(lambda k: m.bind(k))

        def run(self, cont, *args, **kwargs):
            return self.inner(cont).run(*args, **kwargs)

    def callcc(f):
        return Cont(
            lambda k: f.inner(lambda v: Cont(lambda _: k(v))).inner(k)
        )

    return Cont, {"callcc": callcc}


Cont = combine(ContT)
