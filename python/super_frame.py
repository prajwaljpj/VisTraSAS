import cv2

class SuFrame(object):
    """frame with metadata of yolo deepsort tracklets or any other
    Its easy to handle every frame with its own metadata it can be
    pushed around between modules easily.
    """

    def __init__(self, frame, dets):
        super(SuFrame, self).__init__()
        self.frame = frame
        self.dets = dets

    # set members 
    def set_trackers(self, trackers):
        self.trackers = trackers

    def set_HgPoints(self, HgPoints):
        self.HgPoints = HgPoints

    def set_HgPointers(self, HgPointers):
        self.HgPointers = HgPointers

    # get members
    def get_trackers(self):
        if not self.trackers:
            print("No trackers available")
            return None
        return self.trackers

    def get_HgPoints(self):
        if not self.HgPoints:
            print("No achor points available")
            return None
        return self.HgPoints

    def get_HgPointers(self):
        if not self.set_HgPointers:
            print("No achor points available")
            return None
        return self.set_HgPointers

    def get_image(self):
        if not self.frame:
            print("frame is black")
            return None
        return self.frame

    def get_dets(self):
        return self.dets

    def get_dets_dict(self):
        return [det.__dict__() for det in self.dets]

    def get_scores(self, arg):
        return [sc.class_confidence() for sc in self.dets]

    def get_class_ids(self):
        return [cid.class_id() for cid in self.dets]

    def get_class_names(self):
        return [cnm.class_name() for cnm in self.dets]
    
    def get_ds_boxes(self):
        return [dsb.ds_format() for dsb in self.dets]

    def show_frame(self):
        try:
            cv2.imshow(self.frame)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            return True
        except:
            return False

    def wrap_box(self):
        wrap_frame = self.frame
        cv2.rectangle(wrap_frame, (self.dets.left(), self.dets.top()),
                      (self.dets.right(), self.dets.bottom()), (255,0,0), 2)
        cv2.putText(wrap_frame, self.dets.class_name(), (self.dets.left(), self.dets.top()),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(wrap_frame, str(self.dets.class_confidence()),
                    (self.dets.right(), self.dets.bottom()), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (255, 0, 0), 2, cv2.LINE_AA)
        return wrap_frame
