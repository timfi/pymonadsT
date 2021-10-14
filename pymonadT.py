from functools import wraps, reduce
from inspect import isgenerator


class Identity:
    def __init__(self, inner):
        self.inner = inner

    @classmethod
    def unit(cls, v):
        return cls(v)

    def map(self, f):
        return f(self.inner)

    def bind(self, f):
        return f(self.inner)

    @classmethod
    def lift(cls, m):
        return cls.unit(m)

    def run(self):
        return self.inner


def combine(*transformer, name="Monad", base=Identity):
    def lift_cons(lift, const):
        def _cons(*args):
            return lift(const(*args))
        return staticmethod(_cons)

    def _combine(acc, trans):
        inner_m, inner_cons = acc
        new_m, new_cons = trans(inner_m)
        return new_m, new_cons | {
            name: lift_cons(new_m.lift, cons)
            for name, cons in inner_cons.items()
        }

    raw, const = reduce(_combine, transformer[::-1], (base, {}))
    return type(name, (raw,), const)


def do(m):
    def dec(func):
        @wraps(func)
        def monadic(*args, **kwargs):
            gen = func(*args, **kwargs)
            if isgenerator(gen):


                def proceed(v):
                    try:
                        return gen.send(v).bind(proceed)
                    except StopIteration as e:
                        return m.unit(e.value)
                return proceed(None)
            else:
                return m.unit(gen)
        return monadic
    return dec


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
        return State(lambda _: M.unit((None, s)))

    return State, {"get": get, "put": put}


State = combine(StateT)


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


class Failable:
    def bind(self, f):
        return Error.from_failable(self).bind(f).run()

    def map(self, f):
        return Error.from_failable(self).map(f).run()


class Success(Failable):
    def __init__(self, v):
        self.value = v

    def __repr__(self):
        return f"<Success: {self.value!r}>"

    def match(self, success, failure):
        return success(self.value)


class Failure(Failable):
    def __init__(self, v):
        self.value = v

    def __repr__(self):
        return f"<Failure: {self.value!r}>"

    def match(self, success, failure):
        return failure(self.value)


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

    def from_failable(v):
        return Error(M.unit(v))

    return Error, {"from_failable": from_failable}


Error = combine(ErrorT)


class Optional:
    def bind(self, f):
        return Option.from_option(self).bind(f).run()

    def map(self, f):
        return Option.from_option(self).map(f).run()


class Just(Optional):
    def __init__(self, v):
        self.value = v

    def __repr__(self):
        return f"<Just: {self.value!r}>"

    def match(self, just, nothing):
        return just(self.value)


class NothingType(Optional):
    def __repr__(self):
        return "<Nothing>"

    def match(self, just, nothing):
        return nothing()


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

    def from_option(v):
        return Option(M.unit(v))

    return Option, {"from_option": from_option}


Option = combine(OptionT)

if __name__ == "__main__":
    OpSem = combine(ContT, ReaderT, StateT, ErrorT)

    @do(OpSem)
    def test():
        ctx = yield OpSem.ask()
        yield OpSem.put(ctx)
        return Just("hello").map(lambda x: x + " fine")


    print(
        test().run(
            cont=lambda x: x,
            context="WORLD!",
            state=None,
        )
    )
