---

---
# 考虑用concurrent.futures来处理并发和实现真正的平行计算

## 导读

编写Python程序时,我们可以利用CPU的多核心通过平行计算来提升计算任务的速度。很遗憾，Python的全局解释器(`GIL`)的存在使得我们没有办法用`线程`实现真正的平行计算。

为了实现平行计算，我们可以考虑用C语言扩展或者使用诸如`Cython`和`Numba`等开源工具迁移到C语言。但是这样做大幅增加了测试量和风险。于是我们思考一下：有没有一种更好的方式，只需使用少量的Python代码，即可有效提升执行效率，并迅速解决复杂的计算问题。

我们可以试着通过内置的`concurrent.futures`模块来利用内置的`multiprocessing`模块实现这种需求。这样的做法会以子进程的形式，平行运行多个解释器，从而利用多核心CPU来提升执行速度(子进程与主解释器相分离，所以它们的全局解释器锁也是相互独立的)。
<!--more-->
我们可以通过下面的例子来看一下效果。

## 计算两数最大公约数

现在给出一个列表，列表里每个元素是一对数，求出每对数的最大公约数

```python
numbers = [(1963309, 2265973), (2030677, 3814172),
            (1551645, 2229620), (2039045, 2020802)]
```

### 没有做平行计算的版本

```python 求最大公约数

def gcd(pair):
    a, b = pair
    low = min(a, b)
    for i in range(low, 0, -1):
        if a % i == 0 and b % i == 0:
            return i
```

我们用map来试运行一下:

```python
import time
start = time.time()
results = list(map(gcd, numbers))
end = time.time()
print('Took %.3f seconds' % (end - start))
>>>
Took 0.530 seconds
```

下面我们用conccurrent.futures来模拟多线程和多进程

### 使用`concurretn.futures`的`ThreadPoolExecutor`

```python 使用ThreadPoolExecutor多线程
from concurrent.futures import ThreadPoolExecutor
start = time.time()
pool = ThreadPoolExecutor(max_workers=2) # cpu核心数目个工作线程 
results = list(pool.map(gcd, numbers))
end = time.time()
print('Took %.3f seconds' % (end - start))
>>>
Took 0.535 seconds
```
两个线程用了和上面差不多的时间，而且比上面还慢一些，说明多线程并不能平行计算，而且开线程也有耗费。

### 使用`concurrent.futures`的`ProcessPoollExecutor`

```python 将ThreadPoolExecutor换成ProcessPoolExecutor
from concurrent.futures import ProcessPoolExecutor
start = time.time()
pool = ProcessPoolExecutor(max_workers=2) # cpu核心数目个工作进程 
results = list(pool.map(gcd, numbers))
end = time.time()
print('Took %.3f seconds' % (end - start))
>>> 
Took 0.287 seconds
```

在双核电脑上运行上面程序发现比之前两个版本运行快很多。这是因为`ProcessPoolExecutor`会利用`multiprocessing`模块所提供的的底层机制来逐步完成下列操作：

1. 把numbers列表中的每一项输入数据都传给map
2. 用pickle模块对数据进行序列化，将其变成二进制形式。
3. 通过本地套接字socket将序列化后的数据从主解释器所在的进程发送到子解释器所在的进程。
4. 接下来在子进程中，用pickle对二进制数据进行反序列化操作,将其还原为Python对象
5. 引入包含gcd函数的那个Python模块
6. 各条子进程平行地针对各自的输入数据，来运行gcd函数
7. 对运行结果进行序列化操作，将其变为字节
8. 将这些字节通过socket复制到主进程中
9. 主进程对这些字节执行反序列化操作，将其还原为Python对象。
10. 最后，把每条子进程所求出的计算结果合并到一份列表中，返回给调用者

### 编后语

