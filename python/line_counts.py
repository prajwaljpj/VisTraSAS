from collections import  defaultdict
import configparser
from python.deepsort import deepsort_tracker
import cv2


class counts(object):
    """This Module is used to generate counts. Depends on yolo and deepsort_tracker

    """
    def __init__(self, line_coord):
        super(counts, self).__init__()
        self.line_coord = line_coord
        # parser = configparser.SafeConfigParser()
        # _ = parser.read("configs/global.cfg")
        # self.yolo_model = parser.get("Yolo", "model_path")
        # classes_path = parser.get("general", "classes")
        # TODO change hardcoded paths
        with open("/home/rbccps2080ti/projects/VisTraSAS/configs/class.names", "r") as cls_file:
            self.classes = cls_file.readlines()
            self.classes = [nm.strip() for nm in self.classes]
        self.below_line = set()
        self.above_line = set()
        self.considered = set()
        self.v_count_up = defaultdict(int)
        self.v_count_down = defaultdict(int)

        for c in self.classes:
            self.v_count_up[c]
            self.v_count_down[c]

    def calc_line_point(self, point_cord, frame):
        xy0, xy1 = self.line_coord
        if((xy1[1]-xy0[1])==0 or (xy1[1]-xy0[1])==0):
            print("coordinates give a point and not a line!!")
        try:
            slope = (xy1[1]-xy0[1])/(xy1[0]-xy0[0])
        except(ZeroDivisionError):
            print("coordinates give a point and not a line!!")
            exit(0)
        #Determinant method
        d = (point_cord[0]-xy0[0])*(xy1[1]-xy0[1]) - (point_cord[1] - xy0[1])*(xy1[0]-xy0[0])
        height, width = frame.shape[:2]
        y1old = xy0[1]
        y2old = xy1[1]
        const = xy0[1]-(slope*xy0[0])
        y1new = int(slope*0 + const)
        y2new = int(slope*width + const)
        cv2.line(frame, (0, y1new), (width, y2new), (0, 0, 0), 2)
        d = (point_cord[0] - 0)*(y2new - y1new) - (point_cord[1] - y1new)*(width - 0)
        if (d == 0):
            return 0
        elif (d < 0):
            # Above the line
            return 1
        elif (d > 0):
            # Below the line
            return -1


    def count_id(self, bbox, id_num, classname, frame):
        # line coordinates is of the format ((x1, y1), (x2, y2))
        #Centroid
        bbox_hat = [int((bbox[0] + bbox[2])/2), int((bbox[1] + bbox[3])/2)]

        point_position = self.calc_line_point(bbox_hat, frame)

        # Zero is impossible!
        if(point_position == 1):
            if id_num in self.below_line:
                self.v_count_up[classname] += 1
                self.below_line.remove(id_num)
                self.considered.add(id_num)
            else:
                self.above_line.add(id_num)
        elif(point_position == -1):
            if(id_num in self.above_line):
                self.v_count_down[classname] += 1
                self.above_line.remove(id_num)
                self.considered.add(id_num)
            else:
                self.below_line.add(id_num)


    def get_count(self, super_frame):
        frame = super_frame.get_image()
        tracker = super_frame.get_trackers()
        # det_box = super_frame.get_dets_tlbr()
        # print("detections of super frame in tlbr: ", det_box)
        for track in tracker:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue
            bbox = track.to_tlbr()
            # print(bbox)
            
            classname = track.classname
            # print(classname)
            # classname = classname.decode('utf8').strip('\r')
            id_num = str(track.track_id)
            self.count_id(bbox, id_num, classname, frame)  
        return_dict = {'up_count': self.v_count_up, 'down_count': self.v_count_down}
        return return_dict
