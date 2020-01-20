import sys
import os

fifo_pipe = os.open(sys.argv[1], os.O_WRONLY)
byte_size = os.write(fifo_pipe, (1).to_bytes(1, 'big'))
