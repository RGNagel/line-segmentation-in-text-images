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
        
        # if some coordinates are out of image boundaries,
        # the function does not take into account their 
        # closest coordinates, instead, it just ignores 
        # the out-of-bound coordinates.
        r, c = rectangle_perimeter((1,1), end=(self.rows - 2, self.cols - 2), shape=self.image_gray.shape)

        black_ctr = 0
        white_ctr = 0

        # set_color(self.image_rgb, (r, c), (0,255,0))

        for point in self.image_bin[r, c]:
            
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
                self.lines.append(TextLineImage(start=(row - row_ctr, 0), end=(row - 1, self.cols - 1)))
                row_ctr = 0
            else:
                row_ctr = 0


            # next pixel row or finished

        return text_lines

    def getCharsPerLine(self):
        charsPerLine = []
        for line in self.lines:
            charsPerLine.append(line.getChars(self))

        return charsPerLine

    def drawTextLines(self):

        for line in self.lines:
            # yellow
            line.drawPerimeter(self.image_rgb, color=(255, 255, 0))

    def drawChars(self):

        for line in self.lines:
            # red
            line.drawChars(self.image_rgb, color=(255, 0, 0))

    def saveImages(self):

        # imsave converts images to uint8

        filepath_rgb = self.filepath.split('.')[0] + '_rgb.' + self.filepath.split('.')[1]
        io.imsave(filepath_rgb, self.image_rgb)

        filepath_bin = self.filepath.split('.')[0] + '_bin.' + self.filepath.split('.')[1]
        io.imsave(filepath_bin, img_as_ubyte(self.image_bin))


class Rectangle:

    def __init__(self, start, end):
        self.start = start
        self.end   = end

        self.row_len  = self.end[0] - self.start[0] + 1
        self.col_len  = self.end[1] - self.start[1] + 1

        assert self.row_len > 0, "row length must be greater than 0"
        assert self.col_len > 0, "col length must be greater than 0"


    def drawPerimeter(self, image, color):

        if len(color) != 3:
            raise ValueError("color must be of size 3")

        if image[0][0].size != 3:
            raise ValueError("image must be of size 3")

        r, c = rectangle_perimeter(self.start, end=self.end, shape=image.shape)
        set_color(image, (r, c), color)
        # image[r, c] = (255, 255, 0)


class TextLineImage(Rectangle):

    chars = []

    def getChars(self, text_image: TextImage):

        image            = text_image.image_bin
        text_color       = text_image.text_color
        background_color = text_image.background_color

        if image[0][0].size != 1:
            raise ValueError('image must be one-dimension')

        threshold_percent_px_rows = 0.05
        threshold_qty_px_cols_is_char = 3

        chars = 0
        col_ctr = 0

        for col in range(self.start[1], self.end[1]):

            text_pxs = 0
            background_pxs = 0

            for row in range(self.start[0], self.end[0]):

                if image[row][col] == text_color:
                    text_pxs = text_pxs + 1
                else:
                    background_pxs = background_pxs + 1

            if text_pxs / self.row_len >= threshold_percent_px_rows:
                col_ctr = col_ctr + 1

            elif col_ctr >= threshold_qty_px_cols_is_char:
                chars = chars + 1
                self.chars.append(Rectangle(start=(self.start[0], col - col_ctr),end=(self.end[0], col - 1)))
                col_ctr = 0

        return chars

    def drawChars(self, image, color):

        for char in self.chars:
            # red
            char.drawPerimeter(image, color)
            