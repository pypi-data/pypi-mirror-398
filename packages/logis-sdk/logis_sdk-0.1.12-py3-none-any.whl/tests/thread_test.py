import threading
import time
from functools import reduce
from threading import Thread


def test_cost():
    def run(dt: int):
        return reduce(lambda x, y: x * y, range(1, 10000))

    start = time.time()
    run(0)
    dt = time.time() - start
    print(dt)

    ts = []
    for i in range(20):
        t = Thread(target=run, args=(i,), name=str(i))
        ts.append(t)
    start = time.time()
    for t in ts:
        t.start()
        t.join()
    dt = time.time() - start
    print(dt)
