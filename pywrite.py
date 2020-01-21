import sys
import os

def int_to_bytes(x: int) -> bytes:
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')

fifo_pipe = os.open(sys.argv[1], os.O_WRONLY)
byte_size = os.write(fifo_pipe, b'1')
os.close(fifo_pipe)
