# threading

## python线程

可以用线程来执行阻塞式I/O,但不要用它做平行计算

标准的Python实现叫做CPython。Cpython分两步来运行Python程序：

1. 首先，把文本形式的源代码解析并编译成字节码
2. 然后，用一种基于栈的解释器来运行这份字节码

执行Python程序时，字节码解释器必须保持协调一致的状态。Python采用GIL(global inerpreter lock,全局解释器锁)机制来确保这种协调性(coherence)。

GIL实际上就是一把互斥锁(mutual-exclusion-lock,又称为mutex)，用以防止CPython受到占先式多线程切换(preemptive multithreaing)操作的干扰。

GIL有一种非常显著额负面影响。用C++或者Java等语言写程序时，可以同时执行多条线程，以充分利用计算机所配备的多个CPU核心。Python程序尽管也支持多线程，但由于受到GIL保护，所以同一时刻，只有一条线程可以向前执行。这就意味着，如果我们想利用多线程做平行计算(parallel computation)， 并希望借此为Python程序提速，那么结果会非常令人失望。

既然如此，Python为什么还要支持多线程呢？

* 首先，多线程使得到程序看上去好像能够在同一时间做许多事情。如果要自己实现这种效果，并手工管理任务之间的切换，那就显得比较困难
* 其次，在处理阻塞式I/O时很有用。读写文件、在网络间通信，以及与显示器等设备相交互等，都属于阻塞式的I/O操作。为了响应这种阻塞式的请求，操作系统必须花一些时间，而开发者可以借助多线程，把python程序与这些耗时的I/O操作隔离开。(python在执行系统调用的时候会释放GIL)。当然除了线程，还有一些其他的方，也能处理阻塞式的I/O操作，例如内置的asyncio模块等。相对于这些模块，使用多线程来实现会比较简单一些。

### threading.Thread

Thread 是threading模块中最重要的类之一，可以使用它来创建线程。有两种方式来创建线程：

* 一种是创建一个threading.Thread对象，在它的初始化函数（__init__）中将可调用对象作为参数传入。
* 另一种是通过继承Thread类，重写它的run方法；

下面分别举例说明：开启`4`个线程，每个线程进行`10`次`+1`操作

* 先来看看通过创建继承`threading.Thread`对象来创建线程的例子：

```python
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
```

* `继承Thread类`:

```python
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
```

* 相对于方法一的修改，不使用`global`而是使用一个`自定义的counter类`

```python
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

```

运行：

```python
if __name__ == '__main__':
    print('-----method1-----:')
    thread_num = 4
    func1_main(thread_num) 
    print('-----method2-----:')
    func2_main(thread_num)
    print('-----method3-----:')
    counter = LockingCounter(0)
    func3_main(thread_num, worker, 10, counter)
```

### 使用Queue来协调各线程之间的工作

管线(Pipeline)是一种优秀的任务处理方式，它可以把处理流程分为若干阶段，并使用多条Python线程来同时执行这些任务

构建并发式的管线时，要注意许多问题，其中包括：如何防止某个阶段陷入持续等待的状态之中、如何停止工作线程，以及如何防止内存膨胀等。

Queue类所提供的的机制，可以彻底解决上述问题，它具备阻塞式的队列操作、能够制定缓冲区尺寸，而且还支持join方法，这使得开发者可以构建出健壮的管线。

* 示例：生产者消费者模型
```python
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

    # 生产者线程，每个线程生产10个，1号线程生产1，10，2号生产11-20......
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
```

output:

```python
...
...
[+] 生产者1号 生产 item8
[-] 消费者2号 消费 item8
[+] 生产者1号 生产 item9
[-] 消费者3号 消费 item9
[+] 生产者1号 生产 item10
[-] 消费者2号 消费 item10
[x] 消费者1号 退出
[x] 消费者3号 退出
[x] 消费者2号 退出
all done
```


* 管线

我们构建一个有三个阶段的管线：下载图片-->>调整大小-->>重新上传

```python
# -*- coding: utf-8 -*-
"""用threading模块和Queue实现管线"""
import time
import threading
from queue import Queue


class ClosableQueue(Queue):
    """带有终止信号的Queue
    close时put终止信号"""
    SENTINEL = object()  # 终止信号

    def close(self):
        self.put(self.SENTINEL)

    def __iter__(self):
        while True:
            item = self.get()
            try:
                if item is self.SENTINEL:
                    return # 致使线程退出
                yield item
            finally:
                self.task_done()


class StopableWorker(threading.Thread):
    """queue遇到终止信号的线程退出"""
    def __init__(self, func, in_queue, out_queue):
        super().__init__()
        self.func = func
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        for item in self.in_queue:
            result = self.func(item)
            if result is not None:
                self.out_queue.put(result)


def download(item):
    """下载"""
    print('download item ', item)
    time.sleep(0.1)
    return item 

def resize(item):
    """调整"""

    print('resize item ', item)
    time.sleep(0.1)
    return item

def upload(item):
    """上传"""
    print('upload item ', item)
    return item 


def main():
    """主程序"""
    # 各阶段队列
    download_queue = ClosableQueue()
    resize_queue = ClosableQueue()
    upload_queue = ClosableQueue()
    out_queue = Queue()
    # 线程
    threads = [
        StopableWorker(download, download_queue, resize_queue),
        StopableWorker(resize, resize_queue, upload_queue),
        StopableWorker(upload, upload_queue, out_queue)
    ]

    for thread in threads:
        thread.start()

    for i in range(1, 101):
        download_queue.put(i)

    download_queue.close()
    download_queue.join()

    resize_queue.close()
    resize_queue.join()

    upload_queue.close()
    upload_queue.join()

    print(out_queue.qsize(), 'pictures finished')
    # while not out_queue.empty():
    #     print(out_queue.get())

if __name__ == '__main__':
    main()
```

output:

```python
...
...
upload item  96
resize item  97
upload item  97
resize item  98
download item  99
download item  100
resize item  99
upload item  98
upload item  99
resize item  100
upload item  100
100 pictures finished
```
