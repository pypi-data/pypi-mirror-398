import cv2
import numpy as np


class TileUtils:

    @staticmethod
    def add_border(a, thickness=0.05, color=(0, 0, 0)):
        '''

        :param a: the matrix image
        :param thickness: border thickness
        :return:
        '''

        h, w, c = a.shape

        # some coordinates may be part of cropped part of heatmap (recall we do tile size * divide fac). ignore those ones
        if h == 0 or c == 0:
            return

        if c != 3:
            raise Exception('Only RGB images supported')

        pixel_len = min(int(w * thickness), int(h * thickness))

        # for each row in the image
        for j in range(h):
            # if we are in first 5% or last% of rows, we color the whole row
            if j <= pixel_len or j >= w - pixel_len:
                # color entire row
                for i in range(3):
                    a[j, :, i] = color[i]
            else:

                # color the leftmost and rightmost 5% of the row
                for i in range(3):
                    a[j, :pixel_len, i] = color[i]
                    a[j, (w - pixel_len):, i] = color[i]

    @staticmethod
    def add_text(a, text, bottom_left_corner_of_text, color=(0, 0, 0), font_scale=1, thickness=2):
        font = cv2.FONT_HERSHEY_DUPLEX

        cv2.putText(a, text,
                    bottom_left_corner_of_text,
                    font,
                    font_scale,
                    color,
                    thickness)
