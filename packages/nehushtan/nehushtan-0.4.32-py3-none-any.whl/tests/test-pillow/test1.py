import sys

from PIL import Image, ImageDraw

if __name__ == '__main__':
    image = Image.new("RGB", (100, 200))
    draw = ImageDraw.Draw(image)
    draw.line((0, 0) + image.size, fill=128)
    draw.line((0, image.size[1], image.size[0], 0), fill=128)

    # write to stdout
    image.save(sys.stdout, "PNG")

    image.show("aaa")

    image.close()
