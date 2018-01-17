# -*- coding: utf-8 -*-
import hashlib
import sys
import io


def md5_func(input_bytes):
    if isinstance(input_bytes, str):
        input_bytes = input_bytes.encode('utf-8')
    print(hashlib.md5(input_bytes).hexdigest())
if __name__ == '__main__':
    line = "123"

    md5_func(line)
