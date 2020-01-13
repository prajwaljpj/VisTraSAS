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
        print("Time taken for Init side of python : ", load_duration*1000, "ms")
        # Q length part
        with open(self.qlen_conf, 'r') as conf_q:
            qlc = json.loads(conf_q.read())
        mask_path = qlc["mask_path"]
        self.imgcoord = qlc["image_array"]
        self.worldcoord = qlc["world_array"]
        self.qscale = qlc["scale"]
        self.mask_img = cv2.imread(mask_path, 0)
        if self.mask_img is None:
            print("got mask image as :", self.mask_img)
            #sys.exit(0)
        # speed part
        # self.speeder = speed_estimation()


    def getboxval(self):
        try:
            os.mkfifo(self.pipe_path)
        except OSError as oe:
            if oe.errno != errno.EEXIST:
                raise
        fifo = os.open(self.pipe_path, os.O_RDONLY)
        print("Pipe opened::::::::")
        # TODO add a functionality to close fifo pipe somehow
        return fifo


    def run_analytics(self):
        fifo_pipe = self.getboxval()
        previous_file = ''
        logfile = open("logfile_py.log", "a+")
        while(True):
            print("inside run_analytics")

            try:
                lat_file = os.read(fifo_pipe, 28)
                print("lat_file received Python side",lat_file)
                logfile.write("lat_file received Python side :: {}\n".format(lat_file))
                lat_file = lat_file.decode("utf-8")

            except IOError:
                print("didn't get latest file")
                continue

            print("latest file name: {}".format(lat_file))
            logfile.write("latest file name: {}\n".format(lat_file))
            lat_file_path = os.path.join("./segments", self.segment_path, lat_file)

            if not os.path.exists(lat_file_path):
                print("The file has dissappeared in python, desynchronized:: the file im looking for is ::", lat_file_path)
                sys.exit(0)
            cap = cv2.VideoCapture(lat_file_path)

            while (cap.isOpened()):
                frame_time = time.time()
                ret, frame = cap.read()

                if not ret:
                    print("continuing to next iter as no frame found at:", lat_file_path)
                    logfile.write("continuing to next iter as no frame found at: {}\n".format(lat_file_path))
                    break

                try:
                    head = os.read(fifo_pipe, 1)
                    #print("pipe read::::::::::::::::")
                except IOError:
                    print("didnt get HEADER for frame")
                    continue
                head = int.from_bytes(head, "big")
                logfile.write("head of frame :: {}\n".format(head))
                # frame_number += 1

                if head == 0:
                    continue


                for i in range(head):
                    try:
                        data_bytes = os.read(fifo_pipe, 24)
                        data = struct.unpack("=iiiiif", data_bytes)
                        #print("struct unpacked ::::::::::")
                    except struct.error as err:
                        print("Check: ",err)
                    logfile.write("bbox data recieved :: {}\n".format(data))
                    if (data[0] < 0 or data[0] > 9):
                        new_data = (random.randint(1,8), data[1], data[2], data[3], data[4], data[5])
                    else:
                        new_data = data
                # op_dump = os.path.join("results/", self.segment_path, lat_file.split('.')[0]+'.json')
                # with open(op_dump, 'a+') as json_file:
                #     json.dump(vehicle_counts, json_file)
            logfile.write("\n\n\n+++I finished a file\n\n\n")
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
