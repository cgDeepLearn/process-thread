import time
import random
import asyncio

@asyncio.coroutine
def fast_fib(n):
    """smart one"""
    index = 0
    a, b = 0, 1
    while index < n:
        sleep_secs = random.uniform(0, 0.2)
        yield from asyncio.sleep(sleep_secs)
        print('Fast one think {} secs to get {}'.format(sleep_secs, b))
        a, b = b, a + b
        index += 1


def slow_fib(n):
    """slow one"""
    index = 0
    a, b = 0, 1
    while index < n:
        sleep_secs = random.uniform(0, 0.4)
        yield from asyncio.sleep(sleep_secs)
        print('Slow one think {} secs to get {}'.format(sleep_secs, b))
        a, b = b, a + b
        index += 1

if __name__ == '__main__':
    loop = asyncio.get_event_loop()  # 获取时间循环的引用
    tasks = [
        asyncio.ensure_future(fast_fib(10)),
        asyncio.ensure_future(slow_fib(10))  
        # ensure_future 和create_task都可以，asyncio.async过时了
        # loop.create_task(fast_fib(10)),
        # loop.create_task(slow_fib(10)) 
    ]
    loop.run_until_complete(asyncio.wait(tasks)) 
    print('All fib finished.')
    loop.close()