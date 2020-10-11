import sys
from TextImage import TextImage

assert len(sys.argv) == 2, "Provide only one cli argument: the filepath"

filepath = sys.argv[1]

img_obj = TextImage(filepath)

print("bg color : ", img_obj.background_color)
print("txt color: ", img_obj.text_color)

print("text lines qty: ", img_obj.getTextLines())
img_obj.drawTextLines()

print("chars in each line:", img_obj.getCharsPerLine())
img_obj.drawChars()

img_obj.saveImages()
