import os
import glob
import struct
import errno
import cv2
import configparser
import argparse
import json

from python.boundbox import Box
from python.super_frame import SuFrame
from python.deepsort import deepsort_tracker
from python.line_counts import counts
from python.vehicle_speed import VehicleSpeed


class Analytics(object):
    """Top level of the analytics pipeline

    """

    def __init__(self, segment_source, pipe_path, line_coordinates_path, camera_intrinsics):
        super(Analytics, self).__init__()
        self.segment_source = segment_source
        self.pipe_path = pipe_path
        self.line_coordinates_path = line_coordinates_path
        self.camera_intrinsics = camera_intrinsics
        parser = configparser.SafeConfigParser()
        parser.read(["../configs/global.cfg", "../configs/Global.cfg", "../configs/globals.cfg"])
        with open(self.line_coordinates_path, 'r') as lcp:
            lc = json.loads(lcp)
        self.line_coordinates = [lc["point_1"], lc["point_2"]]


    def get_latest(self, segment_path):
        list_of_files = glob.glob(os.path.join(segment_path, "*.flv"))
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

    def run_analytics(self):
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
                print("trackers::", trackers)
                vehicle_counts = counter.get_count(sframe)
                vehicle_speeds = speeder.get_speed(sframe)

                print("VC::", vehicle_counts)
                print("VS::", vehicle_speeds)
            cap.release()

            
def is_valid_file(agparser, ags):
    if not os.path.exists(ags):
        agparser.error("The file %s does not exist!" % ags)
    else:
        return ags


if __name__ == "__main__":
    agparser = argparse.ArgumentParser(description='Visual Traffic \
               Surveillance and Analytics System')
    agparser.add_argument('segment_source', metavar='S',
                          type=lambda x: is_valid_file(agparser, x),
                          help='Source for video files from the rtsp stream')
    agparser.add_argument('--pipe_path', metavar='p', default="/tmp/fifopipe",
                          type=lambda x: is_valid_file(agparser, x),
                          help='Location of the pipe buffer (default:/tmp/fifopipe)')
    agparser.add_argument('--line_coordinates', metavar='l',
                          type=lambda x: is_valid_file(agparser, x),
                          help='Path to the line points json file for the \
                          correesponding stream')
    agparser.add_argument('--camera_intrinsics', metavar='i',
                          type=lambda x: is_valid_file(agparser, x),
                          help='Camera intrinsics')
    args = agparser.parse_args()

    analytics = Analytics(args.segment_source, args.pipe_path, args.line_coordinates, args.camera_intrinsics)
    analytics.run_analytics()
