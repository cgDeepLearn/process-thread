from subprocess import Popen, PIPE
from os import kill
import signal
import time


talkpipe = Popen(['python', 'echo.py'],
    shell=False, stdout=PIPE)
try:
    while True:
        line = talkpipe.stdout.readline()
        if line:
            print("SERVER HEARD", line.strip())
        else:
            print("no data")
        time.sleep(2)

except KeyboardInterrupt:
    print("Killing child...")
    kill(talkpipe.pid, signal.SIGTERM)