import numpy as np
import cv2

from havoc_clustering_v2.general_utility.tile_image_utils import TileUtils
# from general_utility.tile_image_utils import TileUtils


class ImageCreator:

    def __init__(self, height, width, scale_factor=1, channels=3):
        '''

        Creates an image of the specified size except scaled down by an optional factor amount

        :param height:
        :param width:
        :param scale_factor: scale the created image down by a factor of this amount
        :param channels:
        '''

        # this matrix will always have the specified dtype
        self.image = np.ones((int(height / scale_factor), int(width / scale_factor), channels), dtype=np.uint8) * 255
        self.scale_factor = scale_factor

    def _get_scaled_coordinate(self, coordinate):
        return tuple(int(c / self.scale_factor) for c in coordinate)

    def add_tile(self, tile, coordinate):
        '''

        :param tile: a 0-255 valued matrix
        :param coordinate: tuple containing top left and bottom right coordinate of image (x1, y1, x2, y2)
        :return:
        '''

        # adjust coordinates depending on if we want to scale our image
        x1_adj, y1_adj, x2_adj, y2_adj = self._get_scaled_coordinate(coordinate)

        # Put sub-image into correct spot of matrix (recreating image) by resizing tile if needed to fit within the spot
        self.image[y1_adj:y2_adj, x1_adj:x2_adj, :] = cv2.resize(tile, (x2_adj - x1_adj, y2_adj - y1_adj))

    def get_tile(self, coordinate):
        '''

        :param coordinate: tuple containing top left and bottom right coordinate of image (x1, y1, x2, y2)
        :return:
        '''

        # adjust coordinates depending on if we want to scale our image
        x1_adj, y1_adj, x2_adj, y2_adj = self._get_scaled_coordinate(coordinate)

        # get sub-image from correct spot of matrix and resize tile if needed to be within original passed in coordinate dims
        return cv2.resize(self.image[y1_adj:y2_adj, x1_adj:x2_adj, :],
                          (coordinate[2] - coordinate[0], coordinate[3] - coordinate[1]))

    def add_borders(self, coordinates, border_thickness=0.1, color=(0, 255, 0)):
        '''
        Adds colored borders onto the image at the coordinates. Default is bright green

        :param coordinates: tuple containing top left and bottom right coordinate of image
        :param color: BGR tuple
        :return:
        '''

        for idx, coordinate in enumerate(coordinates):
            # adjust coordinates depending on if we want to scale our image
            x1_adj, y1_adj, x2_adj, y2_adj = self._get_scaled_coordinate(coordinate)

            curr_slice = self.image[y1_adj:y2_adj, x1_adj:x2_adj, :]

            TileUtils.add_border(curr_slice, thickness=border_thickness, color=color)
            # curr_slice = cv2.copyMakeBorder(curr_slice, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=(0,1,0))
