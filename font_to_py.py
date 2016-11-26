#! /usr/bin/python3
# -*- coding: utf-8 -*-
# Needs freetype-py>=1.0

# Implements multi-pass solution to setting an exact font height

# Some code adapted from Daniel Bader's work at the following URL
# http://dbader.org/blog/monochrome-font-rendering-with-freetype-and-python

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

import argparse
import sys
import os
import freetype

# UTILITIES FOR WRITING PYTHON SOURCECODE TO A FILE

# ByteWriter takes as input a variable name and data values and writes
# Python source to an output stream of the form
# my_variable = b'\x01\x02\x03\x04\x05\x06\x07\x08'\

# Lines are broken with \ for readability.


class ByteWriter(object):
    bytes_per_line = 16

    def __init__(self, stream, varname):
        self.stream = stream
        self.stream.write('{} =\\\n'.format(varname))
        self.bytecount = 0  # For line breaks

    def _eol(self):
        self.stream.write("'\\\n")

    def _eot(self):
        self.stream.write("'\n")

    def _bol(self):
        self.stream.write("b'")

    # Output a single byte
    def obyte(self, data):
        if not self.bytecount:
            self._bol()
        self.stream.write('\\x{:02x}'.format(data))
        self.bytecount += 1
        self.bytecount %= self.bytes_per_line
        if not self.bytecount:
            self._eol()

    # Output from a sequence
    def odata(self, bytelist):
        for byt in bytelist:
            self.obyte(byt)

    # ensure a correct final line
    def eot(self):  # User force EOL if one hasn't occurred
        if self.bytecount:
            self._eot()
        self.stream.write('\n')


# Define a global
def var_write(stream, name, value):
    stream.write('{} = {}\n'.format(name, value))

# FONT HANDLING


class Bitmap(object):
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
                char = '#' if self.pixels[row * self.width + col] else '.'
                print(char, end='')
            print()
        print()

    def bitblt(self, src, row):
        """Copy all pixels from `src` into this bitmap"""
        srcpixel = 0
        dstpixel = row * self.width
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
                if bit == 7:
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
                if bit == 7:
                    yield byte
                row += 1


class Glyph(object):
    def __init__(self, pixels, width, height, top, advance_width):
        self.bitmap = Bitmap(width, height, pixels)

        # The glyph bitmap's top-side bearing, i.e. the vertical distance from
        # the baseline to the bitmap's top-most scanline.
        self.top = top

        # Ascent and descent determine how many pixels the glyph extends
        # above or below the baseline.
        self.descent = max(0, self.height - self.top)
        self.ascent = max(0, max(self.top, self.height) - self.descent)

        # The advance width determines where to place the next character
        # horizontally, that is, how many pixels we move to the right to
        # draw the next glyph.
        self.advance_width = advance_width

    @property
    def width(self):
        return self.bitmap.width

    @property
    def height(self):
        return self.bitmap.height

    @staticmethod
    def from_glyphslot(slot):
        """Construct and return a Glyph object from a FreeType GlyphSlot."""
        pixels = Glyph.unpack_mono_bitmap(slot.bitmap)
        width, height = slot.bitmap.width, slot.bitmap.rows
        top = slot.bitmap_top

        # The advance width is given in FreeType's 26.6 fixed point format,
        # which means that the pixel values are multiples of 64.
        advance_width = slot.advance.x / 64

        return Glyph(pixels, width, height, top, advance_width)

    @staticmethod
    def unpack_mono_bitmap(bitmap):
        """
        Unpack a freetype FT_LOAD_TARGET_MONO glyph bitmap into a bytearray
        where each pixel is represented by a single byte.
        """
        # Allocate a bytearray of sufficient size to hold the glyph bitmap.
        data = bytearray(bitmap.rows * bitmap.width)

        # Iterate over every byte in the glyph bitmap. Note that we're not
        # iterating over every pixel in the resulting unpacked bitmap --
        # we're iterating over the packed bytes in the input bitmap.
        for row in range(bitmap.rows):
            for byte_index in range(bitmap.pitch):

                # Read the byte that contains the packed pixel data.
                byte_value = bitmap.buffer[row * bitmap.pitch + byte_index]

                # We've processed this many bits (=pixels) so far. This
                # determines where we'll read the next batch of pixels from.
                num_bits_done = byte_index * 8

                # Pre-compute where to write the pixels that we're going
                # to unpack from the current byte in the glyph bitmap.
                rowstart = row * bitmap.width + byte_index * 8

                # Iterate over every bit (=pixel) that's still a part of the
                # output bitmap. Sometimes we're only unpacking a fraction of
                # a byte because glyphs may not always fit on a byte boundary.
                # So we make sure to stop if we unpack past the current row
                # of pixels.
                for bit_index in range(min(8, bitmap.width - num_bits_done)):

                    # Unpack the next pixel from the current glyph byte.
                    bit = byte_value & (1 << (7 - bit_index))

                    # Write the pixel to the output bytearray. We ensure that
                    # `off` pixels have a value of 0 and `on` pixels have a
                    # value of 1.
                    data[rowstart + bit_index] = 1 if bit else 0

        return data


