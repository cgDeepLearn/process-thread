import time
import sys
import random

ii = 1
while ii < 10:
    delay = random.randint(0,100)/100.0 #1秒内的随机时间
    sys.stdout.write("Talking every %s seconds, blabbed %i times\n" % (delay, ii))
    #如果没有flush 后面的程序无法读取的
    sys.stdout.flush()
    ii += 1
    time.sleep(delay)
