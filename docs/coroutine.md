---
title: Python协程-coroutine
categories:
  - Python
  - 进程线程协程
tags:
  - yield
  - coroutine
  - yield from
copyright: true
date: 2018-01-30 10:45:38
top:
password:
description:
image:
---
<p class="description">考虑用协程来并发的运行多个函数
</p>

<img src="" alt="" style="width:100%" />

## 前言

<div class="note primary"><p>
我们可以用线程来运行多个函数，使这些函数看上去好像是在同一时间得到执行的。然而，线程有`三`个显著的缺点：
<ul>
<li><i class="fa fa-minus-square"></i> 为了确保数据安全，我们必须使用特殊的工具(`Lock`, `Queue`等)来协调这些线程，这使得多线程的代码，要比单线程的过程式代码更加难懂。这些复杂的多线程代码，会逐渐令程序变得难以扩展和维护。</li>
<li><i class="fa fa-minus-square"></i> 线程需要`占用大量内存`，每个正在执行的线程，大约占据`8MB`内存。如果只开十几个线程，多数计算机还是可以承受的。</li>
<li><i class="fa fa-minus-square"></i> 线程`启动的开销比较大`。如果程序不停地依靠创建新线程来同时执行多个函数，并等待这些线程结束，那么使用线程所引发的开销，就会拖慢整个程序的速度。</li>
</ul></p></div>

<!-- more -->

Python的`协程(coroutine)`可以避免上述问题，它使得Python程序看上去好像是在同时运行多个函数。协程的实现方式，实际上是对生成器的一种扩展。启动生成器协程所需的开销，与调用函数的开销相仿。处于活跃状态的协程，在其耗尽之前，只会占用不到`1KB`的内存。

## 协程的工作原理

每当生成器函数执行到`yield`表达式的时候，消耗生成器的那段代码，就通过`send`方法给生成器回传一个值。而生成器在手熬了经由send函数所传进来的这个值后，这个值会绑定给`yield`关键字左边的变量；如果`yield`关键字右边有表达式，那么`yield`表达式右侧的内容会当成send方法的返回值(没有的话其实返回的是`None`)，返回给外界(调用方).关键的一点是，协程在 `yield` 关键字所在的位置暂停执行。在赋值语句中， `=` 右边的代码在赋值之前执行。下面我们结合两个例子来看看。

### 简单的协程示例

```python  简单协程示例
def my_coroutine():
    while True:
        received = yield
        print('Received:', received)

it = my_coroutine()
next(it)  # 1
it.send('First')  # 2
it.send('Second')

>>>
Received: First
Received: Second
```

<i class="fa fa-pencil"></i>注1: 在生成器上面调用`send`方法，我们要先调用next函数(这叫`预激协程`)，以便将生成器推进到第一条`yield`表达式那里

### 协程产出值

该示例在协程每收到一个数值，就会产出当前所统计到的最大值

```python 协程产出值
def maximize():
    current = yield  # 1
    while True:
        value = yield current  # 2
        current = max(value, current)  # 3

it = maximize()
next(it)  # 预激协程，执行到第一个yield处
print(it.send(10)) # 执行到#2处产出current值，等待接收值
print(it.send(12)) # 绑定12给value，计算current，执行到#2处产出current值，等待接收值
print(it.send(4))  # 同上，即执行到yield表达式右边，等待左边输入绑定
print(it.send(22))

>>>
10
12
12
22
```

上面的代码范例中，第一条`yield`语句中的`yield`关键字后面没有跟随内容，其意思是，把外面传进来的首个值，当成目前的最大值。
此后生成器会屡次执行while循环中的那条`yield`语句，以便将当前统计到的最大值告诉外界，同时等候外界传入下一个待考察的值。

<div class="note info"><p>协程在yield关键字所在的位置暂停执行。在赋值语句中， = 右边的代码在赋值之前执行。即各个阶段都在yield表达式中结束，先产出值然后在yield出暂停，等待外界传入值。下一个阶段都从那一行代码开始</p></div>

## yield from 

协程可以通过yield的输出值来推进其他的生成器函数，使得那些生成器函数也执行到它们各自的下一条yield比到时处。接连推进多个独立的生成器，即可模拟出Python线程的并发行为，令程序看上去好像是在同时运行多个函数

### 使用yield from计算平均值并输出统计报告

