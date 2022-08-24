from .base import combine


__all__ = "Just", "Nothing", "OptionT", "Option"


class Optional:
    ...


class Just(Optional):
    def __init__(self, v):
        self.value = v

    def __repr__(self):
        return f"<Just: {self.value!r}>"

    def map(self, f):
        return Success(f(self.value))

    def bind(self, f):
        return f(self.value)

    __match_args__ = ("value",)


class NothingType(Optional):
    def __repr__(self):
        return "<Nothing>"

    def map(self, f):
        return self

    def bind(self, f):
        return self


Nothing = NothingType()


def OptionT(M):
    class Option:
        def __init__(self, inner):
            self.inner = inner

        @staticmethod
        def unit(v):
            return Option(M.unit(Just(v)))

        def map(self, f):
            return self.bind(lambda v: self.unit(f(v)))

        def bind(self, f):
            return Option(self.inner.bind(lambda v: f(v.value) if isinstance(v, Just) else M.unit(Nothing)))

        @staticmethod
        def lift(m):
            return Option(m.bind(lambda v: M.unit(Just(v))))

        def run(self, *args, **kwargs):
            return self.inner.run(*args, **kwargs)


    def nothing():
        return Option(M.unit(Nothing))

    return Option, {"nothing": nothing}


Option = combine(OptionT)
