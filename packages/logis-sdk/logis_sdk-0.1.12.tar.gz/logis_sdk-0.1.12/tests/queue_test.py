import asyncio
import queue

from logis.iface import IQueue


def test_queue_type():

    assert asyncio.Queue is not queue.Queue
    assert asyncio.PriorityQueue is not queue.PriorityQueue

    assert issubclass(asyncio.Queue, IQueue)
    assert issubclass(asyncio.PriorityQueue, IQueue)

    assert issubclass(queue.Queue, IQueue)
    assert issubclass(queue.PriorityQueue, IQueue)

    q = queue.Queue()
    q.empty()
