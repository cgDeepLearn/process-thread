# -*- coding:utf-8 -*-
"""
多线程生产者消费者模型
Python中，队列是线程间最常用的交换数据的形式之一。Queue模块是python中提供队列操作的模块。
创建一个"队列"对象（即用于存放数据的buffer）, 然后不断产生数据并存入该"队列"，同时也在不断地从该队列中取出数据。
"""


import time
import random
import threading
from queue import Queue  # 队列模块
from itertools import chain

q = Queue()
sentinel = object()  # 结束标记


def Producer(nums):
    """生产者函数
    nums:product起始编号元组,例如(1,10)"""
    thread_name = threading.currentThread().getName()
    for item in range(*nums):
        q.put(item)
        print('[+] %s 生产 item%s' % (thread_name,item))
        time.sleep(random.randrange(2))  # 控制生产速度


def Consumer():
    """消费者函数"""
    thread_name = threading.currentThread().getName()
    while True:
        data = q.get()

        if data is sentinel:
            print('[x] %s 退出' % thread_name)
            break
        print('[-] %s 消费 item%s' % (thread_name, data))

        time.sleep(1)


def run():
    """主函数"""
    pnum = 2
    cnum = 3

    # 每个线程生产10个，1号线程生产1，10，2号生产11-20......
    pthreads = [
        threading.Thread(target=Producer,
                         args=((i * 10 + 1, (i + 1) * 10 + 1),),
                         name="生产者%d号" % (i + 1))
        for i in range(pnum)]
    # 消费者线程
    cthreads = [
        threading.Thread(target=Consumer, name="消费者%d号" % (i + 1))
        for i in range(cnum)]

    for thread in chain(pthreads, cthreads):
        thread.start()

    for pt in pthreads:
        pt.join()  # 生产线程阻塞
    for _ in range(cnum):
        q.put(sentinel)  # put结束标记
    for ct in cthreads:
        ct.join()

    print("all done")


if __name__ == '__main__':
    run()
