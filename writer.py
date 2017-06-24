# writer.py Implements the Writer class.
# V0.2 Peter Hinch Dec 2016

# The MIT License (MIT)
#
# Copyright (c) 2016 Peter Hinch
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

# A Writer supports rendering text to a Display instance in a given font.
# Multiple Writer instances may be created, each rendering a font to the
# same Display object.


class Writer(object):
    # these attributes and set_position are common to all Writer instances
    x_pos = 0
    y_pos = 0
    device = None
    screen_height = 0
    screen_width = 0
    draw_pixel = None

    @classmethod
    def set_position(cls, x, y):
        cls.x_pos = x
        cls.y_pos = y

    def __init__(self, device, font, rotation=None):
        super().__init__()
        self.device = device
        self.set_font(font)
        self.set_rotation(rotation)

    def set_font(self, font):
        self.font = font
        self._draw_char = self._draw_vmap_char
        if font.hmap():
            self._draw_char = self._draw_hmap_char

    @classmethod
    def set_rotation(cls, rotation=None):
        rotation = 0 if not rotation else rotation % 360
        if not rotation:
            cls.draw_pixel = cls._draw_pixel
        elif rotation == 90:
            cls.draw_pixel = cls._draw_pixel_90
        elif rotation == 180:
            cls.draw_pixel = cls._draw_pixel_180
        elif rotation == 270:
            cls.draw_pixel = cls._draw_pixel_270
        else:
            raise ValueError('rotation must be falsy or one of 90, 180 or 270')

        if not rotation or rotation == 180:
            cls.screen_width = cls.device.width
            cls.screen_height = cls.device.height
        else:
            cls.screen_width = cls.device.height
            cls.screen_height = cls.device.width

    def _draw_pixel(self, x, y, color):
        self.device.pixel(x, y, color)

    def _draw_pixel_90(self, x, y, color):
        self.device.pixel(self.device.width - y, x, color)

    def _draw_pixel_180(self, x, y, color):
        self.device.pixel(self.device.width - x, self.device.height - y, color)

    def _draw_pixel_270(self, x, y, color):
        self.device.pixel(y, self.device.height - x, color)

    def _newline(self):
        Writer.x_pos = 0
        Writer.y_pos += self.font.height()

    def draw_text(self, string):
        for char in string:
            self._draw_char(char)

    def _draw_hmap_char(self, char):
        if char == '\n':
            self._newline()
            return

        glyph, char_height, char_width = self.font.get_char(char)

        if Writer.x_pos + char_width > self.screen_width:
            self._newline()

        div, mod = divmod(char_width, 8)
        bytes_per_row = div + 1 if mod else div

        for glyph_row_i in range(char_height):
            glyph_row_start = glyph_row_i * bytes_per_row
            glyph_row = int.from_bytes(
                glyph[glyph_row_start:glyph_row_start + bytes_per_row],
                'little'
            )
            if not glyph_row:
                continue
            x = Writer.x_pos
            y = Writer.y_pos + glyph_row_i
            for glyph_col_i in range(char_width):
                if glyph_row & (1 << glyph_col_i):
                    self.draw_pixel(x, y, 1)
                x += 1

        Writer.x_pos += char_width

    def _draw_vmap_char(self, char):
        if char == '\n':
            self._newline()
            return

        glyph, char_height, char_width = self.font.get_char(char)

        if Writer.x_pos + char_width > self.screen_width:
            self._newline()

        div, mod = divmod(char_height, 8)
        bytes_per_col = div + 1 if mod else div

        for glyph_col_i in range(char_width):
            glyph_col_start = glyph_col_i * bytes_per_col
            glyph_col = int.from_bytes(
                glyph[glyph_col_start:glyph_col_start + bytes_per_col],
                'little'
            )
            if not glyph_col:
                continue
            x = Writer.x_pos + glyph_col_i
            y = Writer.y_pos
            for glyph_row_i in range(char_height):
                if glyph_col & (1 << glyph_row_i):
                    self.draw_pixel(x, y, 1)
                y += 1

        Writer.x_pos += char_width
