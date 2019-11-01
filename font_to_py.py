#! /usr/bin/python3
# -*- coding: utf-8 -*-
# Needs freetype-py>=1.0

# Implements multi-pass solution to setting an exact font height

# Some code adapted from Daniel Bader's work at the following URL
# http://dbader.org/blog/monochrome-font-rendering-with-freetype-and-python
# With thanks to Stephen Irons @ironss for various improvements.

# The MIT License (MIT)
#
# Copyright (c) 2016-2019 Peter Hinch
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

MINCHAR = 32  # Ordinal values of default printable ASCII set
MAXCHAR = 126  # 94 chars

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
    def __init__(self, pixels, width, height, top, left, advance_width):
        self.bitmap = Bitmap(width, height, pixels)

        # The glyph bitmap's top-side bearing, i.e. the vertical distance from
        # the baseline to the bitmap's top-most scanline.
        self.top = top
        self.left = left

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
        left = slot.bitmap_left

        # The advance width is given in FreeType's 26.6 fixed point format,
        # which means that the pixel values are multiples of 64.
        advance_width = slot.advance.x / 64

        return Glyph(pixels, width, height, top, left, advance_width)

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
    def __init__(self, filename, size, minchar, maxchar, monospaced, defchar, charset):
        super().__init__()
        self._face = freetype.Face(filename)
        # .crange is the inclusive range of ordinal values spanning the character set.
        self.crange = range(minchar, maxchar + 1)
        self.monospaced = monospaced
        self.defchar = defchar
        # .charset has all defined characters with '' for those in range but undefined.
        # Sort order is increasing ordinal value of the character whether defined or not,
        # except that item 0 is the default char.
        if defchar is None: # Binary font
            self.charset = [chr(ordv) for ordv in self.crange]
        elif charset == '':
            self.charset = [chr(defchar)] + [chr(ordv) for ordv in self.crange]
        else:
            cl = [ord(x) for x in chr(defchar) + charset if self._face.get_char_index(x) != 0 ]
            self.crange = range(min(cl), max(cl) + 1)  # Inclusive ordinal value range
            cs = [chr(ordv) if chr(ordv) in charset and self._face.get_char_index(chr(ordv)) != 0 else '' for ordv in self.crange]
            # .charset has an item for all chars in range. '' if unsupported.
            # item 0 is the default char. Subsequent chars are in increasing ordinal value.
            self.charset = [chr(defchar)] + cs
        # Populate self with defined chars only
        self.update(dict.fromkeys([c for c in self.charset if c]))
        self.max_width = self.get_dimensions(size)
        self.width = self.max_width if monospaced else 0
        self._assign_values()  # Assign values to existing keys

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
            for char in self.keys():
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
        st = 'Height set in {} passes. Actual height {} pixels.\nMax character width {} pixels.'
        print(st.format(npass + 1, self.height, max_width))
        self._max_ascent = int(max_ascent)
        self._max_descent = int(max_descent)
        return max_width


    def _glyph_for_character(self, char):
        # Let FreeType load the glyph for the given character and tell it to
        # render a monochromatic bitmap representation.
        assert char != ''
        self._face.load_char(char, freetype.FT_LOAD_RENDER |
                             freetype.FT_LOAD_TARGET_MONO)
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

            width = self.width if self.width else char_width  # Space required if monospaced
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
            data += (width).to_bytes(2, byteorder='little')
            data += bytearray(self.stream_char(char, hmap, reverse))

        # self.charset is contiguous with chars having ordinal values in the
        # inclusive range specified. Where the specified character set has gaps
        # missing characters are empty strings.
        # Charset includes default char and both max and min chars, hence +2.
        if len(self.charset) <= MAXCHAR - MINCHAR + 2:
            # Build normal index. Efficient for ASCII set and smaller as
            # entries are 2 bytes (-> data[0] for absent glyph)
            for char in self.charset:
                if char == '':
                    index += bytearray((0, 0))
                else:
                    index += (len(data)).to_bytes(2, byteorder='little')  # Start
                    append_data(data, char)
            index += (len(data)).to_bytes(2, byteorder='little')  # End
        else:
            # Sparse index. Entries are 4 bytes but only populated if the char
            # has a defined glyph.
            append_data(data, self.charset[0])  # data[0] is the default char
            for char in sorted(self.keys()):
                sparse += ord(char).to_bytes(2, byteorder='little')
                sparse += (len(data)).to_bytes(2, byteorder='little')  # Start
                append_data(data, char)
        return data, index, sparse

    def build_binary_array(self, hmap, reverse, sig):
        data = bytearray((0x3f + sig, 0xe7, self.max_width, self.height))
        for char in self.charset:
            width = self[char][2]
            data += bytes((width,))
            data += bytearray(self.stream_char(char, hmap, reverse))
        return data

