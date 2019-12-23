from speed_estimate_class_updated3 import speed_estimation
import cv2
from auto_track import analytics_rbc

if __name__ == '__main__':
    # Pass yolo output to speed_estimate method below.
    image = cv2.imread("/home/rbccps2080ti/projects/link_speed_estimation/ta_darknet/test.jpg")
    count_line = [(650, 400), (1000, 500)]
    sline_1_203 = [(1065, 514), (524, 366)]
    sline_2_203 = [(1038, 704), (151, 406)]
    a = analytics_rbc(count_line, sline_1_203, sline_2_203)
    trackers_list = a.run_analytics(image, 300)
    im_h, im_w, im_c = image.shape
    sp_obj = speed_estimation()
    sp_obj.speed_estimate(image)
