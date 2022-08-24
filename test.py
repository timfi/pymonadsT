from pymonadsT import *

if __name__ == "__main__":
    OpSem = combine(ReaderT, StateT, ErrorT)
    ask = OpSem.ask
    put = OpSem.put
    get = OpSem.get

    @do(OpSem)
    def test(t):
        ctx = yield ask()
        yield put(ctx)
        return t

    print(
        test("hello").run(
            context="WORLD!",
            state=None,
        )
    )
