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
        print("Pipe opened::::::::")
        current_time = time.time()*1000
        print("Time for pipe check at {}\n".format(current_time))
        # logfile.write("Time for pipe check at {}\n".format(current_time)) 
        # fifo = os.open(self.pipe_path, os.O_RDONLY)
        # TODO add a functionality to close fifo pipe somehow
        # return fifo

    # def read_from_pipe(self, byte_len=1):
        # print(self.pipe_path)
        # popened = os.open(self.pipe_path, os.O_RDONLY)
        # pdat = os.read(popened, byte_len)
#        popened.close()
        # os.close(popened)
        # return pdat
        #
    # TODO add logfile as a class object
    def write_status(self, success, logfile):
        fifo_pipe = os.open(self.pipe_path, os.O_WRONLY)
        if success:
            byte_size = os.write(fifo_pipe, b'1')
            print("Written success at {}\n".format(time.time()*1000))
            logfile.write("Written success at {}\n".format(time.time()*1000))
        elif not success:
            byte_size = os.write(fifo_pipe, b'0')
            print("Written success at {}\n".format(time.time()*1000))
            logfile.write("Written success at {}\n".format(time.time()*1000))
        else:
            print("PYTHON LOG ## exited in write_status")
            os.close(fifo_pipe)
            sys.exit(0)
        os.close(fifo_pipe)

    def run_analytics(self):
        # counter = counts(self.line_coordinates)
        # fifo_pipe = self.getboxval()
        logfile = open("logs/pylogfile_"+self.pipe_path.split("/")[-1]+".log", "w+")
        self.getboxval()
        # fifo_pipe = os.open(self.pipe_path, os.O_RDONLY)
        previous_file = ''
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~ ENTERING MAIN LOOP ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        while(True):
            print("inside run_analytics")
            DeepSort = deepsort_tracker()

            # print("finished deepsort tracker init")
            counter = counts(self.line_coordinates)

            # TODO add queue length initializer when its ready
            # qlen = q_det_class.q_lenner(self.mask_img, self.imgcoord, self.worldcoord, self.qscale)
            #  add camera intrinsics and extract model in vehicle speeds
            # TODO add speed module later
            # speeder = VehicleSpeed(self.camera_intrinsics)
            frame_number = 1
            empty_frame_counter = 0
            # latest_video = self.get_video_to_process()
            # self.check_and_delete()
            #fifo_pipe = self.getboxval()

            '''
            lat_file = os.read(fifo_pipe, 28)
            print(lat_file)
            lat_file = lat_file.decode("utf-8")
            '''

