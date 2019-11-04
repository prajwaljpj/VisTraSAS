import os
import cv2
import configparser

class Box(object):
    """Documentation for Box

    """

    def __init__(self, box_tuple):
        super(Box, self).__init__()
        parser = configparser.SafeConfigParser()
        found = parser.read(["../configs/global.cfg", "../configs/Global.cfg", "../configs/globals.cfg"])
        classes = parser.get("general", "classes")
        with open(classes, "r") as cls_file:
            cls_names = cls_file.readlines()
            cls_names = [nm.strip() for nm in cls_names]
        self.class_names_dict = {cls_names[i]: i for i in range(len(cls_names))}
        self.box_tuple = box_tuple
        # self.class_names_dict = {
        #     "car": 0,
        #     "bus": 1,
        #     "truck": 2,
        #     "three-wheeler": 3,
        #     "two-wheeler": 4,
        #     "lcv": 5,
        #     "tempo-traveller": 6,
        #     "bicycle": 7,
        #     "people": 8
        # }
        self.box_dict = self.todict()

    def todict(self):
        box_dict = {
            "class": {
                "class_name":
                list(self.class_names_dict.keys())[list(self.class_names_dict.values()).index(self.box_tuple[0])],
                "class_confidence": self.box_tuple[-1],
                "class_id": self.box_tuple[0],
            },
            "coord": {
                "top": self.box_tuple[3],
                "bottom": self.box_tuple[4],
                "left": self.box_tuple[1],
                "right": self.box_tuple[2]
            }
        }
        return box_dict

    def left(self):
        return self.box_dict["coord"]["left"]

    def right(self):
        return self.box_dict["coord"]["right"]

    def top(self):
        return self.box_dict["coord"]["top"]

    def bottom(self):
        return self.box_dict["coord"]["bottom"]

    def class_confidence(self):
        return self.box_dict["class"]["class_confidence"]

    def class_name(self):
        return self.box_dict["class"]["class_name"]

    def class_id(self):
        return self.box_dict["class"]["class_id"]

    def ds_format(self):
        op = (self.left(), self.top(), self.right()-self.left(), self.top()-self.bottom())
        return op


    def __dict__(self):
        return self.box_dict
