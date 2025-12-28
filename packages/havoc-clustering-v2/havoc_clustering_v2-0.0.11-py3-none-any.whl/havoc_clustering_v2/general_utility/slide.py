from enum import Enum
import re
import pathlib
from collections import namedtuple
from datetime import datetime
import openslide
from PIL import Image, ImageFile

Image.MAX_IMAGE_PIXELS = 100000000000
ImageFile.LOAD_TRUNCATED_IMAGES = True


class ImageType(Enum):
    # our supported image types
    SVS = '.svs'
    JPG = '.jpg'
    JPEG = '.jpeg'
    PNG = '.png'
    NDPI = '.ndpi'
    TIF = '.tif'
    TIFF = '.tiff'

    @classmethod
    def supports(cls, value):
        '''
        Checks if given value is a supported image type
        :param value: str
        :return:
        '''
        return any(value == item.value for item in cls)


class ImageTypeError(Exception):
    pass


class Slide:
    '''
    A slide object
    '''

    def __init__(self, path, mpp=None):
        '''
        Creates a slide object with metadata
        '''

        self.path = path
        self.name = pathlib.Path(path).stem
        self.image_type = pathlib.Path(path).suffix
        if not ImageType.supports(self.image_type):
            raise ImageTypeError("We currently do not support images of type {}".format(self.image_type))

        # the actual instance of the image at the given path
        if self.image_type == ImageType.SVS.value or self.image_type == ImageType.NDPI.value or self.image_type == ImageType.TIF.value or self.image_type == ImageType.TIFF.value:
            i = openslide.open_slide(self.path)
            w, h = i.dimensions
        else:
            i = Image.open(self.path)
            w, h = i.width, i.height

        Coordinate = namedtuple('Coordinate', 'x y')
        self.start_coordinate = Coordinate(0, 0)
        self.width = w
        self.height = h
        self.image = i

        if self.image_type == ImageType.SVS.value:
            curr_slide_data = self.extract_data_svs()
        elif self.image_type == ImageType.NDPI.value:
            curr_slide_data = self.extract_data_ndpi()
        else:
            curr_slide_data = self.extract_data_no_metadata()

        self.date_scanned = curr_slide_data['date_scanned']
        self.time_scanned = curr_slide_data['time_scanned']
        self.compression = curr_slide_data['compression']
        self.mpp = mpp if mpp is not None else curr_slide_data['mpp']
        self.apparent_magnification = curr_slide_data['apparent_magnification']  # only here while in process of removal

    def crop(self, coordinates):
        '''
        Updates internal slide properties so that we will only use a section of the slide

        :param coordinates: use only a section of the slide (top_left_x, top_left_y, bot_right_x, bot_right_y)
        :return:
        '''
        Coordinate = namedtuple('Coordinate', 'x y')
        self.start_coordinate = Coordinate(coordinates[0], coordinates[1])
        self.width = coordinates[2] - coordinates[0]
        self.height = coordinates[3] - coordinates[1]

    def extract_data_svs(self):
        '''
        Extracts useful metadata from the svs
        '''

        # dictionary of properties
        image_properties = self.image.properties

        if 'aperio.Date' not in image_properties:
            date_scanned = None
            time_scanned = None
        else:
            # for date and time
            date_scanned = image_properties['aperio.Date']
            # check if was a datetime (requires separation) or just date (there is another property for time)
            if 'aperio.Time' not in image_properties:
                date_scanned = re.search('\d{4}-\d{2}-\d{2}', image_properties['aperio.Date']).group()
                time_scanned = re.search('\d{2}:\d{2}:\d{2}', image_properties['aperio.Date']).group()
            else:
                time_scanned = image_properties['aperio.Time']

        # check if we have mag/compression data
        if 'tiff.ImageDescription' not in image_properties:
            mpp = compression = None
        else:
            mpp = re.search('MPP = ([\d.]+)', image_properties['tiff.ImageDescription'])
            compression = re.search('Q=(\d+)', image_properties['tiff.ImageDescription'])

            # get just the numeric portion of the above regex result
            if mpp is not None:
                mpp = float(mpp.group(1))
            if compression is not None:
                compression = int(compression.group(1))

        # archived. should NOT use this
        if 'aperio.AppMag' in image_properties:
            apparent_magnification = int(float(image_properties['aperio.AppMag']))
        else:
            apparent_magnification = None

        return {
            'date_scanned': date_scanned,
            'time_scanned': time_scanned,
            'compression': compression,
            'mpp': mpp,
            'apparent_magnification': apparent_magnification
        }

    def extract_data_ndpi(self):
        '''
        Extracts useful metadata from the ndpi
        '''

        # dictionary of properties
        image_properties = self.image.properties

        # https://github.com/InsightSoftwareConsortium/ITKIOOpenSlide/blob/master/examples/ExampleOutput.txt

        datetime2 = datetime.strptime(image_properties['tiff.DateTime'], '%Y:%m:%d %H:%M:%S')

        # works with .svs and .ndpi
        if 'openslide.objective-power' in image_properties:
            apparent_magnification = int(float(image_properties['openslide.objective-power']))
        else:
            apparent_magnification = None

        return {
            'date_scanned': datetime2.strftime('%m/%d/%y'),
            'time_scanned': datetime2.strftime('%H:%M:%S'),
            'compression': None,
            'mpp': float(image_properties['openslide.mpp-x']) if 'openslide.mpp-x' in image_properties else None,
            'apparent_magnification': apparent_magnification
        }

    def extract_data_no_metadata(self):
        return {
            'date_scanned': None,
            'time_scanned': None,
            'compression': None,
            'mpp': None,
            'apparent_magnification': None
        }