#            try:
#                head_same = os.read(fifo_pipe, 1)
#            except IOError:
#                print("didn't get HEADER for frame")
#                continue
#            head_same = int.from_bytes(head_same, "big")
#            if head_same == 3:
#                head_same = 0
#                continue
#
            # try:
            current_time = time.time()*1000
            fifo_pipe = os.open(self.pipe_path, os.O_RDONLY)
            lat_file = os.read(fifo_pipe, 28)
            print("Read file name at {}\n".format(current_time))
            logfile.write("Read file name at {}\n".format(current_time))
            os.close(fifo_pipe)
            # lat_file = self.read_from_pipe(28)
            print("lat_file received Python side",lat_file)
            logfile.write("lat_file received Python side :: {}\n".format(lat_file))
            lat_file = lat_file.decode("utf-8")

            # except IOError:
            #     print("didn't get latest file")
            #     continue
            # except Exception as excp:
            #     print("some other error ", excp)

            #print("previous file name: {}".format(previous_file))
            print("latest file name: {}\n".format(lat_file))
            logfile.write("latest file name: {}\n".format(lat_file))
            lat_file_path = os.path.join("./segments", self.segment_path, lat_file)

            if not os.path.exists(lat_file_path):
                print("The file has dissappeared in python, desynchronized:: The file required is: ", lat_file_path)
                # print("Waiting for correct file.\r")
                # print("Waiting for correct file..\r")
                # print("Waiting for correct file...\r")
                sys.exit()

                # TODO Make the change in the c++ side
                # while(os.path.exists(lat_file_path)==False):
                #     self.write_status(False, logfile)
                #     fifo_pipe = os.open(self.pipe_path, os.O_RDONLY)
                #     lat_file = os.read(fifo_pipe, 28)
                #     print("Read file name at {}\n".format(current_time))
                #     logfile.write("Read file name at {}\n".format(current_time))
                #     os.close(fifo_pipe)
                #     lat_file_path = os.path.join("./segments", self.segment_path, lat_file)

            self.write_status(True, logfile)
            cap = cv2.VideoCapture(lat_file_path)

            if (not cap.isOpened()):
                continue

            print("~~~~~~~~~~~~~~~~~~~~~~~~~~ ENTERING FILE LOOP ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            while (1):
                frame_time = time.time()
                ret, frame = cap.read()
                print("return value ---- ", ret)
                logfile.write("return value ---- {}\n".format(ret))

                if frame is None:
                    print("Frame is None; for :: ", frame_number)
                    logfile.write("Frame is None; for :: {}\n".format(frame_number))
                    empty_frame_counter += 1
#                    if empty_frame_counter == 10:
#                        break
#                    continue
                    print("&&&&&&&&&&&&& FRAME IS NONE BREAK")
                    logfile.write("&&&&&&&&&&&&& FRAME IS NONE BREAK &&&&&&&&&&&&&&&&&&&")
                    break

                # print("frame_shape value ---- ", frame.shape)
                # logfile.write("frame_shape value ---- {}\n".format(frame.shape))

                if not ret:
                    print("continuing to next iter as no frame found at:", lat_file_path)
                    logfile.write("continuing to next iter as no frame found at: {}\n".format(lat_file_path))
                    break
                # print("image Size :::", frame.size)


                # try:
                current_time = time.time()*1000
                fifo_pipe = os.open(self.pipe_path, os.O_RDONLY)
                head = os.read(fifo_pipe, 1)
                print("Header read at {}\n".format(current_time))
                logfile.write("Header read at {}\n".format(current_time))
                os.close(fifo_pipe)
                    # head = self.read_from_pipe()
                    #print("pipe read::::::::::::::::")
                # except IOError:
                #     print("didnt get HEADER for frame")
                #     continue
                head = int.from_bytes(head, "big")
                logfile.write("head of frame :: {}\n".format(head))
                print("FRAME NUMBER == ", frame_number)
                logfile.write("FRAME NUMBER == {}\n".format(frame_number))
                # if frame_number <= 20:
                #     cv2.imwrite('~/home/rbccps/saved_frames/pythonframe{}.jpg'.format(frame_number), frame)
                frame_number += 1
                if head == 0:
                    self.write_status(True, logfile)
                    continue
                elif ((head < 0) or (head > 99)):
                    print("PYTHON LOGS ## Weird head, got value :: ", head)
                    self.write_status(False, logfile)
                    print("&&&&&&&&&&&&& WEIRD HEAD LOOP SYS EXIT FOUND &&&&&&&&&&&&&&")
                    logfile.write("&&&&&&&&&&&&&WEIRD HEAD LOOP SYS EXIT FOUND  &&&&&&&&&&&&&&&&&&&")
                    sys.exit()
                self.write_status(True, logfile)

                detections = []

                print("~~~~~~~~~~~~~~~~~~~~~~~~~~ ENTERING BBOX LOOP ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                for i in range(head):
                    current_time = time.time()*1000
                    fifo_pipe = os.open(self.pipe_path, os.O_RDONLY)
                    data_bytes = os.read(fifo_pipe, 24)
                    print("BBox read at {}\n".format(current_time))
                    logfile.write("BBox read at {}\n".format(current_time))
                    os.close(fifo_pipe)
                    print("BBox byte length {}\n".format(len(data_bytes)))
                    logfile.write("BBox byte length {}\n".format(len(data_bytes)))
                    # data_bytes = self.read_from_pipe(24)
                    try:
                        data = struct.unpack("=iiiiif", data_bytes)
                        #print("struct unpacked ::::::::::")
                    except struct.error as err:
                        print("ERROR: @@Struct couldnt be unpacked@@ ",err)
                        logfile.write("ERROR: @@Struct couldnt be unpacked@@")
                        self.write_status(False, logfile)
                        sys.exit(0)

                    logfile.write("bbox data recieved :: {}\n".format(data))
                    if not (0 < data[-1] <= 1):
                        print("PYTHON LOG ## DATA[-1] = ", data[-1])
                        self.write_status(False, logfile)
                        print("PYTHON LOG ## Something is wrong with the BBox Value")
                        sys.exit(0)
                    self.write_status(True, logfile)

                    detections.append(Box(data))
                    # detections.append(Box(new_data))

                sframe = SuFrame(frame)
                sframe.set_dets(detections)
                _ = DeepSort.run_deep_sort(sframe)
                vehicle_counts = counter.get_count(sframe)
                op_dump = os.path.join("results/", self.segment_path, lat_file.split('.')[0]+'.json')
                with open(op_dump, 'a+') as json_file:
                    json.dump(vehicle_counts, json_file)
                # print("VS::", vehicle_speeds)
                frame_duration = time.time() - frame_time
                #print("Time taken for process of one frame python side :", frame_duration*1000, "ms")
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
