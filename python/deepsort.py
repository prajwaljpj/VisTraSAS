import os
import numpy as np
import tensorflow as tf
import sys
import configparser
import cv2
sys.path.insert(0, "/home/rbccps/projects/VisTraSAS/deep_sort")

# from deep_sort.deep_sort.detection import Detection
# from deep_sort.application_util import visualization, preprocessing as prep
# from deep_sort.deep_sort import nn_matching
# from deep_sort.tools import generate_detections
# from deep_sort.deep_sort.tracker import Tracker

from deep_sort.detection import Detection
from application_util import visualization, preprocessing as prep
from deep_sort import nn_matching
from tools import generate_detections
from deep_sort.tracker import Tracker

os.environ['KERAS_BACKEND'] = 'tensorflow'
CONFIG = tf.ConfigProto()
#CONFIG.gpu_options.per_process_gpu_memory_fraction = 0.15
CONFIG.gpu_options.per_process_gpu_memory_fraction = 0.01
SESSION = tf.Session(config=CONFIG)


class deepsort_tracker():
    def __init__(self):
        # loading this encoder is slow, should be done only once.
        parser = configparser.ConfigParser()
        _ = parser.read("configs/global.cfg")
        self.deepsort_model = parser.get("Deepsort", "model_path")
        # print(self.deepsort_model)
        self.encoder = generate_detections.create_box_encoder(
            "/home/rbccps/projects/VisTraSAS/models/mars-small128.pb")
        # print("The model has been loaded")
        self.metric = nn_matching.NearestNeighborDistanceMetric(
            "cosine", .5, 100)
        self.tracker = Tracker(self.metric)

    def reset_tracker(self):
        self.tracker = Tracker(self.metric)

    # Older yolo used to give y,x,h,w.
    """
        def format_yolo_output( self,out_boxes):
                out_boxes=np.array([out_boxes[:,1],out_boxes[:,0],\
                        out_boxes[:,3]-out_boxes[:,1],out_boxes[:,2]-out_boxes[:,0]])
                out_boxes=out_boxes.T
                return out_boxes                                
        """

    # Current Yolo gives x_center,y_center,w,h
    # Deep sort needs the format `top_left_x, top_left_y, width,height

    def format_yolo_output(self, out_boxes):
        for b in range(len(out_boxes)):
            out_boxes[b][0] = out_boxes[b][0] - out_boxes[b][2]/2
            out_boxes[b][1] = out_boxes[b][1] - out_boxes[b][3]/2
        return out_boxes

    def run_deep_sort(self, super_frame):

        # out_boxes = self.format_yolo_output(out_boxes)
        bbox = super_frame.get_ds_boxes()
        out_scores = super_frame.get_scores()
        frame = super_frame.get_image()
        out_classes = super_frame.get_class_names()
        # cv2.imshow("asdf", frame)
        # cv2.waitKey(0)
        # print(bbox)
        # print(out_scores)
        # print(out_classes)

        detections = np.array(bbox)
        # print(detections)
        features = self.encoder(frame, detections.copy())
        # print("feat done")
        # print(len(features))
        #features = self.encoder.extract_features(frame,detections)

        # print(frame.shape)

        detections = [Detection(bbox, score, feature, classname)
                      for bbox, score, feature, classname in
                      zip(detections, out_scores, features, out_classes)]

        outboxes = np.array([d.tlwh for d in detections])

        outscores = np.array([d.confidence for d in detections])
        indices = prep.non_max_suppression(outboxes, 0.8, outscores)

        detections = [detections[i] for i in indices]
        self.tracker.predict()
        self.tracker.update(detections)
        trackers = self.tracker.tracks
        super_frame.set_trackers(trackers)
        return trackers
