import time
from collections import deque
import openslide
import cv2
import numpy as np

from havoc_clustering_v2.general_utility.image_creator import ImageCreator
# from general_utility.image_creator import ImageCreator


class TileExtractor:

    def __init__(self, slide, tile_size=512, map_scale_fac=16, coordinates=None):
        '''
        Creates a tile extractor object for the given slide

        If desired MPP and slide MPP match, then this serves as a raw tile extractor.
        If they don't match:
            if slide MPP is smaller (larger magnification), takes a larger tile size and resizes the tile down
            if slide MPP is larger (smaller magnification), takes a smaller tile size and resizes the tile up

        :param slide: slide object
        :param tile_size: the size of tiles to extract (in 20x)
        '''

        self.slide = slide
        self.original_tile_size = tile_size
        # NOTE: This is fixed in order to ensure consistency. All tiles extracted will be in 20x at the specified tile size
        self.desired_tile_mpp = 0.5040

        # NOTE: the slides could have different but very similar mpp which can result in errors later
        if slide.mpp and np.abs(slide.mpp - self.desired_tile_mpp) < 0.01: slide.mpp = self.desired_tile_mpp

        # resize tile size if required. if the slide's mpp has too high precision, round down to avoid numerical issues
        factor = self.desired_tile_mpp / round(slide.mpp, 3) if slide.mpp else 1
        modified_tile_size = int(tile_size * factor)
        self.modified_tile_size = modified_tile_size
        self.tile_size_resize_factor = factor

        # 'Crop' leftover from right and bottom
        self.trimmed_width = slide.width - (slide.width % modified_tile_size)
        self.trimmed_height = slide.height - (slide.height % modified_tile_size)
        self.chn = 3

        # for use with ImageCreator. the actual output dimensions once we extract all tiles
        self.output_width = int(self.trimmed_width / factor)
        self.output_height = int(self.trimmed_height / factor)

        self.coordinates = self.get_all_possible_coordinates() if coordinates is None else coordinates

        # best way to have an efficiently created thumbnail guaranteed. it is free if we go through the whole slide
        self.extraction_map = ImageCreator(
            height=self.trimmed_height / factor,
            width=self.trimmed_width / factor,
            scale_factor=map_scale_fac,  # make resulting image size smaller
            channels=self.chn
        )

    @staticmethod
    def amount_tissue(tile):
        '''
        Returns percentage of how many pixels are tissue within the tile

        :param tile: BGR numpy array
        :return:
        '''

        # COLOR CHECK
        # issue: RGB std method overcalls colorful stuff (tints, weird chroma-y backgrounds)
        score1 = 1 - (np.sum(np.std(tile, axis=2) < 2.75) / (tile.shape[0] * tile.shape[1]))

        # DARKNESS CHECK
        # issue: Grayscale method overcalls dark stuff (smudges, pen, sometimes shadows).
        bw_tile = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
        score2 = 1 - ((bw_tile > 220).sum() / (bw_tile.shape[0] * bw_tile.shape[1]))

        # Both checks above are biased toward calling “tissue” in their own way too often. Taking min(.) makes sure that
        # the tile must be both non-blank in grayscale and non-blank in color.
        return min(score1, score2)

    def get_all_possible_coordinates(self):
        x = y = 0
        tile_size = self.modified_tile_size

        possible_coordinates = []

        # break out when top left coordinate of next tile is the bottom of image
        while y != self.trimmed_height:

            # Get current sub-image
            x_adj = x + self.slide.start_coordinate.x
            y_adj = y + self.slide.start_coordinate.y

            possible_coordinates.append((x_adj, y_adj, x_adj + tile_size, y_adj + tile_size))

            # move onto next spot
            x += tile_size
            if x == self.trimmed_width:
                x = 0
                y += tile_size

        return possible_coordinates

    def iterate_tiles2(self, min_tissue_amt=0.0, batch_size=4, print_time=True):
        '''
        A generator that iterates over the tiles within the supplied slide (dictated by self.coordinates)

        :param min_tissue_amt: tile must have at least this percentage of tissue
        :param batch_size: get x tiles at once
        :param print_time: for printing out how many tiles/how many to go
        :return: dict containing array of tiles and coordinates
        '''

        if not (0 <= min_tissue_amt <= 1):
            raise Exception("Minimum tissue amount must be a percentage between 0.0 and 1.0")

        if batch_size < 1:
            raise Exception('Batch size must be at least 1')

        # initialization
        start_time = time.time()

        # buffer for our batches. will keep updating this each yield
        tiles_buffer = np.zeros((batch_size, self.original_tile_size, self.original_tile_size, self.chn),
                                dtype=np.uint8)
        coordinates_buffer = np.zeros((batch_size, 4), dtype=int)
        amt_tissue_buffer = np.zeros((batch_size,), dtype=float)
        buffer_i = 0

        coordinates = deque(self.coordinates)
        num_coordinates = len(coordinates)
        while len(coordinates):
            x, y, x2, y2 = coordinates.popleft()

            if isinstance(self.slide.image, openslide.ImageSlide) or isinstance(self.slide.image, openslide.OpenSlide):
                tile = np.array(self.slide.image.read_region((x, y), 0, (x2 - x, y2 - y)))[:, :, 2::-1]
            else:
                tile = np.array(self.slide.image.crop((x, y, x2, y2)))[:, :, 2::-1]

            r = 1 / self.tile_size_resize_factor
            if r != 1:
                tile = cv2.resize(tile, (self.original_tile_size, self.original_tile_size))

            self.extraction_map.add_tile(tile, (int(x * r), int(y * r), int(x2 * r), int(y2 * r)))

            # only yield if under maximum blank allowance
            curr_amt_tissue = TileExtractor.amount_tissue(tile)
            if curr_amt_tissue >= min_tissue_amt:
                top_left_x, top_left_y = int(x * r), int(y * r)
                bot_right_x, bot_right_y = int(x2 * r), int(y2 * r)
                coordinate = (top_left_x, top_left_y, bot_right_x, bot_right_y)

                tiles_buffer[buffer_i] = tile
                coordinates_buffer[buffer_i] = coordinate
                amt_tissue_buffer[buffer_i] = curr_amt_tissue
                buffer_i += 1

                if buffer_i == batch_size:
                    buffer_i = 0
                    yield {'tiles': tiles_buffer.copy(), 'amt_tissue': amt_tissue_buffer.copy(),
                           'coordinates': coordinates_buffer.copy()}

            if print_time:
                if (num_coordinates // 10) and (len(coordinates) % (num_coordinates // 10)) == 0:
                    print("{:0.2f}% ({}/{} cooordinates) in {:0.2f}s".format(
                        (1 - len(coordinates) / num_coordinates) * 100,
                        num_coordinates - len(coordinates),
                        num_coordinates,
                        time.time() - start_time))

        # may have leftover tiles
        if buffer_i > 0:
            yield {'tiles': tiles_buffer[:buffer_i, :, :, :], 'amt_tissue': amt_tissue_buffer[:buffer_i, ],
                   'coordinates': coordinates_buffer[:buffer_i, :]}