从一个字典中读取虚构的七年级男女学生的体重和身高。例如，'boys;m' 键对应于 9 个男学生的身高（单位是米）， 'girls;kg' 键对应于 10 个女学生的体重（单位是千克）。这个脚本把各组数据传给前面定义的 averager 协程，然后生成一个报告。

```python 使用yield from计算平均值并输出统计报告
# -*- coding: utf-8 -*-
"""使用yield from计算平均值并输出统计报告"""

from collections import namedtuple

Result = namedtuple('Result', 'count average')

# 子生成器
def averager():  # 1
    total = 0.0
    count = 0
    average = None
    while True:
        term = yield  # 2
        if term is None:  # 3
            break
        total += term
        count += 1
        average = total / count
    return Result(count, average)  # 4

# 委派生成器
def grouper(results, key):  # 5
    while True:  # 6
        results[key] = yield from averager()  # 7
# 客户端代码，即调用方
def main(data):  # 8
    results = {}
    for key, values in data.items():
        group = grouper(results, key)  # 9
        next(group)  # 10
        for value in values:
            group.send(value)  # 11
        group.send(None)  # 重要！ 12
    print(results)  # 如果要调试，去掉注释
    report(results)
# 输出报告

def report(results):
    for key, result in sorted(results.items()):
        group, unit = key.split(';')
        print('{:2} {:5} averaging {:.2f}{}'.format(
            result.count, group, result.average, unit))

DATA = {
    'girls;kg': [40.9, 38.5, 44.3, 42.2, 45.2, 41.7, 44.5, 38.0, 40.6, 44.5],
    'girls;m': [1.6, 1.51, 1.4, 1.3, 1.41, 1.39, 1.33, 1.46, 1.45, 1.43],
    'boys;kg': [39.0, 40.8, 43.2, 40.8, 43.1, 38.6, 41.4, 40.6, 36.3],
    'boys;m': [1.38, 1.5, 1.32, 1.25, 1.37, 1.48, 1.25, 1.49, 1.46],
}

if __name__ == '__main__':
    main(DATA)
```

<div class="note info"><p>
1-  与示例 16-13 中的 averager 协程一样。这里作为子生成器使用。
2-  main 函数中的客户代码发送的各个值绑定到这里的 term 变量上。
3-  至关重要的终止条件。如果不这么做，使用 yield from 调用这个协程的生成器会永
远阻塞。
4- 返回的 Result 会成为 grouper 函数中 yield from 表达式的值。
5-  grouper 是委派生成器。
6-  这个循环每次迭代时会新建一个 averager 实例；每个实例都是作为协程使用的生成器对象。
7-  grouper 发送的每个值都会经由 yield from 处理，通过管道传给 averager 实例。 grouper 会在 yield from 表达式处暂停，等待 averager 实例处理客户端发来的值。 averager 实例运行完毕后，返回的值绑定到 results[key] 上。 while 循环会不断创建 averager 实例，处理更多的值。
8- main 函数是客户端代码，用 PEP 380 定义的术语来说，是“调用方”。这是驱动一切的函数
9- group 是调用 grouper 函数得到的生成器对象，传给 grouper 函数的第一个参数是results，用于收集结果；第二个参数是某个键。 group 作为协程使用。
10- 预激 group 协程。
11- 把各个 value 传给 grouper。传入的值最终到达 averager 函数中 term = yield 那一行； grouper 永远不知道传入的值是什么。
12- 把 None 传入 grouper，导致当前的 averager 实例终止，也让 grouper 继续运行，再创建一个 averager 实例，处理下一组值。
</p></div>

## 生命游戏：演示协程的协同运作效果。

### 游戏规则

- 在一个任意尺寸的二维网格中，每个细胞(即每个单元格)都处于`生存(alive,用*表示)`或`空白(empty,用-表示)`状态。
- 时钟每走一步，生命游戏就向前进一步。向前推进时，我们要点算每个细胞周边的那八个单元格，看看该细胞附近有多少个存活的细胞。然后根据存活的数量来判断自己下一轮是继续存活、死亡还是再生。
- 具体判断规则
  - 若本细胞存活，且周围存活者不足两个，则本细胞下一轮死亡。
  - 若本细胞存活，且周围的存活者多于3个，则本细胞下一轮死亡。
  - 若本细胞死亡，且周围的存活者恰有3个，则本细胞下一轮再生。

### 建模

基于规则我们可以将整个程序分成三个阶段:`count_neighbors`, `step_cell`, `display`

