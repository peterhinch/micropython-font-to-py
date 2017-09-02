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
import itertools

# UTILITIES FOR WRITING PYTHON SOURCECODE TO A FILE

# ByteWriter takes as input a variable name and data values and writes
# Python source to an output stream of the form
# my_variable = b'\x01\x02\x03\x04\x05\x06\x07\x08'\

# Lines are broken with \ for readability.


def flatten(l):
    return list(itertools.chain.from_iterable(l))


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


def byte(data, signed=False):
    return data.to_bytes(1, byteorder='little', signed=signed)


def byte_pair(data, signed=False):
    return data.to_bytes(2, byteorder='little', signed=signed)


class Bitmap(object):
    """
    A 2D bitmap image represented as a list of byte values. Each byte indicates
    the state of a single pixel in the bitmap. A value of 0 indicates that the
    pixel is `off` and any other value indicates that it is `on`.
    """
    def __init__(self, char, width, height, pixels=None):
        self.char = char
        self.width = width
        self.height = height
        self.pixels = pixels or bytearray(width * height)
        self.lh_data = []
        self.lv_data = []

    def display(self):
        """Print the bitmap's pixels."""
        for row in range(self.height):
            for col in range(self.width):
                char = '#' if self.pixels[row * self.width + col] else '.'
                print(char, end='')
            print()
        print()

    def display_line_map(self):
        """Print the bitmap's line map."""
        lh_count = len(flatten(self.lh_data))
        print('{} horizontal line mapping: {} hline draw calls. {} bytes'.format(
            self.char,
            lh_count,
            len(list(self._stream_lhmap()))
        ))
        print('v' * len(''.join([str(i) for i in range(self.width)])), '  y [(x, length)]')
        for y in range(self.height):
            for x in range(self.width):
                space = ' ' if x < 10 else '  '
                char = space if self.pixels[y * self.width + x] else x
                print(char, end='')
            print(' ', '%2d' % y, self.lh_data[y])
        print()

        lv_count = len(flatten(self.lv_data))
        print('{} vertical line mapping: {} vline draw calls. {} bytes'.format(
            self.char,
            lv_count,
            len(list(self._stream_lvmap()))
        ))
        print('>' * len(''.join([str(i) for i in range(self.height)])), '  x [(y, length)]')
        for x in range(self.width)[::-1]:
            for y in range(self.height):
                space = ' ' if y < 10 else '  '
                char = space if self.pixels[y * self.width + x] else y
                print(char, end='')
            print(' ', '%2d' % x, self.lv_data[x])
        print()

        print('selecting {} mapping for {} char\n'.format(
            'lhmap horizontal' if self.is_char_lhmap() else 'lvmap vertical',
            self.char
        ))

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

        # calc horizontal line mapping
        for y in range(self.height):
            self.lh_data.append([])
            x = 0
            while x < self.width:
                if self.pixels[y * self.width + x]:
                    line_start = x
                    line_end = x
                    inline_x = x
                    while inline_x <= self.width:
                        if inline_x < self.width and self.pixels[y * self.width + inline_x]:
                            inline_x += 1
                        else:
                            line_end = inline_x
                            break
                    self.lh_data[y].append((line_start, line_end - line_start))
                    x = line_end + 1
                else:
                    x += 1

        # calc vertical line mapping
        for x in range(self.width):
            self.lv_data.append([])
            y = 0
            while y < self.height:
                if self.pixels[y * self.width + x]:
                    line_start = y
                    line_end = y
                    inline_y = y
                    while inline_y <= self.height:
                        if inline_y < self.height and self.pixels[inline_y * self.width + x]:
                            inline_y += 1
                        else:
                            line_end = inline_y
                            break
                    self.lv_data[x].append((line_start, line_end - line_start))
                    y = line_end + 1
                else:
                    y += 1

    def is_char_lhmap(self):
        len_lhmap = len(flatten(self.lh_data))
        len_lvmap = len(flatten(self.lv_data))
        if len_lhmap == len_lvmap:
            return len(list(self._stream_lhmap())) <= len(list(self._stream_lvmap()))
        return len_lhmap <= len_lvmap

    def stream(self):
        if self.is_char_lhmap():
            yield from self._stream_lhmap()
        else:
            yield from self._stream_lvmap()

    def _stream_lhmap(self):
        prev_row = None
        for y, row in enumerate(self.lh_data):
            if not row:
                prev_row = None
                continue
            elif row == prev_row:
                yield byte(0)
            else:
                yield byte(len(row))
                yield byte(y)
                for x, length in row:
                    yield byte(x)
                    yield byte(length)
            prev_row = row

    def _stream_lvmap(self):
        prev_col = None
        for x, col in enumerate(self.lv_data):
            if not col:
                prev_col = None
                continue
            elif col == prev_col:
                yield byte(0)
            else:
                yield byte(len(col))
                yield byte(x)
                for y, length in col:
                    yield byte(y)
                    yield byte(length)
            prev_col = col

    # Horizontal mapping generator function
    def get_hbyte(self, reverse):
        for y in range(self.height):
            x = 0
            while True:
                bit = x % 8
                if bit == 0:
                    if x >= self.width:
                        break
                    byte = 0
                if x < self.width:
                    if reverse:
                        byte |= self.pixels[y * self.width + x] << bit
                    else:
                        # Normal map MSB of byte 0 is (0, 0)
                        byte |= self.pixels[y * self.width + x] << (7 - bit)
                if bit == 7:
                    yield byte
                x += 1

    # Vertical mapping
    def get_vbyte(self, reverse):
        for x in range(self.width):
            y = 0
            while True:
                bit = y % 8
                if bit == 0:
                    if y >= self.height:
                        break
                    byte = 0
                if y < self.height:
                    if reverse:
                        byte |= self.pixels[y * self.width + x] << (7 - bit)
                    else:
                        # Normal map MSB of byte 0 is (0, 7)
                        byte |= self.pixels[y * self.width + x] << bit
                if bit == 7:
                    yield byte
                y += 1


