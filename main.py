import os
import sys
import struct
import subprocess
from multiprocessing import Process
import errno
import cv2
from python.boundbox import Box, wrap_box


def setBbox():
    cmd = "/home/rbccps2080ti/projects/TensorRT-Yolov3/build/runYolov3"
    subprocess.Popen(cmd)


def getBbox():

    path = "/tmp/fifopipe"

    try:
        os.mkfifo(path)
    except OSError as oe:
        if oe.errno != errno.EEXIST:
            raise

    fifo = os.open(path, os.O_RDONLY)
    frame_number = 1

    while(True):
        videocap = cv2.VideoCapture("latest.mp4")
        if (videocap.isOpened() == False):
            print("python side ::::::::: Error opening video stream or file")
        out = cv2.VideoWriter('outpy.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 20, (1280, 720))

        while(videocap.isOpened()):
            ret, frame = videocap.read()
            if ret == False:
                break

            try:
                head = os.read(fifo, 1)
                print("python side ::::::::: value of head in try :: ", head)
                # head = sys.stdin.read(1)
            except:
                print("python side ::::::::: some error :: end??")
                sys.exit(0)

            head = int.from_bytes(head, "big")
            print("python side ::::::::: header length(number of boxes): ", head)
            print("python side ::::::::: frame_number :::::::::::::: ", frame_number)
            frame_number += 1
            if head == 0:
                print("python side ::::::::: data :::::::::::::: DATA IS EMPTY")
                continue

            for i in range(head):
                data_byte = os.read(fifo, 24)
                print("python side :::::::::::: data_byte value :::::: ", data_byte)
                print("python side :::::::::::: data_byte value :::::: ",
                      len(data_byte))
                data = struct.unpack("=iiiiif", data_byte)

                print("python side ::::::::: data :::::::::::::: ", data)
                data = Box(data)
                frame = wrap_box(frame, data)
            out.write(frame)
        videocap.release()
        out.release()


if __name__ == "__main__":

    p1 = Process(target=setBbox)
    p2 = Process(target=getBbox)

    p1.start()
    p2.start()

    p1.join()
    p2.join()
