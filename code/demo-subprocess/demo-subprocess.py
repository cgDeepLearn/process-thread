# -*- coding: utf8 -*-
"""
用subprocess模块来管理子进程
"""
import os
import time
import subprocess

def func1():
    """
    用Popen构造器来启动进程，然后用communicate方法读取进程的输出信息
    """
    proc = subprocess.Popen(['echo', 'Hello from the child!'],
        stdout=subprocess.PIPE)
    out, err = proc.communicate()
    print(out.decode('utf-8'))

def func2():
    """
    一边定期查询子进程的状态，一边处理其他事物
    """
    proc = subprocess.Popen(['sleep', '0.1'])
    while proc.poll() is None:
        print('Working...')
        # some time-consuming work here
        # print('cacculating')
    print('exit status', proc.poll())

def run_sleep(period):
    proc = subprocess.Popen(['sleep', str(period)])
    return proc

def func3():
    """平行运行多个子进程"""
    start = time.time()
    procs = []
    for _ in range(10):
        proc = run_sleep(0.1)
        procs.append(proc)
    # 通过communicate方法等待子进程完成其I/O工作并终结
    for proc in procs:
        proc.communicate()
    end = time.time()
    print("Finished n %.3f seconds" % (end - start))

def run_openssl(data):
    """利用openssl加密一些数据"""
    env = os.environ.copy()
    env['mypassword'] = r'xe24U\nxd0Q13S\x11'
    proc = subprocess.Popen(
        ['openssl', 'enc', '-des3', '-pass', 'env:mypassword'],
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE)
    proc.stdin.write(data)
    proc.stdin.flush() # 确保子进程获取输入
    return proc

def func4():
    """
    向子进程输送数据，然后获取子进程的输出信息
    """
    # 把一些随机生成的字节数据传给加密函数
    procs = []
    for _ in range(3):
        data = os.urandom(10)
        proc = run_openssl(data)
        procs.append(proc)
    
    for proc in procs:
        
        out, err = proc.communicate()
        # print(out[-10:])
        print(out)

def run_md5(input_stdin):
    """md5加密进程,会用命令行式的md5工具来处理流中的数据
    注：python内置的hashlib模块本身提供了md5函数,本函数只作演示chain用"""


    proc = subprocess.Popen(
        ['python', 'mymd5.py'],
        stdin=input_stdin,
        stdout=subprocess.PIPE,
        encoding='utf-8')


    return proc

def func5():
    """用平行的子进程搭建链条"""
    input_procs = []
    hash_procs = []
    for _ in range(3):
        data = os.urandom(10)
        proc = run_openssl(data)
        input_procs.append(proc)
        hash_proc = run_md5(proc.stdout)
        hash_procs.append(hash_proc)
    
    for proc in input_procs:
        proc.communicate()
    for proc in hash_procs:
        out, err = proc.communicate()
        print(out.strip())

def func6():
    """communicate方法的timeout参数,指定时间没有给出响应则会抛出异常"""
    proc = run_sleep(3)
    try:
        proc.communicate(timeout=0.1)
    except subprocess.TimeoutExpired:
        proc.terminate()
        proc.wait()
    print('Exit status:', proc.poll())

if __name__ == '__main__':
    funcs = [func1, func2, func3, func4, func5, func6]
    for i, func in enumerate(funcs,start=1):
        
        print('-----running func%d:-----' % i)
        func()
        time.sleep(1)
