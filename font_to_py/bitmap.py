# Some code adapted from Daniel Bader's work at the following URL
# https://dbader.org/blog/monochrome-font-rendering-with-freetype-and-python
# With thanks to Stephen Irons @ironss for various improvements, also to
# @enigmaniac for ideas around handling `bdf` and `pcf` files.

# The MIT License (MIT)
#
# Copyright (c) 2016-2023 Peter Hinch
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


class Bitmap:
    """
    A 2D bitmap image represented as a list of byte values. Each byte indicates
    the state of a single pixel in the bitmap. A value of 0 indicates that the
    pixel is `off` and any other value indicates that it is `on`.
    """

    def __init__(self, width, height, pixels=None):
        self.width = width
        self.height = height
        self.pixels = pixels or bytearray(width * height)

    def display(self):
        """Print the bitmap's pixels."""
        for row in range(self.height):
            for col in range(self.width):
                char = "#" if self.pixels[row * self.width + col] else "."
                print(char, end="")
            print()
        print()

    def bitblt(self, src, top, left):
        """Copy all pixels from `src` into this bitmap"""
        srcpixel = 0
        dstpixel = top * self.width + left
        row_offset = self.width - src.width

        for _ in range(src.height):
            for _ in range(src.width):
                self.pixels[dstpixel] = src.pixels[srcpixel]
                srcpixel += 1
                dstpixel += 1
            dstpixel += row_offset

    # Horizontal mapping generator function
    def get_hbyte(self, reverse):
        for row in range(self.height):
            col = 0
            while True:
                bit = col % 8
                if bit == 0:
                    if col >= self.width:
                        break
                    byte = 0
                if col < self.width:
                    if reverse:
                        byte |= self.pixels[row * self.width + col] << bit
                    else:
                        # Normal map MSB of byte 0 is (0, 0)
                        byte |= self.pixels[row * self.width + col] << (7 - bit)
                if bit == 7:  # noqa: PLR2004
                    yield byte
                col += 1

    # Vertical mapping
    def get_vbyte(self, reverse):
        for col in range(self.width):
            row = 0
            while True:
                bit = row % 8
                if bit == 0:
                    if row >= self.height:
                        break
                    byte = 0
                if row < self.height:
                    if reverse:
                        byte |= self.pixels[row * self.width + col] << (7 - bit)
                    else:
                        # Normal map MSB of byte 0 is (0, 7)
                        byte |= self.pixels[row * self.width + col] << bit
                if bit == 7:  # noqa: PLR2004
                    yield byte
                row += 1
