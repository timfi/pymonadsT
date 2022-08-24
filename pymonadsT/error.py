from .base import combine

__all__ = "Success", "Failure", "ErrorT", "Error"

class Failable:
    ...


class Success(Failable):
    def __init__(self, v):
        self.value = v

    def __repr__(self):
        return f"<Success: {self.value!r}>"

    def match(self, success, failure):
        return success(self.value)

    def map(self, f):
        return Success(f(self.value))

    def bind(self, f):
        return f(self.value)

    __match_args__ = ("value",)


class Failure(Failable):
    def __init__(self, v):
        self.value = v

    def __repr__(self):
        return f"<Failure: {self.value!r}>"

    def match(self, success, failure):
        return failure(self.value)

    def map(self, f):
        return self

    def bind(self, f):
        return self

    __match_args__ = ("value",)


def ErrorT(M):
    class Error:
        def __init__(self, inner):
            self.inner = inner

        @staticmethod
        def unit(v):
            return Error(M.unit(Success(v)))

        def map(self, f):
            return self.bind(lambda v: self.unit(f(v)))

        def bind(self, f):
            def capture(f, v):
                try:
                    return f(v)
                except Exception as e:
                    return M.unit(Failure(e))

            return Error(self.inner.bind(
                lambda v: M.unit(v) if isinstance(v, Failure) else capture(f, v.value)
            ))

        @staticmethod
        def lift(m):
            return Error(m.bind(lambda v: M.unit(Success(v))))

        def run(self, *args, **kwargs):
            return self.inner.run(*args, **kwargs)

    def failure(v):
        return Error(M.unit(Failure(v)))

    return Error, {"failure": failure}


Error = combine(ErrorT)