为了实现平行计算，`multiprocessing`模块和`ProcessPoolExecutor`类在幕后做了大量的工作。如果改用其他的语言来写，那么开发者只需一把同步锁或一项原子操作，就可以把线程之间的通信过程协调好。而在Python中，我们却必须使用开销较高的`multiprocessing`模块,其开销之所以大，原因就在于主进程与子进程之间，必须进行序列化和反序列化操作，这些是导致大量开销的来源。

对于某些较为孤立，且数据利用率高的任务来说，上述方案非常适合。如果执行的运算不符合上述特征，那么`multiprocessing`所产生的的开销可能并不能使程序加速。在这种情况下，可以求助multiprocessing所提供的的一些高级机制，如内存共享(`shared memory`)、跨进程锁定(`cross-process lock`)、队列(`queue`)和代理(`proxy`)等。


## 下载进度条显示

用`concurrent.futures`的`ThreadPoolExecutor`类处理对于大量I/O操作的并发任务的示例。非常值得参考的实现。

flags_common.py是一些默认参数和函数接口以及argparse。
flags_sequential.py是单线程依序下载以及进度条显示实现。
flags_threadpool.py是利用concurrent.futures的多线程操作实现。

- flags_common.py

```python flags_common.py
"""Utilities for second set of flag examples.
"""

import os
import time
import sys
import string
import argparse
from collections import namedtuple
from enum import Enum


Result = namedtuple('Result', 'status data')

HTTPStatus = Enum('Status', 'ok not_found error')

POP20_CC = ('CN IN US ID BR PK NG BD RU JP '
            'MX PH VN ET EG DE IR TR CD FR').split()

DEFAULT_CONCUR_REQ = 1
MAX_CONCUR_REQ = 1

SERVERS = {
    'REMOTE': 'http://flupy.org/data/flags',
    'LOCAL':  'http://localhost:8001/flags',
    'DELAY':  'http://localhost:8002/flags',
    'ERROR':  'http://localhost:8003/flags',
}
DEFAULT_SERVER = 'LOCAL'

DEST_DIR = 'downloads/'
COUNTRY_CODES_FILE = 'country_codes.txt'


def save_flag(img, filename):
    path = os.path.join(DEST_DIR, filename)
    with open(path, 'wb') as fp:
        fp.write(img)


def initial_report(cc_list, actual_req, server_label):
    if len(cc_list) <= 10:
        cc_msg = ', '.join(cc_list)
    else:
        cc_msg = 'from {} to {}'.format(cc_list[0], cc_list[-1])
    print('{} site: {}'.format(server_label, SERVERS[server_label]))
    msg = 'Searching for {} flag{}: {}'
    plural = 's' if len(cc_list) != 1 else ''
    print(msg.format(len(cc_list), plural, cc_msg))
    plural = 's' if actual_req != 1 else ''
    msg = '{} concurrent connection{} will be used.'
    print(msg.format(actual_req, plural))


def final_report(cc_list, counter, start_time):
    elapsed = time.time() - start_time
    print('-' * 20)
    msg = '{} flag{} downloaded.'
    plural = 's' if counter[HTTPStatus.ok] != 1 else ''
    print(msg.format(counter[HTTPStatus.ok], plural))
    if counter[HTTPStatus.not_found]:
        print(counter[HTTPStatus.not_found], 'not found.')
    if counter[HTTPStatus.error]:
        plural = 's' if counter[HTTPStatus.error] != 1 else ''
        print('{} error{}.'.format(counter[HTTPStatus.error], plural))
    print('Elapsed time: {:.2f}s'.format(elapsed))


def expand_cc_args(every_cc, all_cc, cc_args, limit):
    codes = set()
    A_Z = string.ascii_uppercase
    if every_cc:
        codes.update(a+b for a in A_Z for b in A_Z)
    elif all_cc:
        with open(COUNTRY_CODES_FILE) as fp:
            text = fp.read()
        codes.update(text.split())
    else:
        for cc in (c.upper() for c in cc_args):
            if len(cc) == 1 and cc in A_Z:
                codes.update(cc+c for c in A_Z)
            elif len(cc) == 2 and all(c in A_Z for c in cc):
                codes.add(cc)
            else:
                msg = 'each CC argument must be A to Z or AA to ZZ.'
                raise ValueError('*** Usage error: '+msg)
    return sorted(codes)[:limit]


def process_args(default_concur_req):
    server_options = ', '.join(sorted(SERVERS))
    parser = argparse.ArgumentParser(
                description='Download flags for country codes. '
                'Default: top 20 countries by population.')
    parser.add_argument('cc', metavar='CC', nargs='*',
                help='country code or 1st letter (eg. B for BA...BZ)')
    parser.add_argument('-a', '--all', action='store_true',
                help='get all available flags (AD to ZW)')
    parser.add_argument('-e', '--every', action='store_true',
                help='get flags for every possible code (AA...ZZ)')
    parser.add_argument('-l', '--limit', metavar='N', type=int,
                help='limit to N first codes', default=sys.maxsize)
    parser.add_argument('-m', '--max_req', metavar='CONCURRENT', type=int,
                default=default_concur_req,
                help='maximum concurrent requests (default={})'
                      .format(default_concur_req))
    parser.add_argument('-s', '--server', metavar='LABEL',
                default=DEFAULT_SERVER,
                help='Server to hit; one of {} (default={})'
                      .format(server_options, DEFAULT_SERVER))
    parser.add_argument('-v', '--verbose', action='store_true',
                help='output detailed progress info')
    args = parser.parse_args()
    if args.max_req < 1:
        print('*** Usage error: --max_req CONCURRENT must be >= 1')
        parser.print_usage()
        sys.exit(1)
    if args.limit < 1:
        print('*** Usage error: --limit N must be >= 1')
        parser.print_usage()
        sys.exit(1)
    args.server = args.server.upper()
    if args.server not in SERVERS:
        print('*** Usage error: --server LABEL must be one of',
              server_options)
        parser.print_usage()
        sys.exit(1)
    try:
        cc_list = expand_cc_args(args.every, args.all, args.cc, args.limit)
    except ValueError as exc:
        print(exc.args[0])
        parser.print_usage()
        sys.exit(1)

    if not cc_list:
        cc_list = sorted(POP20_CC)
    return args, cc_list


def main(download_many, default_concur_req, max_concur_req):
    args, cc_list = process_args(default_concur_req)
    actual_req = min(args.max_req, max_concur_req, len(cc_list))
    initial_report(cc_list, actual_req, args.server)
    base_url = SERVERS[args.server]
    t0 = time.time()
    counter = download_many(cc_list, base_url, args.verbose, actual_req)
    assert sum(counter.values()) == len(cc_list), \
        'some downloads are unaccounted for'
    final_report(cc_list, counter, t0)
```

