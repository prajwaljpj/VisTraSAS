import configparser
from deepsort import deepsort_tracker


class counts(object):
    """This Module is used to generate counts. Depends on yolo and deepsort_tracker

    """
    def __init__(self, line_coord):
        super(counts, self).__init__()
        self.line_coord = line_coord
        parser = configparser.SafeConfigParser()
        found = parser.read(["../configs/global.cfg", "../configs/Global.cfg", "../configs/globals.cfg"])
        self.yolo_model = parser.get("Yolo", "model_path")


    def get_count(self, super_frame, time_slot):
        frame = super_frame.get_image()
        dets = super_frame.get_dets()
        trackers = deepsort_tracker.run_deep_sort(frame, super_frame.get_scores(), super_frame.get_ds_boxes(), super_frame.get_class_names())