class Glyph(object):
    def __init__(self, char, pixels, width, height, top, advance_width):
        self.bitmap = Bitmap(char, width, height, pixels)

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
    def from_glyphslot(char, slot):
        """Construct and return a Glyph object from a FreeType GlyphSlot."""
        pixels = Glyph.unpack_mono_bitmap(slot.bitmap)
        width, height = slot.bitmap.width, slot.bitmap.rows
        top = slot.bitmap_top

        # The advance width is given in FreeType's 26.6 fixed point format,
        # which means that the pixel values are multiples of 64.
        advance_width = slot.advance.x / 64

        return Glyph(char, pixels, width, height, top, advance_width)

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
    def __init__(self, filename, size, charset, monospaced):
        super().__init__()
        self._glyphs = {}
        self._face = freetype.Face(filename)
        self.charset = charset
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
            max_ascent = 0
            max_descent = 0

            # for whatever wonderful reason, the fonts render differently if we only
            # iterate over self.charset, so instead we use all of extended ASCII, cache
            # the results, and cherry pick the ones we care about afterwards
            for char in [chr(x) for x in range(32, 255)]:
                glyph = self._glyph_for_character(char)
                max_ascent = max(max_ascent, glyph.ascent)
                max_descent = max(max_descent, glyph.descent)
                self._glyphs[char] = {'glyph': glyph,
                                      'width': int(max(glyph.advance_width, glyph.width)),
                                      'ascent': glyph.ascent,
                                      'descent': glyph.descent}

            new_error = required_height - (max_ascent + max_descent)
            if (new_error == 0) or (abs(new_error) - abs(error) == 0):
                break
            error = new_error
        self.height = int(max_ascent + max_descent)

        max_width = 0
        for char in self.charset:
            if self._glyphs[char]['width'] > max_width:
                max_width = self._glyphs[char]['width']

        st = 'Height set in {} passes. Actual height {} pixels.\nMax character width {} pixels.'
        print(st.format(npass + 1, self.height, max_width))
        self._max_descent = int(max_descent)
        return max_width

    def _glyph_for_character(self, char):
        # Let FreeType load the glyph for the given character and tell it to
        # render a monochromatic bitmap representation.
        self._face.load_char(char, freetype.FT_LOAD_RENDER |
                             freetype.FT_LOAD_TARGET_MONO)
        return Glyph.from_glyphslot(char, self._face.glyph)

    def _render_char(self, char):
        glyph = self._glyphs[char]['glyph']
        char_width = int(max(glyph.width, glyph.advance_width))  # Actual width
        width = self.width if self.width else char_width  # Space required if monospaced
        bitmap = Bitmap(char, width, self.height)

        # The vertical drawing position should place the glyph
        # on the baseline as intended.
        row = self.height - int(glyph.ascent) - self._max_descent
        bitmap.bitblt(glyph.bitmap, row)
        self[char] = [bitmap, width, char_width]

    def stream_char(self, char, hmap, reverse):
        bitmap, _, _ = self[char]
        if hmap:
            gen = bitmap.get_hbyte(reverse)
        else:
            gen = bitmap.get_vbyte(reverse)
        yield from gen

    def build_lmap_arrays(self):
        data = bytearray()
        index = bytearray((0, 0))
        for char in self.charset:
            bitmap, width, char_width = self[char]
            data += byte(1 if bitmap.is_char_lhmap() else 0)
            data += byte(width)
            for b in bitmap.stream():
                data += b
            index += byte_pair(len(data))
        return data, index

    def build_arrays(self, hmap, reverse):
        data = bytearray()
        index = bytearray((0, 0))
        for char in self.charset:
            width = self[char][1]
            data += byte_pair(width)
            data += bytearray(self.stream_char(char, hmap, reverse))
            index += byte_pair(len(data))
        return data, index

    def build_binary_array(self, hmap, reverse, sig):
        data = bytearray((0x3f + sig, 0xe7, self.max_width, self.height))
        for char in self.charset:
            width = self[char][2]
            data += bytes((width,))
            data += bytearray(self.stream_char(char, hmap, reverse))
        return data

