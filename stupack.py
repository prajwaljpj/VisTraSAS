import struct
import sys

try:
    pipe_data = sys.stdin.buffer.read(24)
    # print(pipe_data)
    data = struct.unpack("=iiiiif", pipe_data)
    sys.stdout.write(str(data)+'\n')
except struct.error as err:
    print("Check: ",err)
    print("ERROR: @@Struct couldnt be unpacked@@")
