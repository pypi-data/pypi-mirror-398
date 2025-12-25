import simpy

from logis.util.simpy_util import (
    interrupt_if_timeout,
    resize_container,
    run_until,
    stop_simulation,
)


def test_resize_container():
    env = simpy.Environment()
    container = simpy.Container(env, init=0, capacity=10)

    def get(n):
        print(f"get {n} start at {env.now}")
        yield container.get(n)
        print(f"get {n} end at {env.now}")

    def put(n):
        print(f"put {n} start at {env.now}")
        yield container.put(n)
        print(f"put {n} end at {env.now}")

    def resize_after(timeout: int, new_capacity: int):
        yield env.timeout(timeout)
        print(f"resize to {new_capacity} at {env.now}")
        resize_container(container, new_capacity)
        print(f"container capacity: {container.capacity}")

    def wait_request_done():
        while container.get_queue or container.put_queue:
            yield env.timeout(1)
            print(f"request not done, {env.now}")

    env.process(put(15))
    env.process(resize_after(5, 20))
    # env.process(wait_request_done())
    env.process(get(10))
    env.run()
    assert container.level == 5


def test_stop_simulation():
    env = simpy.Environment()
    exit_event = env.event()

    def sleep(n):
        print(f"sleep {n} start at {env.now}")
        yield env.timeout(n)
        print(f"sleep {n} end at {env.now}")

    def trigger_exit_after(timeout: int):
        yield env.timeout(timeout)
        exit_event.succeed()

    env.process(sleep(10))
    env.process(trigger_exit_after(6))
    run_until(env, max_sim_time=5, exit_signal=exit_event)
    assert env.now == 5
    run_until(env, max_sim_time=10, exit_signal=exit_event)
    assert env.now == 6
    stop_simulation(env)
    env.run()
    assert env.now == 6
