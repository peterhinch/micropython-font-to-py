#! /usr/bin/python3
# -*- coding: utf-8 -*-

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

# Test programs for the utility font_to_py and for font files created by it.
# The test of most general use is test_font which enables a string to be
# output to the REPL using a font file created by this utility.

import sys
import os
from importlib import import_module
from font_to_py import Font, write_font

# Utility functions

def validate_hmap(data, height, width):
    bpr = (width - 1)//8 + 1
    msg = 'Horizontal map, invalid data length got {} expected {}'
    assert len(data) == bpr * height, msg.format(len(data), bpr * height)


def validate_vmap(data, height, width):
    bpc = (height - 1)//8 + 1
    msg = 'Vertical map, invalid data length got {} expected {}'
    assert len(data) == bpc * width, msg.format(len(data), bpc * width)


# Routines to render to REPL
def render_row_hmap(data, row, height, width, reverse):
    validate_hmap(data, height, width)
    bytes_per_row = (width - 1)//8 + 1
    for col in range(width):
        byte = data[row * bytes_per_row + col // 8]
        if reverse:
            bit = (byte & (1 << (col % 8))) > 0
        else:
            bit = (byte & (1 << (7 - (col % 8)))) > 0
        char = '#' if bit else '.'
        print(char, end='')


def render_row_vmap(data, row, height, width, reverse):
    validate_vmap(data, height, width)
    bytes_per_col = (height - 1)//8 + 1
    for col in range(width):
        byte = data[col * bytes_per_col + row//8]
        if reverse:
            bit = (byte & (1 << (7 - (row % 8)))) > 0
        else:
            bit = (byte & (1 << (row % 8))) > 0
        char = '#' if bit else '.'
        print(char, end='')


# Render a string to REPL using a specified Python font file
# usage font_test.test_font('freeserif', 'abc')
# Default tests outliers with fonts created with -k extended
def test_font(fontfile, string='abg'+chr(126)+chr(127)+chr(176)+chr(177)+chr(937)+chr(981)):
    if fontfile in sys.modules:
        del sys.modules[fontfile]  # force reload
    myfont = import_module(fontfile)
    print(('Horizontal' if myfont.hmap() else 'Vertical') + ' map')
    print(('Reverse' if myfont.reverse() else 'Normal') + ' bit order')
    print(('Fixed' if myfont.monospaced() else 'Proportional') + ' spacing')
    print('Dimensions height*max_width {} * {}'.format(myfont.height(), myfont.max_width()))
    s, e = myfont.min_ch(), myfont.max_ch()
    print('Start char "{}" (ord {}) end char "{}" (ord {})'.format(chr(s), s, chr(e), e))

    height = myfont.height()
    for row in range(height):
        for char in string:
            data, _, width = myfont.get_ch(char)
            if myfont.hmap():
                render_row_hmap(data, row, height, width, myfont.reverse())
            else:
                render_row_vmap(data, row, height, width, myfont.reverse())
        print()

usage = '''Usage:
./font_test fontfile string
fontfile is a Python font file name with the .py extension omitted.
string is an optional string to render.
If string is omitted a challenging test string will be rendered. This
is for fonts created with -k extended. Other fonts will show "?" for
nonexistent glyphs.
Requires Python 3.2 or newer.
'''

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == '--help':
        print(usage)
    elif len(sys.argv) == 2:
        test_font(sys.argv[1])
    else:
        test_font(sys.argv[1], sys.argv[2])
