import os
import struct
import errno
import cv2
import configparser
import argparse
import json
import sys
import time
import random
# import pika
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from python.boundbox import Box
from python.super_frame import SuFrame
from python.deepsort import deepsort_tracker
from python.line_counts import counts
# from python.vehicle_speed import VehicleSpeed
from KyuLength import q_det_class
# from speed_estimate_class_updated3 import speed_estimation


class Analytics(object):
    """Top level of the analytics pipeline

    """

    def __init__(self, pipe_path, line_coordinates_path,
                 camera_intrinsics_file, qlen_conf,
                 segment_path):
        load_start = time.time()
        super(Analytics, self).__init__()
        self.pipe_path = pipe_path
        self.line_coordinates_path = line_coordinates_path
        self.camera_intrinsics_file = camera_intrinsics_file
        self.qlen_conf = qlen_conf
        self.segment_path = segment_path
        # self.connection = pika.BlockingConnection(pika.ConnectionParameters('video.iudx.org.in'))
        parser = configparser.ConfigParser()
        parser.read("../configs/global.cfg")
        with open(self.line_coordinates_path, 'r') as lcp:
            lc = json.loads(lcp.read())
        self.line_coordinates = [lc["point_1"], lc["point_2"]]
        with open(self.camera_intrinsics_file, 'r') as cif:
            self.camera_intrinsics = json.loads(cif.read())
        load_duration = time.time() - load_start
        with open(self.qlen_conf, 'r') as conf_q:
            qlc = json.loads(conf_q.read())
        mask_path = qlc["mask_path"]
        self.imgcoord = qlc["image_array"]
        self.worldcoord = qlc["world_array"]
        self.qscale = qlc["scale"]
        self.mask_img = cv2.imread(mask_path, 0)
        if self.mask_img is None:
            print("got mask image as :", self.mask_img)


    def getboxval(self):
        try:
            os.mkfifo(self.pipe_path)
        except OSError as oe:
            if oe.errno != errno.EEXIST:
                raise
        current_time = time.time()*1000


    def write_status(self, success, logfile):
        fifo_pipe = os.open(self.pipe_path, os.O_WRONLY)
        if success:
            byte_size = os.write(fifo_pipe, b'1')
            logfile.write("Written success at {}\n".format(time.time()*1000))
        elif not success:
            byte_size = os.write(fifo_pipe, b'0')
            logfile.write("Written success at {}\n".format(time.time()*1000))
        else:
            os.close(fifo_pipe)
            sys.exit(0)
        os.close(fifo_pipe)

    def run_analytics(self):
        self.getboxval()
        previous_file = ''
        DeepSort = deepsort_tracker()

        while(True):
            logfile = open("logs/pylogfile_"+self.pipe_path.split("/")[-1]+".log", "a+")
            DeepSort.reset_tracker()
            counter = counts(self.line_coordinates)

            # TODO add queue length initializer when its ready
            # qlen = q_det_class.q_lenner(self.mask_img, self.imgcoord, self.worldcoord, self.qscale)
            #  add camera intrinsics and extract model in vehicle speeds
            # TODO add speed module later
            # speeder = VehicleSpeed(self.camera_intrinsics)
            frame_number = 1
            empty_frame_counter = 0
            current_time = time.time()*1000
            fifo_pipe = os.open(self.pipe_path, os.O_RDONLY)
            lat_file = os.read(fifo_pipe, 28)
            logfile.write("Read file name at {}\n".format(current_time))
            os.close(fifo_pipe)
            logfile.write("lat_file received Python side :: {}\n".format(lat_file))
            lat_file = lat_file.decode("utf-8")

            print("Working on File: {}\r".format(lat_file))
            logfile.write("latest file name: {}\n".format(lat_file))
            lat_file_path = os.path.join("./segments", self.segment_path, lat_file)

            if not os.path.exists(lat_file_path):
                sys.exit()

            self.write_status(True, logfile)
            cap = cv2.VideoCapture(lat_file_path)

            if (not cap.isOpened()):
                continue

            while (1):
                frame_time = time.time()
                ret, frame = cap.read()
                logfile.write("return value ---- {}\n".format(ret))

                if frame is None:
                    logfile.write("Frame is None; for :: {}\n".format(frame_number))
                    empty_frame_counter += 1
                    logfile.write("&&&&&&&&&&&&& FRAME IS NONE BREAK &&&&&&&&&&&&&&&&&&&")
                    break

                if not ret:
                    logfile.write("continuing to next iter as no frame found at: {}\n".format(lat_file_path))
                    break

                current_time = time.time()*1000
                fifo_pipe = os.open(self.pipe_path, os.O_RDONLY)
                head = os.read(fifo_pipe, 1)
                logfile.write("Header read at {}\n".format(current_time))
                os.close(fifo_pipe)
                head = int.from_bytes(head, "big")
                logfile.write("head of frame :: {}\n".format(head))
                logfile.write("FRAME NUMBER == {}\n".format(frame_number))
                frame_number += 1
                if head == 0:
                    self.write_status(True, logfile)
                    continue
                elif ((head < 0) or (head > 99)):
                    self.write_status(False, logfile)
                    logfile.write("&&&&&&&&&&&&&WEIRD HEAD LOOP SYS EXIT FOUND  &&&&&&&&&&&&&&&&&&&")
                    sys.exit()
                self.write_status(True, logfile)

                detections = []

                for i in range(head):
                    current_time = time.time()*1000
                    fifo_pipe = os.open(self.pipe_path, os.O_RDONLY)
                    data_bytes = os.read(fifo_pipe, 24)
                    logfile.write("BBox read at {}\n".format(current_time))
                    os.close(fifo_pipe)
                    logfile.write("BBox byte length {}\n".format(len(data_bytes)))
                    try:
                        data = struct.unpack("=iiiiif", data_bytes)
                    except struct.error as err:
                        logfile.write("ERROR: @@Struct couldnt be unpacked@@")
                        self.write_status(False, logfile)
                        sys.exit(0)

                    logfile.write("bbox data recieved :: {}\n".format(data))
                    if not (0 < data[-1] <= 1):
                        self.write_status(False, logfile)
                        sys.exit(0)
                    self.write_status(True, logfile)

                    detections.append(Box(data))

                sframe = SuFrame(frame)
                sframe.set_dets(detections)
                _ = DeepSort.run_deep_sort(sframe)
                vehicle_counts = counter.get_count(sframe)
                op_dump = os.path.join("results/", self.segment_path, lat_file.split('.')[0]+'.json')
                with open(op_dump, 'a+') as json_file:
                    json.dump(vehicle_counts, json_file)
                frame_duration = time.time() - frame_time
                del(sframe)
            cap.release()
            logfile.close()


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
    agparser.add_argument('--q_length_config', metavar='q',
                          default="configs/qlen_conf/coord.json",
                          type=lambda x: is_valid_file(agparser, x),
                          help='Camera Q length configuration file')
    agparser.add_argument('--segment_path', metavar='g',
                          default="segments/test_cam",
                          type=str,
                          help='The stream name for which the analytics should run')
    args = agparser.parse_args()

    analytics = Analytics(args.pipe_path,
                          args.line_coordinates,
                          args.camera_intrinsics_file,
                          args.q_length_config,
                          args.segment_path)
    analytics.run_analytics()