# A Font object is a dictionary of ASCII chars indexed by a character e.g.
# myfont['a']
# Each entry comprises a list
# [0] A Bitmap instance containing the character
# [1] The width of the character data including advance (actual data stored)
# Public attributes:
# height (in pixels) of all characters
# width (in pixels) for monospaced output (advance width of widest char)
class Font(dict):
    charset = [chr(char) for char in range(32, 127)]

    def __init__(self, filename, size, monospaced=False):
        super().__init__()
        self._face = freetype.Face(filename)
        self.max_width = self.get_dimensions(size)
        self.width = self.max_width if monospaced else 0
        for char in self.charset:  # Populate dictionary
            self._render_char(char)

    # n-pass solution to setting a precise height.
    def get_dimensions(self, required_height):
        error = 0
        height = required_height
        for npass in range(10):
            height += error
            self._face.set_pixel_sizes(0, height)
            max_descent = 0

            # For each character in the charset string we get the glyph
            # and update the overall dimensions of the resulting bitmap.
            max_width = 0
            max_ascent = 0
            for char in self.charset:
                glyph = self._glyph_for_character(char)
                max_ascent = max(max_ascent, glyph.ascent)
                max_descent = max(max_descent, glyph.descent)
                # for a few chars e.g. _ glyph.width > glyph.advance_width
                max_width = int(max(max_width, glyph.advance_width,
                                        glyph.width))

            new_error = required_height - (max_ascent + max_descent)
            if (new_error == 0) or (abs(new_error) - abs(error) == 0):
                break
            error = new_error
        self.height = int(max_ascent + max_descent)
        print('Height set in {} passes. Actual height {} pixels'.format(npass + 1, self.height))
        self._max_descent = int(max_descent)
        return max_width


    def _glyph_for_character(self, char):
        # Let FreeType load the glyph for the given character and tell it to
        # render a monochromatic bitmap representation.
        self._face.load_char(char, freetype.FT_LOAD_RENDER |
                             freetype.FT_LOAD_TARGET_MONO)
        return Glyph.from_glyphslot(self._face.glyph)

    def _render_char(self, char):
        glyph = self._glyph_for_character(char)
        char_width = int(max(glyph.width, glyph.advance_width))  # Actual width
        width = self.width if self.width else char_width  # Space required if monospaced
        outbuffer = Bitmap(width, self.height)

        # The vertical drawing position should place the glyph
        # on the baseline as intended.
        row = self.height - int(glyph.ascent) - self._max_descent
        outbuffer.bitblt(glyph.bitmap, row)
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
        index = bytearray((0, 0))
        for char in self.charset:
            width = self[char][1]
            data += (width).to_bytes(2, byteorder='little')
            data += bytearray(self.stream_char(char, hmap, reverse))
            index += (len(data)).to_bytes(2, byteorder='little')
        return data, index

    def build_binary_array(self, hmap, reverse, sig):
        data = bytearray((0x3f + sig, 0xe7, self.max_width, self.height))
        for char in self.charset:
            width = self[char][2]
            data += bytes((width,))
            data += bytearray(self.stream_char(char, hmap, reverse))
        return data

# PYTHON FILE WRITING

STR01 = """# Code generated by font-to-py.py.
# Font: {}
version = '0.1'
"""

