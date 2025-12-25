from typing import Literal

from PIL import Image, ImageFont
from PIL import ImageDraw


class Paint:
    """
    https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html
    """

    def __init__(self, width: int = 400, height: int = 600, mode=None, background_color=None):
        """
        mode: https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes
        """
        if not mode:
            mode = 'RGB'

        self.__image = Image.new(mode, (width, height))

        self.__draw = ImageDraw.Draw(self.__image)

        if background_color is not None:
            self.__draw.rectangle(
                ((0, 0),
                 (width, height)),
                fill=background_color
            )

    def get_image(self):
        return self.__image

    def get_draw_of_image(self):
        return self.__draw

    def arc(self, xy, start, end, fill=None, width=0):
        """
        Draws an arc (a portion of a circle outline) between the start and end angles, inside the given bounding box.

        PARAMETERS:
            xy – Two points to define the bounding box. Sequence of [(x0, y0), (x1, y1)] or [x0, y0, x1, y1], where x1 >= x0 and y1 >= y0.
            start – Starting angle, in degrees. Angles are measured from 3 o’clock, increasing clockwise.
            end – Ending angle, in degrees.
            fill – Color to use for the arc.
            width – The line width, in pixels. New in version 5.3.0.
        """
        self.__draw.arc(xy, start, end, fill, width)

    def chord(self, xy, start, end, fill=None, outline=None, width=1):
        """
        Same as arc(), but connects the end points with a straight line.

        PARAMETERS:
            xy – Two points to define the bounding box. Sequence of [(x0, y0), (x1, y1)] or [x0, y0, x1, y1], where x1 >= x0 and y1 >= y0.
            outline – Color to use for the outline.
            fill – Color to use for the fill.
            width – The line width, in pixels. New in version 5.3.0.
        """
        self.__draw.chord(xy, start, end, fill, outline, width)

    def pieslice(self, xy, start, end, fill=None, outline=None, width=1):
        """
        Same as arc, but also draws straight lines between the end points and the center of the bounding box.

        PARAMETERS:
            xy – Two points to define the bounding box. Sequence of [(x0, y0), (x1, y1)] or [x0, y0, x1, y1], where x1 >= x0 and y1 >= y0.
            start – Starting angle, in degrees. Angles are measured from 3 o’clock, increasing clockwise.
            end – Ending angle, in degrees.
            fill – Color to use for the fill.
            outline – Color to use for the outline.
            width – The line width, in pixels. New in version 5.3.0.
        """
        self.__draw.pieslice(xy, start, end, fill, outline, width)

    def ellipse(self, xy, fill=None, outline=None, width=1):
        """
        Draws an ellipse inside the given bounding box.

        PARAMETERS:
            xy – Two points to define the bounding box. Sequence of either [(x0, y0), (x1, y1)] or [x0, y0, x1, y1], where x1 >= x0 and y1 >= y0.
            outline – Color to use for the outline.
            fill – Color to use for the fill.
            width – The line width, in pixels. New in version 5.3.0.
        """
        self.__draw.ellipse(xy, fill, outline, width)

    def line(self, xy, fill=None, width=0, joint=None):
        """
        Draws a line between the coordinates in the xy list.

        PARAMETERS:
            xy – Sequence of either 2-tuples like [(x, y), (x, y), ...] or numeric values like [x, y, x, y, ...].
            fill – Color to use for the line.
            width – The line width, in pixels.
                New in version 1.1.5.
                Note This option was broken until version 1.1.6.
            joint – Joint type between a sequence of lines. It can be "curve", for rounded edges, or None.
                New in version 5.3.0.
        """
        self.__draw.line(xy, fill, width, joint)

    def point(self, xy, fill=None):
        """
        Draws points (individual pixels) at the given coordinates.

        PARAMETERS:
            xy – Sequence of either 2-tuples like [(x, y), (x, y), ...] or numeric values like [x, y, x, y, ...].
            fill – Color to use for the point.

        """
        self.__draw.point(xy, fill)

    def polygon(self, xy, fill=None, outline=None, width=1):
        """
        Draws a polygon.

        The polygon outline consists of straight lines between the given coordinates, plus a straight line between the last and the first coordinate.

        PARAMETERS:
            xy – Sequence of either 2-tuples like [(x, y), (x, y), ...] or numeric values like [x, y, x, y, ...].
            fill – Color to use for the fill.
            outline – Color to use for the outline.
            width – The line width, in pixels.
        """
        self.__draw.polygon(xy.xy, fill, outline, width)

    def regular_polygon(self, bounding_circle, n_sides, rotation=0, fill=None, outline=None):
        """
        Draws a regular polygon inscribed in bounding_circle, with n_sides, and rotation of rotation degrees.

        PARAMETERS:
            bounding_circle – The bounding circle is a tuple defined by a point and radius. (e.g. bounding_circle=(x, y, r) or ((x, y), r)). The polygon is inscribed in this circle.
            n_sides – Number of sides (e.g. n_sides=3 for a triangle, 6 for a hexagon).
            rotation – Apply an arbitrary rotation to the polygon (e.g. rotation=90, applies a 90 degree rotation).
            fill – Color to use for the fill.
            outline – Color to use for the outline.
        """
        self.__draw.regular_polygon(bounding_circle, n_sides, rotation, fill, outline)

    def rectangle(self, xy, fill=None, outline=None, width=1):
        """
        Draws a rectangle.

        PARAMETERS:
            xy – Two points to define the bounding box. Sequence of either [(x0, y0), (x1, y1)] or [x0, y0, x1, y1]. The second point is just outside the drawn rectangle.
            outline – Color to use for the outline.
            fill – Color to use for the fill.
            width – The line width, in pixels. New in version 5.3.0.
        """
        self.__draw.rectangle(xy, fill, outline, width)

    def rounded_rectangle(self, xy, radius=0, fill=None, outline=None, width=1):
        """
        Draws a rounded rectangle.

        PARAMETERS:
            xy – Two points to define the bounding box. Sequence of either [(x0, y0), (x1, y1)] or [x0, y0, x1, y1]. The second point is just outside the drawn rectangle.
            radius – Radius of the corners.
            outline – Color to use for the outline.
            fill – Color to use for the fill.
            width – The line width, in pixels.

        New in version 8.2.0.
        """
        self.__draw.rounded_rectangle(xy, radius, fill, outline, width)

    def text(self, xy, text, fill=None, font=None, anchor=None, spacing=4,
             align: Literal["left", "center", "right"] = 'left', direction=None, features=None,
             language=None, stroke_width=0, stroke_fill=None, embedded_color=False):
        """
        Draws the string at the given position.

        PARAMETERS:
            xy – The anchor coordinates of the text.
            text – String to be drawn. If it contains any newline characters, the text is passed on to multiline_text().
            fill – Color to use for the text.
            font – An ImageFont instance.
            anchor – The text anchor alignment. Determines the relative location of the anchor to the text. The default alignment is top left. See Text anchors for valid values. This parameter is ignored for non-TrueType fonts.
                Note This parameter was present in earlier versions of Pillow, but implemented only in version 8.0.0.
            spacing – If the text is passed on to multiline_text(), the number of pixels between lines.
            align – If the text is passed on to multiline_text(), "left", "center" or "right". Determines the relative alignment of lines. Use the anchor parameter to specify the alignment to xy.
            direction – Direction of the text. It can be "rtl" (right to left), "ltr" (left to right) or "ttb" (top to bottom). Requires libraqm.
                New in version 4.2.0.
            features – A list of OpenType font features to be used during text layout. This is usually used to turn on optional font features that are not enabled by default, for example "dlig" or "ss01", but can be also used to turn off default font features, for example "-liga" to disable ligatures or "-kern" to disable kerning. To get all supported features, see OpenType docs. Requires libraqm.
                New in version 4.2.0.
            language –  Language of the text. Different languages may use different glyph shapes or ligatures. This parameter tells the font which language the text is in, and to apply the correct substitutions as appropriate, if available. It should be a BCP 47 language code. Requires libraqm.
                New in version 6.0.0.
            stroke_width – The width of the text stroke.
                New in version 6.2.0.
            stroke_fill – Color to use for the text stroke. If not given, will default to the fill parameter.
                New in version 6.2.0.
            embedded_color – Whether to use font embedded color glyphs (COLR, CBDT, SBIX).
                New in version 8.0.0.
        """
        self.__draw.text(xy, text, fill, font, anchor, spacing, align, direction, features, language, stroke_width,
                         stroke_fill, embedded_color)

    def multiline_text(self, xy, text, fill=None, font=None, anchor=None, spacing=4,
                       align: Literal["left", "center", "right"] = 'left', direction=None, features=None, language=None,
                       stroke_width=0, stroke_fill=None, embedded_color=False):
        """
        Draws the string at the given position.

        PARAMETERS:
            xy – The anchor coordinates of the text.
            text – String to be drawn.
            fill – Color to use for the text.
            font – An ImageFont instance.
            anchor – The text anchor alignment. Determines the relative location of the anchor to the text. The default alignment is top left. See Text anchors for valid values. This parameter is ignored for non-TrueType fonts.
                Note This parameter was present in earlier versions of Pillow, but implemented only in version 8.0.0.
            spacing – The number of pixels between lines.
            align – "left", "center" or "right". Determines the relative alignment of lines. Use the anchor parameter to specify the alignment to xy.
            direction – Direction of the text. It can be "rtl" (right to left), "ltr" (left to right) or "ttb" (top to bottom). Requires libraqm.
                New in version 4.2.0.
            features – A list of OpenType font features to be used during text layout. This is usually used to turn on optional font features that are not enabled by default, for example "dlig" or "ss01", but can be also used to turn off default font features, for example "-liga" to disable ligatures or "-kern" to disable kerning. To get all supported features, see OpenType docs. Requires libraqm.
                New in version 4.2.0.
            language – Language of the text. Different languages may use different glyph shapes or ligatures. This parameter tells the font which language the text is in, and to apply the correct substitutions as appropriate, if available. It should be a BCP 47 language code. Requires libraqm.
                New in version 6.0.0.
            stroke_width – The width of the text stroke.
                New in version 6.2.0.
            stroke_fill – Color to use for the text stroke. If not given, will default to the fill parameter.
                New in version 6.2.0.
            embedded_color – Whether to use font embedded color glyphs (COLR, CBDT, SBIX).
                New in version 8.0.0.
        """
        self.__draw.multiline_text(xy, text, fill, font, anchor, spacing, align, direction, features, language,
                                   stroke_width, stroke_fill, embedded_color)

    def textlength(self, text, font=None, direction=None, features=None, language=None, embedded_color=False):
        """
        Returns length (in pixels with 1/64 precision) of given text when rendered in font with provided direction, features, and language.
        This is the amount by which following text should be offset. Text bounding box may extend past the length in some fonts, e.g. when using italics or accents.
        The result is returned as a float; it is a whole number if using basic layout.
        Note that the sum of two lengths may not equal the length of a concatenated string due to kerning. If you need to adjust for kerning, include the following character and subtract its length.

        New in version 8.0.0.

        PARAMETERS:
            text – Text to be measured. May not contain any newline characters.
            font – An ImageFont instance.
            direction – Direction of the text. It can be "rtl" (right to left), "ltr" (left to right) or "ttb" (top to bottom). Requires libraqm.
            features – A list of OpenType font features to be used during text layout. This is usually used to turn on optional font features that are not enabled by default, for example "dlig" or "ss01", but can be also used to turn off default font features, for example "-liga" to disable ligatures or "-kern" to disable kerning. To get all supported features, see OpenType docs. Requires libraqm.
            language – Language of the text. Different languages may use different glyph shapes or ligatures. This parameter tells the font which language the text is in, and to apply the correct substitutions as appropriate, if available. It should be a BCP 47 language code. Requires libraqm.
            embedded_color – Whether to use font embedded color glyphs (COLR, CBDT, SBIX).
        """
        return self.__draw.textlength(text, font, direction, features, language, embedded_color)

    def textbbox(self, xy, text, font=None, anchor=None, spacing=4, align: Literal["left", "center", "right"] = 'left',
                 direction=None, features=None, language=None, stroke_width=0, embedded_color=False):
        """
        Returns bounding box (in pixels) of given text relative to given anchor when rendered in font with provided direction, features, and language. Only supported for TrueType fonts.

        Use textlength() to get the offset of following text with 1/64 pixel precision. The bounding box includes extra margins for some fonts, e.g. italics or accents.

        New in version 8.0.0.

        PARAMETERS:
            xy – The anchor coordinates of the text.
            text – Text to be measured. If it contains any newline characters, the text is passed on to multiline_textbbox().
            font – A FreeTypeFont instance.
            anchor – The text anchor alignment. Determines the relative location of the anchor to the text. The default alignment is top left. See Text anchors for valid values. This parameter is ignored for non-TrueType fonts.
            spacing – If the text is passed on to multiline_textbbox(), the number of pixels between lines.
            align – If the text is passed on to multiline_textbbox(), "left", "center" or "right". Determines the relative alignment of lines. Use the anchor parameter to specify the alignment to xy.
            direction – Direction of the text. It can be "rtl" (right to left), "ltr" (left to right) or "ttb" (top to bottom). Requires libraqm.
            features – A list of OpenType font features to be used during text layout. This is usually used to turn on optional font features that are not enabled by default, for example "dlig" or "ss01", but can be also used to turn off default font features, for example "-liga" to disable ligatures or "-kern" to disable kerning. To get all supported features, see OpenType docs. Requires libraqm.
            language – Language of the text. Different languages may use different glyph shapes or ligatures. This parameter tells the font which language the text is in, and to apply the correct substitutions as appropriate, if available. It should be a BCP 47 language code. Requires libraqm.
            stroke_width – The width of the text stroke.
            embedded_color – Whether to use font embedded color glyphs (COLR, CBDT, SBIX).
        """
        return self.__draw.textbbox(xy, text, font, anchor, spacing, align, direction, features, language, stroke_width,
                                    embedded_color)

    def multiline_textbbox(self, xy, text, font=None, anchor=None, spacing=4,
                           align: Literal["left", "center", "right"] = 'left', direction=None, features=None,
                           language=None, stroke_width=0, embedded_color=False):
        """
        Returns bounding box (in pixels) of given text relative to given anchor when rendered in font with provided direction, features, and language. Only supported for TrueType fonts.

        Use textlength() to get the offset of following text with 1/64 pixel precision. The bounding box includes extra margins for some fonts, e.g. italics or accents.

        New in version 8.0.0.

        PARAMETERS:
            xy – The anchor coordinates of the text.
            text – Text to be measured.
            font – A FreeTypeFont instance.
            anchor – The text anchor alignment. Determines the relative location of the anchor to the text. The default alignment is top left. See Text anchors for valid values. This parameter is ignored for non-TrueType fonts.
            spacing – The number of pixels between lines.
            align – "left", "center" or "right". Determines the relative alignment of lines. Use the anchor parameter to specify the alignment to xy.
            direction – Direction of the text. It can be "rtl" (right to left), "ltr" (left to right) or "ttb" (top to bottom). Requires libraqm.
            features – A list of OpenType font features to be used during text layout. This is usually used to turn on optional font features that are not enabled by default, for example "dlig" or "ss01", but can be also used to turn off default font features, for example "-liga" to disable ligatures or "-kern" to disable kerning. To get all supported features, see OpenType docs. Requires libraqm.
            language – Language of the text. Different languages may use different glyph shapes or ligatures. This parameter tells the font which language the text is in, and to apply the correct substitutions as appropriate, if available. It should be a BCP 47 language code. Requires libraqm.
            stroke_width – The width of the text stroke.
            embedded_color – Whether to use font embedded color glyphs (COLR, CBDT, SBIX).
        """
        return self.__draw.multiline_textbbox(xy, text, font, anchor, spacing, align, direction, features, language,
                                              stroke_width, embedded_color)

    def save(self, fp, the_format=None, **params):
        """
        Saves this image under the given filename. If no format is specified, the format to use is determined from the filename extension, if possible.

        Keyword options can be used to provide additional instructions to the writer. If a writer doesn’t recognise an option, it is silently ignored. The available options are described in the image format documentation for each writer.

        You can use a file object instead of a filename. In this case, you must always specify the format. The file object must implement the seek, tell, and write methods, and be opened in binary mode.

        PARAMETERS:
            fp – A filename (string), pathlib.Path object or file object.
            format – Optional format override. If omitted, the format to use is determined from the filename extension. If a file object was used instead of a filename, this parameter should always be used.
            params – Extra parameters to the image writer.

        RETURNS: None

        RAISES:
            ValueError – If the output format could not be determined from the file name. Use the format option to solve this.
            OSError – If the file could not be written. The file may have been created, and may contain partial data.
        """
        self.__image.save(fp, the_format, **params)

    def show(self, title: str = None):
        """
        Displays this image. This method is mainly intended for debugging purposes.

        This method calls PIL.ImageShow.show() internally. You can use PIL.ImageShow.register() to override its default behaviour.

        The image is first saved to a temporary file. By default, it will be in PNG format.

        On Unix, the image is then opened using the display, eog or xv utility, depending on which one can be found.

        On macOS, the image is opened with the native Preview application.

        On Windows, the image is opened with the standard PNG display utility.

        PARAMETERS:
            title – Optional title to use for the image window, where possible.
        """
        self.__image.show(title)

    def close(self):
        self.__image.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def load_ttf_font(ttf_font_file_path: str, size: int):
        # use a truetype font
        return ImageFont.truetype(ttf_font_file_path, size)
