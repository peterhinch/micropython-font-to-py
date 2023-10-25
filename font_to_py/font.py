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

import freetype

from .bitmap import Bitmap
from .glyph import Glyph

if freetype.version()[0] < 1:
    print("freetype version should be >= 1. Please see FONT_TO_PY.md")


# A Font object is a dictionary of ASCII chars indexed by a character e.g.
# myfont['a']
# Each entry comprises a list
# [0] A Bitmap instance containing the character
# [1] The width of the character data including advance (actual data stored)
# Public attributes:
# height (in pixels) of all characters
# width (in pixels) for monospaced output (advance width of widest char)
class Font(dict):
    def __init__(  # noqa: PLR0913
        self, filename, size, minchar, maxchar, monospaced, defchar, charset, bitmapped
    ):
        super().__init__()
        self._face = freetype.Face(filename)
        # .crange is the inclusive range of ordinal values spanning the character set.
        self.crange = range(minchar, maxchar + 1)
        self.monospaced = monospaced
        self.defchar = defchar
        # .charset has all defined characters with '' for those in range but undefined.
        # Sort order is increasing ordinal value of the character whether defined or not,
        # except that item 0 is the default char.
        if defchar is None:  # Binary font
            self.charset = [chr(ordv) for ordv in self.crange]
        elif charset == "":
            self.charset = [chr(defchar)] + [chr(ordv) for ordv in self.crange]
        else:
            cl = [
                ord(x)
                for x in chr(defchar) + charset
                if self._face.get_char_index(x) != 0
            ]
            self.crange = range(min(cl), max(cl) + 1)  # Inclusive ordinal value range
            cs = [
                chr(ordv)
                if chr(ordv) in charset and self._face.get_char_index(chr(ordv)) != 0
                else ""
                for ordv in self.crange
            ]
            # .charset has an item for all chars in range. '' if unsupported.
            # item 0 is the default char. Subsequent chars are in increasing ordinal value.
            self.charset = [chr(defchar), *cs]
        # Populate self with defined chars only
        self.update(dict.fromkeys([c for c in self.charset if c]))
        self.max_width = (
            self.bmp_dimensions(size) if bitmapped else self.get_dimensions(size)
        )
        self.width = self.max_width if monospaced else 0
        self._assign_values()  # Assign values to existing keys

    def bmp_dimensions(self, height):
        max_descent = 0
        # For each character in the charset string we get the glyph
        # and update the overall dimensions of the resulting bitmap.
        max_width = 0
        max_ascent = 0
        for char in self.keys():
            glyph = self._glyph_for_character(char)
            max_ascent = max(max_ascent, glyph.ascent)
            max_descent = max(max_descent, glyph.descent)
            # for a few chars e.g. _ glyph.width > glyph.advance_width
            max_width = int(max(max_width, glyph.advance_width, glyph.width))

        self.height = int(max_ascent + max_descent)
        self._max_ascent = int(max_ascent)
        self._max_descent = int(max_descent)
        print("Requested height", height)
        print("Actual height", self.height)
        print("Max width", max_width)
        print("Max descent", self._max_descent)
        print("Max ascent", self._max_ascent)
        return max_width

    # n-pass solution to setting a precise height.
    def get_dimensions(self, required_height):
        error = 0
        height = required_height
        npass = 0
        for _ in range(10):
            npass += 1
            height += error
            self._face.set_pixel_sizes(0, height)
            max_descent = 0

            # For each character in the charset string we get the glyph
            # and update the overall dimensions of the resulting bitmap.
            max_width = 0
            max_ascent = 0
            for char in self.keys():
                glyph = self._glyph_for_character(char)
                max_ascent = max(max_ascent, glyph.ascent)
                max_descent = max(max_descent, glyph.descent)
                # for a few chars e.g. _ glyph.width > glyph.advance_width
                max_width = int(max(max_width, glyph.advance_width, glyph.width))

            new_error = required_height - (max_ascent + max_descent)
            if (new_error == 0) or (abs(new_error) - abs(error) == 0):
                break
            error = new_error
        self.height = int(max_ascent + max_descent)
        st = "Height set in {} passes. Actual height {} pixels.\nMax character width {} pixels."
        print(st.format(npass + 1, self.height, max_width))
        self._max_ascent = int(max_ascent)
        self._max_descent = int(max_descent)
        return max_width

    def _glyph_for_character(self, char):
        # Let FreeType load the glyph for the given character and tell it to
        # render a monochromatic bitmap representation.
        assert char != ""
        self._face.load_char(
            char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO
        )
        return Glyph.from_glyphslot(self._face.glyph)

    def _assign_values(self):
        for char in self.keys():
            glyph = self._glyph_for_character(char)
            # https://github.com/peterhinch/micropython-font-to-py/issues/21
            # Handle negative glyph.left correctly (capital J),
            # also glyph.width > advance (capital K and R).
            if glyph.left >= 0:
                char_width = int(max(glyph.advance_width, glyph.width + glyph.left))
                left = glyph.left
            else:
                char_width = int(max(glyph.advance_width - glyph.left, glyph.width))
                left = 0

            width = (
                self.width if self.width else char_width
            )  # Space required if monospaced
            outbuffer = Bitmap(width, self.height)

            # The vertical drawing position should place the glyph
            # on the baseline as intended.
            row = self.height - int(glyph.ascent) - self._max_descent
            outbuffer.bitblt(glyph.bitmap, row, left)
            self[char] = [outbuffer, width, char_width]

    def stream_char(self, char, hmap, reverse):
        outbuffer, _, _ = self[char]
        if hmap:
            gen = outbuffer.get_hbyte(reverse)
        else:
            gen = outbuffer.get_vbyte(reverse)
        yield from gen

    def build_arrays(self, hmap, reverse):
        data = bytearray()
        index = bytearray()
        sparse = bytearray()

        def append_data(data, char):
            width = self[char][1]
            data += (width).to_bytes(2, byteorder="little")
            data += bytearray(self.stream_char(char, hmap, reverse))

        # self.charset is contiguous with chars having ordinal values in the
        # inclusive range specified. Where the specified character set has gaps
        # missing characters are empty strings.
        # Charset includes default char and both max and min chars, hence +2.
        if len(self.charset) <= len(self.crange) + 1:
            # Build normal index. Efficient for ASCII set and smaller as
            # entries are 2 bytes (-> data[0] for absent glyph)
            for char in self.charset:
                if char == "":
                    index += bytearray((0, 0))
                else:
                    index += (len(data)).to_bytes(2, byteorder="little")  # Start
                    append_data(data, char)
            index += (len(data)).to_bytes(2, byteorder="little")  # End
        else:
            # Sparse index. Entries are 4 bytes but only populated if the char
            # has a defined glyph.
            append_data(data, self.charset[0])  # data[0] is the default char
            for char in sorted(self.keys()):
                sparse += ord(char).to_bytes(2, byteorder="little")
                pad = len(data) % 8
                if pad:  # Ensure len(data) % 8 == 0
                    data += bytearray(8 - pad)
                try:
                    sparse += (len(data) >> 3).to_bytes(2, byteorder="little")  # Start
                except OverflowError as err:
                    raise ValueError(
                        "Total size of font bitmap exceeds 524287 bytes."
                    ) from err
                append_data(data, char)
        return data, index, sparse

    def build_binary_array(self, hmap, reverse, sig):
        data = bytearray((0x3F + sig, 0xE7, self.max_width, self.height))
        for char in self.charset:
            width = self[char][2]
            data += bytes((width,))
            data += bytearray(self.stream_char(char, hmap, reverse))
        return data