- count_neighbors: 计算每个细胞附近8个细胞存活的数目
- step_cell: 根据细胞本轮状态和计算得到周围的细胞数量生成下一轮的状态
- 根据每轮的结果显示细胞状态

#### count_neighbors

我们定义一个协程来获取周围细胞的生存状态。协程会产生一个自定义的`Query`对象，每个`yield`表达式的结果，要么是`ALIVE`，要么是`EMPTY`。其后count_neighbors生成器会根据相邻细胞的状态，来返回本细胞周围的存活细胞数(生成器return语句在python3中才可用，实际是把结果作为StopIteration异常的value属性传给了调用者)

```python count_neighbors协程计算细胞周围的存活数目
from collections import namedtuple

ALIVE = '*'
EMPTY = '-'

Query = namedtuple('Query', ('y', 'x'))

def count_neighbors(y, x):
    n_ = yield Query(y + 1, x + 0)  # North
    ne = yield Query(y + 1, x + 1)  # Northeast
    e_ = yield Query(y + 0, x + 1)  # East
    se = yield Query(y - 1, x + 1)  # Southeast
    s_ = yield Query(y - 1, x + 0)  # South
    sw = yield Query(y - 1, x - 1)  # Southwest
    w_ = yield Query(y + 0, x - 1)  # West
    nw = yield Query(y + 1, x - 1)  # Northwest
    neighbor_states = [n_, ne, e_, se, s_, sw, w_, nw]
    count = 0
    for state in neighbor_states:
        if state == ALIVE:
            count += 1
    return count
```

我们用虚构的数据来测试一下这个count_neighbors协程.
下面这段代码，会针对本细胞的每个相邻细胞，向生成器索要一个`Query`对象，并产出`Query namedtuple`。然后通过`send`方法把状态发给协程，使`count_neighbors`协程可以收到上一个`Query`对象所对应的状态(注意我们上文提到的`yield`表达式一行执行顺序--先右再左)

```python 测试count_neighbors协程
    >>> it = count_neighbors(10, 5)
    >>> next(it)  # Get the first query, for q1
    Query(y=11, x=5)
    >>> it.send(ALIVE)  # Send q1 state, get q2
    Query(y=11, x=6)
    >>> it.send(ALIVE)  # Send q2 state, get q3
    Query(y=10, x=6)
    >>>  # Send q3 ... q7 states, get q4 ... q8
    >>> [it.send(state) for state in (EMPTY)*5]  # doctest: +ELLIPSIS
    [Query(y=9, x=6), Query(y=9, x=5), ..., Query(y=11, x=4)]
    >>> try:
    ...     it.send(EMPTY)  # Send q8 state, drive coroutine to end
    ... except StopIteration as e:
    ...     count = e.value  # Value from return statement
    ...
    >>> count
    2
```

#### step_cell

计算出了细胞周围的存活数量，我们就需要根据这个数量来更新细胞的状态。并把得到的状态传给外部调用者。
这里我们自定义了一个`Transition`对象，它表示坐标位于(y,x)的细胞的下一轮的状态。

```python step_cell根据count_neighbors计算出来的存活状态数量产生下一轮的状态
Transition = namedtuple('Transition', ('y', 'x', 'state'))  # state即是下一轮的状态

def step_cell(y, x):
    current_state = yield Query(y, x) # 获取当前状态
    neighbors = yield from count_neighbors(y, x)  # 委派给子生成器count_neighbors 
    next_state = game_logic(state, neighbors)  # game_logic根据规则判断下一轮状态
    yield Transition(y, x, next_state)

def game_logic(state, neighbors):
    # 这里其实我们可以使用是否等于3来简化判断
    if state == ALIVE:
        if neighbors < 2:
            return EMPTY     # Die: Too few
        elif neighbors > 3:
            return EMPTY     # Die: Too many
    else:
        if neighbors == 3:
            return ALIVE     # Regenerate
    return state
```

下面我们用虚拟数据来测试一下`step_cell`协程：

```python 测试step_cell协程
    >>> it = step_cell(10, 5)
    >>> next(it)  # Initial location query
    Query(y=10, x=5)
    >>> [it.send(st) for st in (ALIVE)*5 + (EMPTY)*3]   # doctest: +ELLIPSIS
    [Query(y=11, x=5), Query(y=11, x=6), ... Query(y=11, x=4)]
    >>> it.send(EMPTY)  # Send q8 state, get game decision
    Transition(y=10, x=5, state='-')
```

