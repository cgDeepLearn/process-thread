# subprocess

subprocess模块是python从2.4版本开始引入的模块。主要用来取代 一些旧的模块方法，如os.system、os.spawn、os.popen、commands等。subprocess通过子进程来执行外部指令，并通过input/output/error管道，获取子进程的执行的返回信息。

## 常用方法

### subprocess.call()

执行命令，并返回执行状态，其中shell参数为False时，命令需要通过列表的方式传入，当shell为True时，可直接传入命令

```python
>>> import subprocess
>>> child = subprocess.call(['df', '-h'], shell=False)
Filesystem      Size  Used Avail Use% Mounted on
udev            475M     0  475M   0% /dev
tmpfs            99M  2.9M   97M   3% /run
/dev/vda1        40G  9.5G   28G  26% /
tmpfs           495M  4.0K  495M   1% /dev/shm
tmpfs           5.0M  4.0K  5.0M   1% /run/lock
tmpfs           495M     0  495M   0% /sys/fs/cgroup
tmpfs            99M     0   99M   0% /run/user/1000

>>> child2 = subprocess.call('df -h', shell=True)
Filesystem      Size  Used Avail Use% Mounted on
udev            475M     0  475M   0% /dev
tmpfs            99M  2.9M   97M   3% /run
/dev/vda1        40G  9.5G   28G  26% /
tmpfs           495M  4.0K  495M   1% /dev/shm
tmpfs           5.0M  4.0K  5.0M   1% /run/lock
tmpfs           495M     0  495M   0% /sys/fs/cgroup
tmpfs            99M     0   99M   0% /run/user/1000
```

### subprocess.check_call()

用法与subprocess.call()类似，区别是，当返回值不为0时，直接抛出异常

```python
>>> child3 = subprocess.check_call('df -h', shell=True)
Filesystem      Size  Used Avail Use% Mounted on
udev            475M     0  475M   0% /dev
tmpfs            99M  2.9M   97M   3% /run
/dev/vda1        40G  9.5G   28G  26% /
tmpfs           495M  4.0K  495M   1% /dev/shm
tmpfs           5.0M  4.0K  5.0M   1% /run/lock
tmpfs           495M     0  495M   0% /sys/fs/cgroup
tmpfs            99M     0   99M   0% /run/user/1000
>>> print(child3)
0
>>> child4 = subprocess.check_call('df-h', shell=True)
/bin/sh: 1: df-h: not found
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/cg/anaconda3/lib/python3.6/subprocess.py", line 291, in check_call
    raise CalledProcessError(retcode, cmd)
subprocess.CalledProcessError: Command 'df-h' returned non-zero exit status 127.
```

### subprocess.check_output()

用法与上面两个方法类似，区别是，如果当返回值为0时，不直接输出结果，如果返回值不为0，直接抛出异常。需要说明的是，该方法在python3.x中才有。

```python
>>> child5 = subprocess.check_output('df -h', shell=True)
>>> child5
b'Filesystem      Size  Used Avail Use% Mounted on\nudev            475M     0  475M   0% /dev\ntmpfs            99M  2.9M   97M   3% /run\n/dev/vda1        40G  9.5G   28G  26% /\ntmpfs           495M  4.0K  495M   1% /dev/shm\ntmpfs           5.0M  4.0K  5.0M   1% /run/lock\ntmpfs           495M     0  495M   0% /sys/fs/cgroup\ntmpfs            99M     0   99M   0% /run/user/1000\n'
```

### subprocess.Popen()

在一些复杂场景中，我们需要将一个进程的执行输出作为另一个进程的输入。在另一些场景中，我们需要先进入到某个输入环境，然后再执行一系列的指令等。这个时候我们就需要使用到suprocess的Popen()方法。该方法有以下参数：

* args：shell命令，可以是字符串，或者序列类型，如list,tuple。
* bufsize：缓冲区大小，可不用关心
* stdin,stdout,stderr：分别表示程序的标准输入，标准输出及标准错误
* shell：与上面方法中用法相同
* cwd：用于设置子进程的当前目录
* env：用于指定子进程的环境变量。如果env=None，则默认从父进程继承环境变量
* universal_newlines：不同系统的的换行符不同，当该参数设定为true时，则表示使用\n作为换行符

示例1：在~/test下创建一个suprocesstest的目录， 以及删除：

```python
>>> child6 = subprocess.Popen('mkdir subprocesstest',shell=True,cwd='/home/cg/test')
# 查看目录，已经创建该文件夹
>>> child7 = subprocess.Popen('rmdir subprocesstest',shell=True,cwd='/home/cg/test')
# 查看目录，已经删除该文件夹
```

示例2: 使用python执行几个命令

```python
import subprocess

proc = subprocess.Popen(["python"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

proc.stdin.write('print(1)\n'.encode('utf-8'))
proc.stdin.write('print(2)\n'.encode('utf-8'))
proc.stdin.write('print(3)\n'.encode('utf-8'))
proc.stdin.close()

cmd_out = proc.stdout.read()
proc.stdout.close()
cmd_error = proc.stderr.read()
proc.stderr.close()

print(cmd_out)
print(cmd_error)
```

output:

```python
b'1\n2\n3\n'
b''
```

或者使用communicate()方法：

```python
import subprocess

proc = subprocess.Popen(["python"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

proc.stdin.write('print(1)\n'.encode('utf-8'))
proc.stdin.write('print(2)\n'.encode('utf-8'))
proc.stdin.write('print(3)\n'.encode('utf-8'))

out_err_list = proc.communicate()
print(out_err_list)

```

output:

```python
(b'1\n2\n3\n', b'') #(out,err)元组
```

示例3: 将一个子进程的输出，作为另一个子进程的输入

```python
# 类似于shell的cat /etc/passwd | grep 0:0
import subprocess
child1 = subprocess.Popen(["cat","/etc/passwd"], stdout=subprocess.PIPE)
child2 = subprocess.Popen(["grep","0:0"],stdin=child1.stdout, stdout=subprocess.PIPE)
out = child2.communicate()
```

其他方法：

```python
import subprocess
child = subprocess.Popen('sleep 60',shell=True,stdout=subprocess.PIPE)
child.poll()    #检查子进程状态
child.kill()     #终止子进程
child.send_signal()    #向子进程发送信号
child.terminate()   #终止子进程
```