STR02 = """_mvfont = memoryview(_font)

def _chr_addr(ordch):
    offset = 2 * (ordch - 32)
    return int.from_bytes(_index[offset:offset + 2], 'little')

def get_ch(ch):
    ordch = ord(ch)
    ordch = ordch if ordch >= 32 and ordch <= 126 else ord('?')
    offset = _chr_addr(ordch)
    width = int.from_bytes(_font[offset:offset + 2], 'little')
    next_offs = _chr_addr(ordch +1)
    return _mvfont[offset + 2:next_offs], {}, width
 
"""

def write_func(stream, name, arg):
    stream.write('def {}():\n    return {}\n\n'.format(name, arg))


def write_font(op_path, font_path, height, monospaced, hmap, reverse):
    try:
        fnt = Font(font_path, height, monospaced)
    except freetype.ft_errors.FT_Exception:
        print("Can't open", font_path)
        return False
    try:
        with open(op_path, 'w') as stream:
            write_data(stream, fnt, font_path, monospaced, hmap, reverse)
    except OSError:
        print("Can't open", op_path, 'for writing')
        return False
    return True


def write_data(stream, fnt, font_path, monospaced, hmap, reverse):
    height = fnt.height  # Actual height, not target height
    stream.write(STR01.format(os.path.split(font_path)[1]))
    stream.write('\n')
    write_func(stream, 'height', height)
    write_func(stream, 'max_width', fnt.max_width)
    write_func(stream, 'hmap', hmap)
    write_func(stream, 'reverse', reverse)
    write_func(stream, 'monospaced', monospaced)
    data, index = fnt.build_arrays(hmap, reverse)
    bw_font = ByteWriter(stream, '_font')
    bw_font.odata(data)
    bw_font.eot()
    bw_index = ByteWriter(stream, '_index')
    bw_index.odata(index)
    bw_index.eot()
    stream.write(STR02.format(height))

# BINARY OUTPUT
# hmap reverse magic bytes
# 0    0       0x3f 0xe7
# 1    0       0x40 0xe7
# 0    1       0x41 0xe7
# 1    1       0x42 0xe7
def write_binary_font(op_path, font_path, height, hmap, reverse):
    try:
        fnt = Font(font_path, height, True)  # All chars have same width
    except freetype.ft_errors.FT_Exception:
        print("Can't open", font_path)
        return False
    sig = 1 if hmap else 0
    if reverse:
        sig += 2
    try:
        with open(op_path, 'wb') as stream:
            data = fnt.build_binary_array(hmap, reverse, sig)
            stream.write(data)
    except OSError:
        print("Can't open", op_path, 'for writing')
        return False
    return True

# PARSE COMMAND LINE ARGUMENTS

DESC = """font_to_py.py
Utility to convert ttf or otf font files to Python source.
Sample usage:
font_to_py.py FreeSans.ttf 23 freesans.py
This creates a font with nominal height 23 pixels. To specify monospaced
rendering issue
font_to_py.py FreeSans.ttf 23 --fixed freesans.py
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(__file__, description=DESC,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('infile', type=str, help='input file path')
    parser.add_argument('height', type=int, help='font height in pixels')
    parser.add_argument('-x', '--xmap', action='store_true',
                        help='horizontal (x) mapping')
    parser.add_argument('-r', '--reverse', action='store_true',
                        help='bit reversal')
    parser.add_argument('-f', '--fixed', action='store_true',
                        help='Fixed width (monospaced) font')
    parser.add_argument('outfile', type=str,
                        help='Path and name of output file')
    args = parser.parse_args()
    if not args.infile[0].isalpha():
        print('Font filenames must be valid Python variable names.')
        sys.exit(1)
    if not os.path.isfile(args.infile):
        print("Font filename does not exist")
        sys.exit(1)
    if not os.path.splitext(args.infile)[1].upper() in ('.TTF', '.OTF'):
        print("Font file should be a ttf or otf file.")
        sys.exit(1)
    if os.path.splitext(args.outfile)[1].upper() == '.PY':  # Emit Python
        if not write_font(args.outfile, args.infile, args.height, args.fixed,
                          args.xmap, args.reverse):
            sys.exit(1)
    else:
        print('WARNING: output filename lacks .py extension. Writing binary font file.')
        if not write_binary_font(args.outfile, args.infile, args.height,
                                 args.xmap, args.reverse):
            sys.exit(1)
    print(args.outfile, 'written successfully.')