# PYTHON FILE WRITING

HEADER = """# Code generated by font-to-py.py.
# Font: %(font)s
version = '%(version)s'
"""

HEADER_CHARSET = """# Code generated by font-to-py.py.
# Font: %(font)s
version = '%(version)s'
CHARSET = %(charset)s
"""

FROM_BYTES = """\
def _from_bytes(data):
    return int.from_bytes(data, 'little')
"""

CHAR_BOUNDS = """
def _char_bounds(ch):
    index = ord(ch) - %(minchar)d
    offset = 2 * index
    start = _from_bytes(_index[offset:offset+2])
    next_offset = 2 * (index + 1)
    end = _from_bytes(_index[next_offset:next_offset+2])
    return start, end
"""

CHAR_BOUNDS_CHARSET = """
def _char_bounds(ch):
    index = CHARSET[ch]
    offset = 2 * index
    start = _from_bytes(_index[offset:offset+2])
    next_offset = 2 * (index + 1)
    end = _from_bytes(_index[next_offset:next_offset+2])
    return start, end
"""

GET_CHAR = """
_mvfont = memoryview(_font)

def get_ch(ch):
    start, end = _char_bounds(ch)
    width = _from_bytes(_mvfont[start:start + 2])
    return _mvfont[start + 2:end], %(height)s, width
"""

GET_CHAR_LMAP = """
_mvfont = memoryview(_font)

def get_ch(ch):
    start, end = _char_bounds(ch)
    is_lhmap = _mvfont[start]
    width = _mvfont[start+1]
    return is_lhmap, _mvfont[start + 2:end], %(height)s, width
"""


def write_func(stream, name, arg):
    stream.write('def {}():\n    return {}\n\n'.format(name, arg))


def write_font(op_path, font_path, height, monospaced, hmap, lmap, reverse, charset):
    try:
        fnt = Font(font_path, height, charset, monospaced)
    except freetype.ft_errors.FT_Exception:
        print("Can't open", font_path)
        return False
    try:
        with open(op_path, 'w') as stream:
            write_data(stream, fnt, font_path, monospaced, hmap, lmap, reverse, charset)
    except OSError:
        print("Can't open", op_path, 'for writing')
        return False
    return True


def write_data(stream, fnt, font_path, monospaced, hmap, lmap, reverse, charset):
    height = fnt.height  # Actual height, not target height
    sequential_charset = not bool(len([x for x in range(len(charset) - 1)
                                       if ord(charset[x]) + 1 != ord(charset[x+1])]))
    header_data = {'font': os.path.split(font_path)[1],
                   'charset': {ch: i for i, ch in enumerate(charset)},
                   'version': '0.3' if lmap else '0.2'}
    if sequential_charset:
        stream.write(HEADER % header_data)
    else:
        stream.write(HEADER_CHARSET % header_data)
    stream.write('\n')
    write_func(stream, 'height', height)
    write_func(stream, 'max_width', fnt.max_width)
    write_func(stream, 'hmap', hmap)
    write_func(stream, 'lmap', lmap)
    write_func(stream, 'reverse', reverse)
    write_func(stream, 'monospaced', monospaced)
    if lmap:
        data, index = fnt.build_lmap_arrays()
    else:
        data, index = fnt.build_arrays(hmap, reverse)
    bw_font = ByteWriter(stream, '_font')
    bw_font.odata(data)
    bw_font.eot()
    bw_index = ByteWriter(stream, '_index')
    bw_index.odata(index)
    bw_index.eot()
    stream.write(FROM_BYTES)
    if sequential_charset:
        stream.write(CHAR_BOUNDS % {'minchar': ord(charset[0])})
    else:
        stream.write(CHAR_BOUNDS_CHARSET)
    if lmap:
        stream.write(GET_CHAR_LMAP % {'height': height})
    else:
        stream.write(GET_CHAR % {'height': height})

