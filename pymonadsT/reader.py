from .base import combine


__all__ = "ReaderT", "Reader"


def ReaderT(M):
    class Reader:
        def __init__(self, inner):
            self.inner = inner

        @staticmethod
        def unit(v):
            return Reader(lambda e: M.unit(v))

        def map(self, f):
            return self.bind(lambda v: self.unit(f(v)))

        def bind(self, f):
            return Reader(lambda e: self.inner(e).bind(lambda t: f(t).inner(e)))

        def run(self, context, *args, **kwargs):
            return self.inner(context).run(*args, **kwargs)

        @staticmethod
        def lift(m):
            return Reader(lambda _: m)

    def ask():
        return Reader(lambda e: M.unit(e))

    def local(f, m):
        return Reader(lambda e: m.inner(f(e)))

    return Reader, {"ask": ask, "local": local}


Reader = combine(ReaderT)
