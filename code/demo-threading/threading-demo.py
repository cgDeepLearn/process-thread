# -*- coding: utf-8 -*-
"""threading模块"""


import time
import random
import threading


def func1(loop):
    """创建threading.Thread对象的方式创建线程"""
    global func1_count, func1_lock
    thread_name = threading.currentThread().getName()  # 获取线程名
    for _ in range(loop):
        with func1_lock:
            func1_count += 1
        print(thread_name, func1_count)
        time.sleep(1)

def func1_main(num):
    global func1_count, func1_lock
    threads = []
    func1_count = 0
    func1_lock = threading.Lock()  # 线程中使用Lock防止数据竞争
    for i in range(num):
        t = threading.Thread(target=func1,args=(10, ))
        threads.append(t)
    
    for t in threads:
        t.start()  # 启动所有线程
    for t in threads:
        t.join()  # 主线程中等待所有子线程退出


class Counter(threading.Thread):
    my_count = 0  # 类变量
    my_lock = threading.Lock()
    def __init__(self, loop=10):
        super().__init__()
        self._loop = loop
        # self._count = init_count
        # self._lock = threading.Lock()
    
    def run(self):
        thread_name = threading.currentThread().getName()
        for _ in range(self._loop):
            
            with Counter.my_lock:
                Counter.my_count += 1
            print(thread_name, Counter.my_count)
            time.sleep(1)

def func2_main(num):
    threads = []
    for _ in range(num):
        t = Counter()  # 默认loop为10，init_count为0
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

class LockingCounter(object):
    def __init__(self, init_count):
        self._lock = threading.Lock()
        self._count = init_count

    def increase(self, offset=1):
        with self._lock:
            self._count += 1

def worker(index, loop, counter):
    thread_name = threading.currentThread().getName()
    for _ in range(loop):
        counter.increase(1)
        print(thread_name, counter._count)
        time.sleep(1)

def func3_main(num, func, loop, counter):
    threads = []
    for i in range(num):
        args = (i, loop, counter)
        t = threading.Thread(target=func, args=args)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

if __name__ == '__main__':
    print('-----method1-----:')
    thread_num = 4
    func1_main(thread_num) 
    print('-----method2-----:')
    func2_main(thread_num)
    print('-----method3-----:')
    counter = LockingCounter(0)
    func3_main(thread_num, worker, 10, counter)

