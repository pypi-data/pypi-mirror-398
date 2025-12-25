from PIL import ImageFont

from nehushtan.paint.Paint import Paint

if __name__ == '__main__':
    # use a truetype font
    font = ImageFont.truetype("/Users/leqee/code/Verbum/fonts/OradanoGSRR.ttf", 50)

    paint = Paint(400, 600, background_color="white")

    paint.rectangle(
        (
            (10, 10),
            (391, 591)
        ),
        outline="red"
    )

    paint.text(
        (50, 50, 200, 100),
        fill="red",
        font=font,
        align="center",
        text="なりすまし"
    )

    paint.show("test2")
