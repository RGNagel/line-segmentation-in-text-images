import skimage
from skimage.color import rgb2gray, rgba2rgb, gray2rgb
from skimage.util import img_as_ubyte
from skimage.draw import rectangle_perimeter, set_color
from skimage import io

import numpy as np


class TextImage:

    WHITE = 1
    BLACK = 0

    def __init__(self, filepath, threshold_img_bin = 0.5, threshold_percent_px_cols = 0.1, threshold_qty_px_rows_is_text = 5):

        assert threshold_img_bin >= 0 and threshold_img_bin <= 1, "threshold_img_bin is out of range"
        self.threshold_img_bin = threshold_img_bin

        assert threshold_percent_px_cols >= 0 and threshold_percent_px_cols <= 1, "threshold_percent_px_cols out of range"
        self.threshold_percent_px_cols = threshold_percent_px_cols

        assert threshold_qty_px_rows_is_text >= 1, "threshold_qty_px_rows_is_text out of range"
        self.threshold_qty_px_rows_is_text = threshold_qty_px_rows_is_text

        self.lines = []

        self.filepath = filepath
        image = io.imread(filepath)

        print(image[0][0])
        # image = io.imread('images/teste.jpg', np.float64)

        if image[0][0].size == 1:
            self.image_rgb  = gray2rgb(image)
            # by default gray is 0..1
            self.image_gray = rgb2gray(image)
        elif image[0][0].size == 4:
            self.image_rgb  = rgba2rgb(image)
            self.image_gray = rgb2gray(self.image_rgb)
        elif image[0][0].size == 3:
            self.image_rgb  = image
            self.image_gray = rgb2gray(self.image_rgb)
        else:
            raise Exception("image pixel dimension is not supported")

        # assure pixels are represented in 0-255 range
        self.image_rgb = img_as_ubyte(self.image_rgb)

        self.image_bin  = self.image_gray > threshold_img_bin

        self.rows = self.image_gray.shape[0]
        self.cols = self.image_gray.shape[1]

        self.background_color = self.calcBackgroundColor()

        if self.background_color == self.WHITE:
            self.text_color = self.BLACK
        else:
            self.text_color = self.WHITE

        assert self.text_color != self.background_color, "Background and text colors are the same!"

    
    def calcBackgroundColor(self):
        
        r, c = rectangle_perimeter((1,1), end=(self.rows, self.cols), shape=self.image_gray.shape)

        black_ctr = 0
        white_ctr = 0

        for point in self.image_gray[r, c]:
            
            if point == self.BLACK:
                black_ctr = black_ctr + 1
            else:
                white_ctr = white_ctr + 1

        assert white_ctr != black_ctr, "Image perimeter has equal black and white pixels..."

        if white_ctr > black_ctr:
            return self.WHITE
        else:
            return self.BLACK


    def getTextLines(self):

        th = 0.1 # 0 to 1

        text_lines = 0
        row_ctr = 0

        # for every pixel row
        for row in range(0, self.rows):

            text_pxs = 0
            background_pxs = 0

            # for every pixel column
            for col in range(0, self.cols):
                if self.image_bin[row][col] == self.text_color:
                    # black
                    text_pxs = text_pxs + 1
                else:
                    # white
                    background_pxs = background_pxs + 1

            if text_pxs / self.cols >= self.threshold_percent_px_cols:
                row_ctr = row_ctr + 1

            elif row_ctr >= self.threshold_qty_px_rows_is_text:
                # a text line was identified
                text_lines = text_lines + 1
                # save line coordinates for future operations
                self.lines.append(TextLineImage(start=(row - row_ctr, 0), end=(row, self.cols - 1)))
                row_ctr = 0


            # next pixel row or finished

        return text_lines


    def drawTextLines(self):

        for line in self.lines:
            line.drawPerimeter(self.image_rgb)

    def saveImages(self):

        # imsave converts images to uint8

        filepath_rgb = self.filepath.split('.')[0] + '_rgb.' + self.filepath.split('.')[1]
        io.imsave(filepath_rgb, self.image_rgb)

        filepath_bin = self.filepath.split('.')[0] + '_bin.' + self.filepath.split('.')[1]
        io.imsave(filepath_bin, img_as_ubyte(self.image_bin))

    # @staticmethod
    # def drawRect(image, start, end):

    #     # rectangle_perimeter generates coordinates of pixels that are exactly around a rectangle
    #     r, c = rectangle_perimeter(start, end=end, shape=image.shape)
        
    #     # image[r, c] = (255, 255, 0)
    #     # or set_color(image, (r,c), (255,255,0))
    #     set_color(image, (r,c), (255, 255, 0))

    
class TextLineImage:

    def __init__(self, start, end):
        self.start = start
        self.end   = end

    def drawPerimeter(self, image):
        r, c = rectangle_perimeter(self.start, end=self.end, shape=image.shape)
        set_color(image, (r, c), (255, 255, 0))
        # image[r, c] = (255, 255, 0)

        