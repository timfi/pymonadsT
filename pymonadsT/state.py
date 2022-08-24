from .base import combine


__all__ = "StateT", "State"


def StateT(M):
    class State:
        def __init__(self, inner):
            self.inner = inner

        @staticmethod
        def unit(v):
            return State(lambda s: M.unit((v, s)))

        def map(self, f):
            return self.bind(lambda v: self.unit(f(v)))

        def bind(self, f):
            return State(lambda s: self.inner(s).bind(lambda t: f(t[0]).inner(t[1])))

        @staticmethod
        def lift(m):
            return State(lambda s: m.bind(lambda a: M.unit((a, s))))

        def run(self, state, *args, **kwargs):
            return self.inner(state).run(*args, **kwargs)

    def get():
        return State(lambda s: M.unit((s, s)))

    def put(s):
        return State(lambda _: M.unit((s, s)))

    def update(f):
        return State(lambda s: M.unit((s, f(s))))

    return State, {"get": get, "put": put, "update": update}


State = combine(StateT)