# BINARY OUTPUT
# hmap reverse magic bytes
# 0    0       0x3f 0xe7
# 1    0       0x40 0xe7
# 0    1       0x41 0xe7
# 1    1       0x42 0xe7
def write_binary_font(op_path, font_path, height, hmap, reverse):
    try:
        fnt = Font(font_path, height, 32, 126, True, None)  # All chars have same width
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

def quit(msg):
    print(msg)
    sys.exit(1)

DESC = """font_to_py.py
Utility to convert ttf or otf font files to Python source.
Sample usage:
font_to_py.py FreeSans.ttf 23 freesans.py

This creates a font with nominal height 23 pixels with these defaults:
Mapping is vertical, pitch variable, character set 32-126 inclusive.
Illegal characters will be rendered as "?".

To specify monospaced rendering issue:
font_to_py.py FreeSans.ttf 23 --fixed freesans.py
"""

BINARY = """Invalid arguments. Binary (random access) font files support the standard ASCII
character set (from 32 to 126 inclusive). This range cannot be overridden.
Random access font files don't support an error character.
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(__file__, description=DESC,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('infile', type=str, help='Input file path')
    parser.add_argument('height', type=int, help='Font height in pixels')
    parser.add_argument('outfile', type=str,
                        help='Path and name of output file')

    parser.add_argument('-x', '--xmap', action='store_true',
                        help='Horizontal (x) mapping')
    parser.add_argument('-L', '--lmap', action='store_true',
                        help='Line mapping')
    parser.add_argument('-r', '--reverse', action='store_true',
                        help='Bit reversal')
    parser.add_argument('-f', '--fixed', action='store_true',
                        help='Fixed width (monospaced) font')
    parser.add_argument('-b', '--binary', action='store_true',
                        help='Produce binary (random access) font file.')

    parser.add_argument('-s', '--smallest',
                        type = int,
                        help = 'Ordinal value of smallest character')

    parser.add_argument('-l', '--largest',
                        type = int,
                        help = 'Ordinal value of largest character')

    parser.add_argument('-c', '--charset',
                        help='List of characters to include in the generated font file',
                        default=[chr(x) for x in range(32, 127)])

    args = parser.parse_args()

    if args.lmap and args.xmap:
        quit('Please select only one of line (L) mapping or horizontal (x) mapping')

    if args.lmap and args.reverse:
        quit('Cannot use bit reversal with line mapping')

    if args.lmap and args.binary:
        raise NotImplementedError

    if not os.path.isfile(args.infile):
        quit("Font filename does not exist")

    if not os.path.splitext(args.infile)[1].upper() in ('.TTF', '.OTF'):
        quit("Font file should be a ttf or otf file.")

    if args.binary:
        if os.path.splitext(args.outfile)[1].upper() == '.PY':
            quit('Binary file must not have a .py extension.')

        if args.smallest != 32 or args.largest != 126 or args.errchar != ord('?'):
            quit(BINARY)

        print('Writing binary font file.')
        if not write_binary_font(args.outfile, args.infile, args.height,
                                 args.xmap, args.reverse):
            sys.exit(1)
    else:
        if not os.path.splitext(args.outfile)[1].upper() == '.PY':
            quit('Output filename must have a .py extension.')

        if args.smallest and args.largest:
            charset = [chr(x) for x in range(args.smallest, args.largest)]
        else:
            charset = args.charset

        print('Writing Python font file.')
        if not write_font(args.outfile, args.infile, args.height, args.fixed,
                          args.xmap, args.lmap, args.reverse, charset):
            sys.exit(1)

    print(args.outfile, 'written successfully.')
