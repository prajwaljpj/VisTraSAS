import os
import glob
import sys
import struct
import errno
import cv2
from python.boundbox import Box
from python.super_frame import SuFrame
from python.deepsort import deepsort_tracker
from python.line_counts import counts
from python.vehicle_speed import VehicleSpeed
import configparser

class Analytics(object):
    """Top level of the analytics pipeline

    """
    def __init__(self, segment_source, pipe_path, line_coordinates, camera_intrinsics):
        super(Analytics, self).__init__()
        self.segment_source = segment_source
        self.pipe_path = pipe_path
        self.line_coordinates = line_coordinates
        self.camera_intrinsics = camera_intrinsics
        
        parser = configparser.SafeConfigParser()
        parser.read(["../configs/global.cfg", "../configs/Global.cfg", "../configs/globals.cfg"])

    def get_latest(self, segment_path):
        list_of_files = glob.glob(os.path.join(segment_path, "*.flv")) # * means all if need specific format then *.csv
        latest_file = max(list_of_files, key=os.path.getctime)
        return latest_file

    def get_video_to_process(self):
        if not os.path.exists(self.segment_source):
            os.mkdir(self.segment_source)
        list_of_files = glob.glob(os.path.join(self.segment_source, "*.flv"))
        sorted_list = sorted(list_of_files, key=os.path.getmtime)
        if len(sorted_list) != 0:
            latest_file = sorted_list[-1]
            return latest_file
        return []

    def check_and_delete(self):
        list_of_files = glob.glob(os.path.join(self.segment_source, "*.flv"))
        if len(list_of_files) > 10:
            sorted_list = sorted(list_of_files, key=os.path.getmtime)
            for segfile in sorted_list[:len(sorted_list)-2]:
                os.remove(segfile)

    def getboxval(self):
        try:
            os.mkfifo(self.pipe_path)
        except OSError as oe:
            if oe.errno != errno.EEXIST:
                raise
        fifo = os.open(self.pipe_path, os.O_RDONLY)
        # TODO add a functionality to close fifo pipe somehow
        return fifo

    def run_analytics(self, fifo):
        while(True):
            DeepSort = deepsort_tracker()
            counter = counts(self.line_coordinates)
            # TODO add camera intrinsics and extract model in vehicle speeds
            speeder = VehicleSpeed()
            frame_number = 1
            latest_video = self.get_video_to_process()
            self.check_and_delete()
            fifo_pipe = self.getboxval()
            cap = cv2.VideoCapture(latest_video)
            while (cap.isOpened()):
                ret, frame = cap.read()
                if not ret:
                    break

                sframe = SuFrame(frame)

                try:
                    head = os.read(fifo, 1)
                except:
                    print("didnt get header for frame")
                    continue
                head = int.from_bytes(head, "big")
                frame_number += 1
                if head == 0:
                    continue

                detections = []

                for i in range(head):
                    data_bytes = os.read(fifo, 24)
                    data = struct.unpack("=iiiiif", data_bytes)
                    detections.append(Box(data))
                sframe.set_dets(detections)
                # yolo is done above
                # deepsort
                trackers = DeepSort.run_deep_sort(sframe)
                vehicle_counts = counter.get_count(sframe)
                vehicle_speeds = speeder.get_speed(sframe)

                print("VC::", vehicle_counts)
                print("VS", vehicle_speeds)




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
    getBbox()