- falgs_sequential.py

```python flags_sequential.py
"""Download flags of countries (with error handling).

Sequential version

Sample run::

    $ python3 flags_sequential.py -s DELAY b
    DELAY site: http://localhost:8002/flags
    Searching for 26 flags: from BA to BZ
    1 concurrent connection will be used.
    --------------------
    17 flags downloaded.
    9 not found.
    Elapsed time: 13.36s

"""

import collections

import requests
import tqdm

from flags_common import main, save_flag, HTTPStatus, Result


DEFAULT_CONCUR_REQ = 1
MAX_CONCUR_REQ = 1

# BEGIN FLAGS2_BASIC_HTTP_FUNCTIONS
def get_flag(base_url, cc):
    url = '{}/{cc}/{cc}.gif'.format(base_url, cc=cc.lower())
    resp = requests.get(url)
    if resp.status_code != 200:  # <1>
        resp.raise_for_status()
    return resp.content


def download_one(cc, base_url, verbose=False):
    try:
        image = get_flag(base_url, cc)
    except requests.exceptions.HTTPError as exc:  # <2>
        res = exc.response
        if res.status_code == 404:
            status = HTTPStatus.not_found  # <3>
            msg = 'not found'
        else:  # <4>
            raise
    else:
        save_flag(image, cc.lower() + '.gif')
        status = HTTPStatus.ok
        msg = 'OK'

    if verbose:  # <5>
        print(cc, msg)

    return Result(status, cc)  # <6>
# END FLAGS2_BASIC_HTTP_FUNCTIONS

# BEGIN FLAGS2_DOWNLOAD_MANY_SEQUENTIAL
def download_many(cc_list, base_url, verbose, max_req):
    counter = collections.Counter()  # <1>
    cc_iter = sorted(cc_list)  # <2>
    if not verbose:
        cc_iter = tqdm.tqdm(cc_iter)  # <3>
    for cc in cc_iter:  # <4>
        try:
            res = download_one(cc, base_url, verbose)  # <5>
        except requests.exceptions.HTTPError as exc:  # <6>
            error_msg = 'HTTP error {res.status_code} - {res.reason}'
            error_msg = error_msg.format(res=exc.response)
        except requests.exceptions.ConnectionError as exc:  # <7>
            error_msg = 'Connection error'
        else:  # <8>
            error_msg = ''
            status = res.status

        if error_msg:
            status = HTTPStatus.error  # <9>
        counter[status] += 1  # <10>
        if verbose and error_msg: # <11>
            print('*** Error for {}: {}'.format(cc, error_msg))

    return counter  # <12>
# END FLAGS2_DOWNLOAD_MANY_SEQUENTIAL

if __name__ == '__main__':
    main(download_many, DEFAULT_CONCUR_REQ, MAX_CONCUR_REQ)
```