# PYTHON FILE WRITING
# The index only holds the start of data so can't read next_offset but must
# calculate it.

STR01 = """# Code generated by font_to_py.py.
# Font: {}{}
# Cmd: {}
version = '0.33'

"""

# Code emitted for charsets spanning a small range of ordinal values
STR02 = """_mvfont = memoryview(_font)
_mvi = memoryview(_index)
ifb = lambda l : l[0] | (l[1] << 8)

def get_ch(ch):
    oc = ord(ch)
    ioff = 2 * (oc - {0} + 1) if oc >= {0} and oc <= {1} else 0
    doff = ifb(_mvi[ioff : ])
    width = ifb(_mvfont[doff : ])
"""

# Code emiited for large charsets, assumed by build_arrays() to be sparse.
# Binary search of sorted sparse index.
STRSP = """_mvfont = memoryview(_font)
_mvsp = memoryview(_sparse)
ifb = lambda l : l[0] | (l[1] << 8)

def bs(lst, val):
    while True:
        m = (len(lst) & ~ 7) >> 1
        v = ifb(lst[m:])
        if v == val:
            return ifb(lst[m + 2:])
        if not m:
            return 0
        lst = lst[m:] if v < val else lst[:m]

def get_ch(ch):
    doff = bs(_mvsp, ord(ch))
    width = ifb(_mvfont[doff : ])
"""

# Code emitted for horizontally mapped fonts.
STR02H ="""
    next_offs = doff + 2 + ((width - 1)//8 + 1) * {0}
    return _mvfont[doff + 2:next_offs], {0}, width
 
"""

# Code emitted for vertically mapped fonts.
STR02V ="""
    next_offs = doff + 2 + (({0} - 1)//8 + 1) * width
    return _mvfont[doff + 2:next_offs], {0}, width
 
"""

# Extra code emitted where -i is specified.
STR03 = '''
def glyphs():
    for c in """{}""":
        yield c, get_ch(c)

'''

def write_func(stream, name, arg):
    stream.write('def {}():\n    return {}\n\n'.format(name, arg))

def write_font(op_path, font_path, height, monospaced, hmap, reverse, minchar, maxchar, defchar, charset, iterate):
    try:
        fnt = Font(font_path, height, minchar, maxchar, monospaced, defchar, charset)
    except freetype.ft_errors.FT_Exception:
        print("Can't open", font_path)
        return False
    try:
        with open(op_path, 'w', encoding='utf-8') as stream:
            write_data(stream, fnt, font_path, hmap, reverse, iterate, charset)
    except OSError:
        print("Can't open", op_path, 'for writing')
        return False
    return True

def write_data(stream, fnt, font_path, hmap, reverse, iterate, charset):
    height = fnt.height  # Actual height, not target height
    minchar = min(fnt.crange)
    maxchar = max(fnt.crange)
    defchar = fnt.defchar
    st = '' if charset == '' else ' Char set: {}'.format(charset)
    cl = ' '.join(sys.argv)
    stream.write(STR01.format(os.path.split(font_path)[1], st, cl))
    write_func(stream, 'height', height)
    write_func(stream, 'baseline', fnt._max_ascent)
    write_func(stream, 'max_width', fnt.max_width)
    write_func(stream, 'hmap', hmap)
    write_func(stream, 'reverse', reverse)
    write_func(stream, 'monospaced', fnt.monospaced)
    write_func(stream, 'min_ch', minchar)
    write_func(stream, 'max_ch', maxchar)
    if iterate:
        stream.write(STR03.format(''.join(sorted(fnt.keys()))))
    data, index, sparse = fnt.build_arrays(hmap, reverse)
    bw_font = ByteWriter(stream, '_font')
    bw_font.odata(data)
    bw_font.eot()
    if sparse:  # build_arrays() has returned a sparse index
        bw_sparse = ByteWriter(stream, '_sparse')
        bw_sparse.odata(sparse)
        bw_sparse.eot()
        stream.write(STRSP)
    else:
        bw_index = ByteWriter(stream, '_index')
        bw_index.odata(index)
        bw_index.eot()
        stream.write(STR02.format(minchar, maxchar))
    if hmap:
        stream.write(STR02H.format(height))
    else:
        stream.write(STR02V.format(height))

