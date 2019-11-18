import os
import glob
import struct
import errno
import cv2
import configparser
import argparse
import json
import sys
import time
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from python.boundbox import Box
from python.super_frame import SuFrame
from python.deepsort import deepsort_tracker
from python.line_counts import counts
# from python.vehicle_speed import VehicleSpeed


class Analytics(object):
    """Top level of the analytics pipeline

    """

    def __init__(self, pipe_path, line_coordinates_path, camera_intrinsics_file):
        loading_time = time.time()
        super(Analytics, self).__init__()
        self.pipe_path = pipe_path
        self.line_coordinates_path = line_coordinates_path
        self.camera_intrinsics_file = camera_intrinsics_file
        parser = configparser.SafeConfigParser()
        parser.read(["../configs/global.cfg", "../configs/Global.cfg", "../configs/globals.cfg"])
        with open(self.line_coordinates_path, 'r') as lcp:
            lc = json.loads(lcp.read())
        self.line_coordinates = [lc["point_1"], lc["point_2"]]
        with open(self.camera_intrinsics_file, 'r') as cif:
            self.camera_intrinsics = json.loads(cif.read())
        load_duration = time.time() - loading_time
        print("Analytics init time :", load_duration*1000, "ms")

    def getboxval(self):
        try:
            os.mkfifo(self.pipe_path)
        except OSError as oe:
            if oe.errno != errno.EEXIST:
                raise
        fifo = os.open(self.pipe_path, os.O_RDONLY)
        # TODO add a functionality to close fifo pipe somehow
        return fifo

    def run_analytics(self):
        while(True):
            DeepSort = deepsort_tracker()
            print("finished deepsort tracker init")
            counter = counts(self.line_coordinates)
            #  add camera intrinsics and extract model in vehicle speeds
            # TODO add speed module later
            # speeder = VehicleSpeed(self.camera_intrinsics)
            frame_number = 1
            # latest_video = self.get_video_to_process()
            # self.check_and_delete()
            fifo_pipe = self.getboxval()
            lat_file = os.read(fifo_pipe, 28)
            # print(len(lat_file))
            lat_file = lat_file.decode("utf-8")
            # print(lat_file)
            lat_file_path = os.path.join("./segments/test_cam", lat_file)
            # print(lat_file_path)
            if not os.path.exists(lat_file_path):
                print("The file has dissappeared in python, desynchronized")
                sys.exit(0)
            cap = cv2.VideoCapture(lat_file_path)
            while (cap.isOpened()):
                frame_time = time.time()
                ret, frame = cap.read()
                if not ret:
                    break
                # print("image Size :::", frame.size)

                sframe = SuFrame(frame)

                try:
                    head = os.read(fifo_pipe, 1)
                except IOError:
                    print("didnt get header for frame")
                    continue
                head = int.from_bytes(head, "big")
                frame_number += 1
                if head == 0:
                    continue

                detections = []

                for i in range(head):
                    data_bytes = os.read(fifo_pipe, 24)
                    data = struct.unpack("=iiiiif", data_bytes)
                    detections.append(Box(data))
                sframe.set_dets(detections)
                # yolo is done above
                # deepsort
                trackers = DeepSort.run_deep_sort(sframe)
                # print("trackers::", trackers)
                vehicle_counts = counter.get_count(sframe)
                # TODO add speeds module later
                # vehicle_speeds = speeder.get_speed(sframe)

                print("VC::", vehicle_counts)
                # print("VS::", vehicle_speeds)
                frame_duration = time.time() - frame_time
                print("Per frame counting time is :", frame_duration*1000, "ms")
            cap.release()


def is_valid_file(agparser, ags):
    if not os.path.exists(ags):
        agparser.error("The file %s does not exist!" % ags)
    else:
        return ags


if __name__ == "__main__":
    agparser = argparse.ArgumentParser(description='Visual Traffic \
               Surveillance and Analytics System')
    agparser.add_argument('pipe_path', metavar='p', default="/tmp/fifopipe",
                          type=str,
                          help='Location of the pipe buffer (default:/tmp/fifopipe)')
    agparser.add_argument('--line_coordinates', metavar='l',
                          default="configs/line_coord/test_cam.json",
                          type=lambda x: is_valid_file(agparser, x),
                          help='Path to the line points json file for the \
                          correesponding stream')
    agparser.add_argument('--camera_intrinsics_file', metavar='i',
                          default="configs/cam_intrinsic/test_cam.json",
                          type=lambda x: is_valid_file(agparser, x),
                          help='Camera intrinsics file path')
    args = agparser.parse_args()

    analytics = Analytics(args.pipe_path,
                          args.line_coordinates,
                          args.camera_intrinsics_file)
    analytics.run_analytics()