- flags_threadpool.py

```python flags_threadpool.py
"""Download flags of countries (with error handling).

ThreadPool version

Sample run::

    $ python3 flags_threadpool.py -s REMOTE -e
    ERROR site: http://localhost:8003/flags
    Searching for 676 flags: from AA to ZZ
    30 concurrent connections will be used.
    --------------------
    150 flags downloaded.
    361 not found.
    165 errors.
    Elapsed time: 7.46s

"""

# BEGIN FLAGS2_THREADPOOL
import collections
from concurrent import futures

import requests
import tqdm  # <1>

from flags_common import main, HTTPStatus  # <2>
from flags_sequential import download_one  # <3>

DEFAULT_CONCUR_REQ = 30  # <4>
MAX_CONCUR_REQ = 1000  # <5>


def download_many(cc_list, base_url, verbose, concur_req):
    counter = collections.Counter()
    with futures.ThreadPoolExecutor(max_workers=concur_req) as executor:  # <6>
        to_do_map = {}  # <7>
        for cc in sorted(cc_list):  # <8>
            future = executor.submit(download_one,
                            cc, base_url, verbose)  # <9>
            to_do_map[future] = cc  # <10>
        done_iter = futures.as_completed(to_do_map)  # <11>
        if not verbose:
            done_iter = tqdm.tqdm(done_iter, total=len(cc_list))  # <12>
        for future in done_iter:  # <13>
            try:
                res = future.result()  # <14>
            except requests.exceptions.HTTPError as exc:  # <15>
                error_msg = 'HTTP {res.status_code} - {res.reason}'
                error_msg = error_msg.format(res=exc.response)
            except requests.exceptions.ConnectionError as exc:
                error_msg = 'Connection error'
            else:
                error_msg = ''
                status = res.status

            if error_msg:
                status = HTTPStatus.error
            counter[status] += 1
            if verbose and error_msg:
                cc = to_do_map[future]  # <16>
                print('*** Error for {}: {}'.format(cc, error_msg))

    return counter


if __name__ == '__main__':
    main(download_many, DEFAULT_CONCUR_REQ, MAX_CONCUR_REQ)
# END FLAGS2_THREADPOOL
```
