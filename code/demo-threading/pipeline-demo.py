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