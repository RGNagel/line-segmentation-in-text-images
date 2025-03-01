import skimage
from skimage.color import rgb2gray, rgba2rgb, gray2rgb
from skimage.util import img_as_ubyte
from skimage.draw import rectangle_perimeter, set_color
from skimage import io

from skimage.filters import rank
from skimage.morphology import disk, square, star, binary_dilation, binary_erosion, binary_opening

import numpy as np

import math

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

        self.image_original = np.copy(image)

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
        
        self.image_bin_dilated = np.array([])
        self.image_bin_dilated_words = np.array([])

        self.rows = self.image_gray.shape[0]
        self.cols = self.image_gray.shape[1]

        self.background_color = self.calcBackgroundColor()

        if self.background_color == self.WHITE:
            self.image_bin = np.invert(self.image_bin)

        self.text_color = self.WHITE
        self.background_color = self.BLACK

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


        if len(self.image_bin_dilated):
            image = self.image_bin_dilated
        else:
            image = self.image_bin

        text_lines = 0
        row_ctr = 0

        # for every pixel row
        for row in range(0, self.rows):

            text_pxs = 0
            background_pxs = 0

            # for every pixel column
            for col in range(0, self.cols):
                if image[row][col] == self.text_color:
                    text_pxs = text_pxs + 1
                else:
                    background_pxs = background_pxs + 1

            # print(text_pxs / self.cols)
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

    def getTextLinesAlternative(self):

        text_lines = 0
        row_ctr = 0

        # for every pixel row
        for row in range(0, self.rows):

            text_pxs = 0
            background_pxs = 0

            col_block_size = int(self.cols / 20)
            col = 0
            lineFoundInBlocks = False
            while (col + col_block_size - 1) < self.cols:
                
                # for each col block
                for c in range(col, col + col_block_size):
                    if self.image_bin[row][c] == self.text_color:
                        text_pxs = text_pxs + 1
                    else:
                        background_pxs = background_pxs + 1

                if text_pxs / col_block_size >= self.threshold_percent_px_cols:
                    row_ctr = row_ctr + 1
                    lineFoundInBlocks = True
                    break
            
                col = col + col_block_size

            if lineFoundInBlocks is False:
                if row_ctr >= self.threshold_qty_px_rows_is_text:
                    text_lines = text_lines + 1
                    self.lines.append(TextLineImage(start=(row - row_ctr, 0), end=(row - 1, self.cols - 1)))
                    row_ctr = 0
                else:
                    row_ctr = 0

            # next pixel row or finished

        return text_lines


    def dilateLines(self):

        kernel         = np.array([np.ones(100)])
        self.image_bin_dilated = binary_dilation(self.image_bin, kernel)


    def dilateWords(self, width=10):
        kernel = np.array([np.ones(width)])
        self.image_bin_dilated_words = binary_dilation(self.image_bin, kernel)


    def getWordsPerLine(self):
        wordsPerLine = []
        for line in self.lines:
            wordsPerLine.append(line.getWords(self))

        return wordsPerLine

    def drawTextLines(self):

        for line in self.lines:
            # red
            line.drawPerimeter(self.image_rgb, color=(255, 0, 0))

    def drawWords(self, color=(0, 255, 0)):


        for line in self.lines:
            # green by default
            line.drawWords(self.image_rgb, color=color)

    def saveImages(self):

        # imsave converts images to uint8

        filepath_rgb = self.filepath.split('.')[0] + '_rgb.' + self.filepath.split('.')[1]
        io.imsave(filepath_rgb, self.image_rgb)

        filepath_bin = self.filepath.split('.')[0] + '_bin.' + self.filepath.split('.')[1]
        io.imsave(filepath_bin, img_as_ubyte(self.image_bin))

        filepath_gray = self.filepath.split('.')[0] + '_gray.' + self.filepath.split('.')[1]
        io.imsave(filepath_gray, img_as_ubyte(self.image_gray))


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

    # if words arr is initialized here, it will be used by all objects instantiated from this class
    
    def __init__(self, start, end):

        super().__init__(start, end)
        
        self.words = []


    def getWords(self, text_image: TextImage):

        if len(text_image.image_bin_dilated_words):
            image = text_image.image_bin_dilated_words
        else:
            image = text_image.image_bin

        text_color       = text_image.text_color
        background_color = text_image.background_color


        if image[0][0].size != 1:
            raise ValueError('image must be one-dimension')

        threshold_percent_px_rows = 0.001
        threshold_qty_px_cols_is_word = 1

        words = 0
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

            elif col_ctr >= threshold_qty_px_cols_is_word:
                words = words + 1
                self.words.append(Rectangle(start=(self.start[0], col - col_ctr),end=(self.end[0], col - 1)))
                col_ctr = 0

        return words

    def drawWords(self, image, color):

        for word in self.words:
            # red
            word.drawPerimeter(image, color)
            