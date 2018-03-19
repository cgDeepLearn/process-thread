# Python协程: 从yield/send到asyncio.coroutine到async/await 

Python由于众所周知的GIL的原因,同一时刻只能有一个线程在运行，那么对于CPU密集的程序来说，线程之间的切换开销就成了拖累，而以I/O为瓶颈的程序正是协程所擅长的：

**多任务并发（非并行），每个任务在合适的时候挂起（发起I/O）和恢复(I/O结束)**

Python中的协程经历了很长的一段发展历程。其大概经历了如下三个阶段：

1. 最初的生成器进化的yield/send
1. python3.4引入@asyncio.coroutine和yield from
1. 在Python3.5版本中引入async/await关键字

## yield/send

我们用斐波那契数列做个例子

### 传统的方式

```python
def normal_fib(n):
    """返回斐波那契数列前n项"""
    res = [0] * n
    index = 0
    a, b = 0, 1
    while index < n:
        res[index] = b
        a, b = b, a + b
        index += 1
    return res

print('-'*10 + 'test old fib' + '-'*10)
for fib_res in normal_fib(20):
    print(fib_res)
```

如果我们仅仅是需要拿到斐波那契序列的第n位，或者仅仅是希望依此产生斐波那契序列，那么上面这种传统方式就会比较耗费内存。这时生成器的特性就派上用场了---> `yield`!!!

### yield

我们用`yield`实现菲波那切数列。

```python
def gen_fib(n):
    """斐波那契数列生成器"""
    index = 0
    a, b = 0, 1
    while index < n:
        yield b
        a, b = b, a + b
        index += 1

print('-'*10 + 'test yield fib' + '-'*10)
for fib_res in fib(20):
    print(fib_res)
```

当一个函数中包含`yield`语句时，python会自动将其识别为一个生成器。这时fib(20)并不会真正调用函数体，而是以函数体生成了一个生成器对象实例。

`yield`在这里可以保留`gen_fib`函数的计算现场，暂停`gen_fib`的计算并将b返回。而将fib放入`for…in`循环中时，每次循环都会调用`next(fib(20))`，唤醒生成器，执行到下一个`yield`语句处，直到抛出`StopIteration`异常。此异常会被for循环捕获，导致跳出循环。

### send

`send` 事件驱动，生成器进化成协程

```python
import time
import random

def coro_fib(n):
    """斐波那契协程,send一个间隔时间，产出一个值"""
    index = 0
    a, b = 0, 1
    while index < n:
        sleep_sec = yield b  # 产出b，将send值绑定到sleep_sec,
        print('wait {} secs.'.format(sleep_sec))
        time.sleep(sleep_sec)
        a, b = b, a + b
        index += 1

print('-'*10 + 'test yield send' + '-'*10)
N = 20
cfib = coro_fib(N)
fib_res = next(cfib)  # 预激协程,运行至yield处暂停
while True:
    print(fib_res)
    try:
        fib_res = cfib.send(random.uniform(0, 0.5))  # send驱动协程, 修改合适的时间清楚执行过程
    except StopIteration:
        break
```

协程更多详细信息请移步[python coroutine](coroutine.md)这里~

### yield from

`yield from`用于重构生成器，简单的，可以这么使用：

```python
def copy_fib(n):
    print('I am copy from gen_fib')
    yield from gen_fib(n)  # 委派给gen_fib生成器
    print('Copy end')
print('-'*10 + 'test yield from' + '-'*10)
for fib_res in copy_fib(20):
    print(fib_res)
```

这种使用方式很简单，但远远不是`yield from`的全部。`yield from`的作用还体现可以像一个管道一样将`send`信息传递给内层协程，并且**处理好了各种异常情况**，因此，对于`coro_fib`也可以这样包装和使用：

```python
def copy_coro_fib(n):
    print('I am copy from coro_fib')
    yield from coro_fib(n)  # 委托给coro_fib,异常也交由它处理
    print('Copy end')
print('-'*10 + 'test yield from and send' + '-'*10)
N = 20
ccfib = copy_coro_fib(N)
fib_res = next(ccfib)
while True:
    print(fib_res)
    try:
        fib_res = ccfib.send(random.uniform(0, 0.5))
    except StopIteration:
        break
```

## asyncio/yield from

`asyncio`是一个基于事件循环的实现`异步I/O`的模块。通过`yield from`，我们可以将协程的控制权交给事件循环，然后挂起当前协程；之后，由事件循环决定何时唤醒协程,接着向后执行代码。

使用`asyncio.coroutine`装饰器

```python
# 并发处理两个快慢不一的斐波那契生成函数

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
        sleep_secs = random.uniform(0, random_sec)
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
```

运行结果如下:

```
...
Fast one think 0.0393240884371622 secs to get 21
Slow one think 0.12157996704037113 secs to get 5
Fast one think 0.08259000223641344 secs to get 34
Slow one think 0.15816909012449587 secs to get 8
Fast one think 0.1967429201039252 secs to get 55
Slow one think 0.25365548691367573 secs to get 13
Slow one think 0.3235222687782598 secs to get 21
Slow one think 0.35160632142878434 secs to get 34
Slow one think 0.34477299780059134 secs to get 55
All fib finished.
```

## async/await

清楚了`asyncio.coroutine`和`yield from`之后，在Python3.5中引入的`async`和`await`就不难理解了：
可以将他们理解成`asyncio.coroutine/yield from`的完美替身。当然，从Python设计的角度来说，`async/await`让协程表面上独立于生成器而存在，将细节都隐藏于`asyncio`模块之下，语法更清晰明了。

async/await 示例:

```python
# 使用 async/await 关键字

async def fast_fib(n):
    """smart one"""
    index = 0
    a, b = 0, 1
    while index < n:
        sleep_secs = random.uniform(0, 0.2)
        await asyncio.sleep(sleep_secs)
        print('Fast one think {} secs to get {}'.format(sleep_secs, b))
        a, b = b, a + b
        index += 1


async def slow_fib(n):
    """slow one"""
    index = 0
    a, b = 0, 1
    while index < n:
        sleep_secs = random.uniform(0, random_sec)
        await asyncio.sleep(sleep_secs)
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
```

可以发现相比上面`yield from`的版本只改变了以下两点:

* 函数定义前面加了`async`关键字，更加清晰表明这是一个协程
* `yield from` 换成了`await`关键字

## 总结

示例程序中都是以sleep为异步I/O的代表，在实际项目中，可以使用协程异步的读写网络、读写文件、渲染界面等，而在等待协程完成的同时，CPU还可以进行其他的计算。协程的作用正在于此。