# BINARY OUTPUT
# hmap reverse magic bytes
# 0    0       0x3f 0xe7
# 1    0       0x40 0xe7
# 0    1       0x41 0xe7
# 1    1       0x42 0xe7
def write_binary_font(op_path, font_path, height, hmap, reverse):
    try:
        fnt = Font(font_path, height, 32, 126, True, None, '')  # All chars have same width
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
    parser.add_argument('-r', '--reverse', action='store_true',
                        help='Bit reversal')
    parser.add_argument('-f', '--fixed', action='store_true',
                        help='Fixed width (monospaced) font')
    parser.add_argument('-b', '--binary', action='store_true',
                        help='Produce binary (random access) font file.')
    parser.add_argument('-i', '--iterate', action='store_true',
                        help='Include generator function to iterate over character set.')

    parser.add_argument('-s', '--smallest',
                        type = int,
                        default = MINCHAR,
                        help = 'Ordinal value of smallest character default %(default)i')

    parser.add_argument('-l', '--largest',
                        type = int,
                        help = 'Ordinal value of largest character default %(default)i',
                        default = MAXCHAR)

    parser.add_argument('-e', '--errchar',
                        type = int,
                        help = 'Ordinal value of error character default %(default)i ("?")',
                        default = 63)

    parser.add_argument('-c', '--charset',
                        type = str,
                        help = 'Character set. e.g. 1234567890: to restrict for a clock display.',
                        default = '')

    parser.add_argument('-k', '--charset_file',
                        type = str,
                        help = 'File containing charset e.g. cyrillic_subset.',
                        default = '')

    args = parser.parse_args()
    if not args.outfile[0].isalpha():
        quit('Font filenames must be valid Python variable names.')

    if not os.path.isfile(args.infile):
        quit("Font filename does not exist")

    if not os.path.splitext(args.infile)[1].upper() in ('.TTF', '.OTF'):
        quit("Font file should be a ttf or otf file.")

    if args.binary:
        if os.path.splitext(args.outfile)[1].upper() == '.PY':
            quit('Binary file must not have a .py extension.')

        if args.smallest != 32 or args.largest != 126 or args.errchar != ord('?') or args.charset:
            quit(BINARY)

        print('Writing binary font file.')
        if not write_binary_font(args.outfile, args.infile, args.height,
                                 args.xmap, args.reverse):
            sys.exit(1)
    else:
        if not os.path.splitext(args.outfile)[1].upper() == '.PY':
            quit('Output filename must have a .py extension.')

        if args.smallest < 0:
            quit('--smallest must be >= 0')

        if args.largest > 255:
            quit('--largest must be < 256')
        elif args.largest > 127 and os.path.splitext(args.infile)[1].upper() == '.TTF':
            print('WARNING: extended ASCII characters may not be correctly converted. See docs.')

        if args.errchar < 0 or args.errchar > 255:
            quit('--errchar must be between 0 and 255')
        if args.charset and (args.smallest != 32 or args.largest != 126):
            print('WARNING: specified smallest and largest values ignored.')

        if args.charset_file:
            try:
                with open(args.charset_file, 'r', encoding='utf-8') as f:
                    cset = f.read()
            except OSError:
                print("Can't open", args.charset_file, 'for reading.')
                sys.exit(1)
        else:
            cset = args.charset
        # dedupe and remove default char. Allow chars in private use area.
        # https://github.com/peterhinch/micropython-font-to-py/issues/22
        cs = {c for c in cset if c.isprintable() or (0xE000 <= ord(c) <= 0xF8FF) } - {args.errchar}
        cs = sorted(list(cs))
        cset = ''.join(cs)  # Back to string
        print('Writing Python font file.')
        if not write_font(args.outfile, args.infile, args.height, args.fixed,
                          args.xmap, args.reverse, args.smallest, args.largest,
                          args.errchar, cset, args.iterate):
            sys.exit(1)

    print(args.outfile, 'written successfully.')