上面演示了在网格中一个细胞的一次前进。下面我们把`step_cell`组合到新的`simulate`协程之中。新的协程会多次通过yield from 表达式，来推进网格中的每一个细胞。把每个细胞处理完后，`simulate`协程会产生`TICK`对象，用以表示当前这一代的细胞已经全部迁移完毕。

```python simulate
def simulate(height, width):
    while True:
        for y in range(height):
            for x in range(width):
                yield from step_cell(y, x)  # 委派给子生成器step_cell
        yield TICK
```

#### 网格显示状态

为了在真实环境中运行`simulate`，我们需要把网格中的每个细胞状态表示出来。我们定义一个Grid类，来代表整张网格：

```python Grid类显示网格和细胞状态
class Grid(object):
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.rows = []
        for _ in range(self.height):
            self.rows.append([EMPTY] * self.width)

    def __str__(self):
        output = ''
        for row in self.rows:
            for cell in row:
                output += cell
            output += '\n'
        return output

    def __getitem__(self, position):
        y, x = position
        # 如果传入的坐标值越界，我们用取余来自动折回
        return self.rows[y % self.height][x % self.width]

    def __setitem__(self, position, state):
        y, x = position
        self.rows[y % self.height][x % self.width] = state
```

我们定义了`__getitem__`和`__setitem__`两个元方法来设置和获取`state。下面我们看一下Grid的显示：

```python 根据参数Grid生成网格和状态
    >>> grid = Grid(5, 9)
    >>> grid[0, 3] = ALIVE
    >>> grid[1, 4] = ALIVE
    >>> grid[2, 2] = ALIVE
    >>> grid[2, 3] = ALIVE
    >>> grid[2, 4] = ALIVE
    >>> print(grid)
    ---*-----
    ----*----
    --***----
    ---------
    ---------
```

#### live_a_generation

这个函数把网格内的所有细胞都向前推进一步，待各细胞状态迁移完成后，这些细胞就构成了一张新的网格，该函数会把新的网格返回给调用者。

```python live_a_generation
def live_a_generation(grid, sim):
    # grid: 现阶段网格对象；sim: simulate生成器对象
    progeny = Grid(grid.height, grid.width)  # 下一代网格对象 
    item = next(sim)
    while item is not TICK:
        if isinstance(item, Query):  #计算附近细胞
            state = grid[item.y, item.x]
            item = sim.send(state)
        else:  # Must be a Transition，附近细胞算完了,得到Transition对象
            progeny[item.y, item.x] = item.state
            item = next(sim) # 生成器运行到下一个yield处，即simulate的下一个坐标处
    return progeny  #返回下一轮的网格对象
```

`live_a_generation`是将当前细胞向前推进一步，现在我们把每一代的结果都显示出来

```python ColumnPrinter
class ColumnPrinter(object):
    def __init__(self):
        self.columns = []

    def append(self, data):
        self.columns.append(data)

    def __str__(self):
        row_count = 1
        for data in self.columns:
            row_count = max(row_count, len(data.splitlines()) + 1)
        rows = [''] * row_count
        for j in range(row_count):
            for i, data in enumerate(self.columns):
                line = data.splitlines()[max(0, j - 1)]
                if j == 0:
                    rows[j] += str(i).center(len(line))
                else:
                    rows[j] += line
                if (i + 1) < len(self.columns):
                    rows[j] += ' | '
        return '\n'.join(rows)
```

我们来看看效果：

```python
    >>> columns = ColumnPrinter()
    >>> sim = simulate(grid.height, grid.width)
    >>> for i in range(5):
    ...     columns.append(str(grid))
    ...     grid = live_a_generation(grid, sim)
    ...
    >>> print(columns)  # doctest: +NORMALIZE_WHITESPACE
        0     |     1     |     2     |     3     |     4
    ---*----- | --------- | --------- | --------- | ---------
    ----*---- | --*-*---- | ----*---- | ---*----- | ----*----
    --***---- | ---**---- | --*-*---- | ----**--- | -----*---
    --------- | ---*----- | ---**---- | ---**---- | ---***---
    --------- | --------- | --------- | --------- | ---------
```

上面这套的实现方式，其最大优势在于：开发者能够在不修改game_logic函数的前提下，更新该函数外围的那些代码。
上面这套范例代码，演示了如何用协程来分离程序中的各个关注点，而关注点的分离，正是一条重要的原则。
