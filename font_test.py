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
    msg = 'Horizontal map, invalid data length'
    assert len(data) == bpr * height, msg


def validate_vmap(data, height, width):
    bpc = (height - 1)//8 + 1
    msg = 'Vertical map, invalid data length'
    assert len(data) == bpc * width, msg


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


def display(data, hmap, height, width, reverse):
    bpr = (width - 1)//8 + 1
    bpc = (height - 1)//8 + 1
    print('Height: {} Width: {}'.format(height, width))
    print('Bytes/row: {} Bytes/col: {}'.format(bpr, bpc))
    print('Data length: {}'.format(len(data)))
    # Check bytearray is the correct length
    if hmap:
        validate_hmap(data, height, width)
    else:
        validate_vmap(data, height, width)

    for row in range(height):
        if hmap:
            render_row_hmap(data, row, height, width, reverse)
        else:
            render_row_vmap(data, row, height, width, reverse)
        print()


# TESTS: in order of code coverage
# Basic test of Font class functionality
# Usage font_test.font_test()
def font_test():
    fnt = Font('FreeSans.ttf', 20)
    for char in 'WM_eg!.,':
        fnt[char][0].display()
    print(fnt.width)

# Font character streaming
# Usage font_test.test_stream('abc', 20, False, False, False)
def test_stream(string, height, monospaced, hmap, reverse):
    fnt = Font("FreeSans.ttf", height, monospaced)
    height = fnt.height
    for char in string:
        width = fnt[char][1]
        data = bytearray(fnt.stream_char(char, hmap, reverse))
        display(data, hmap, height, width, reverse)


def chr_addr(index, ordch):
    offset = 2 * (ordch - 32)
    return int.from_bytes(index[offset:offset + 2], 'little')


# Font.build_arrays
# Usage font_test.test_arrays('abc', 20, False, False, False)
def test_arrays(string, height, monospaced, hmap, reverse):
    fnt = Font("FreeSans.ttf", height, monospaced)
    height = fnt.height
    data, index = fnt.build_arrays(hmap, reverse)
    for char in string:
        ordch = ord(char)
        offset = chr_addr(index, ordch)
        width = int.from_bytes(data[offset:offset + 2], 'little')
        offset += 2
        next_offs = chr_addr(index, ordch + 1)
        display(data[offset:next_offs], hmap, height, width, reverse)


# Render a string to REPL using a specified Python font file
# usage font_test.test_font('freeserif', 'abc')
def test_font(fontfile, string):
    if fontfile in sys.modules:
        del sys.modules[fontfile]  # force reload
    myfont = import_module(fontfile)

    height = myfont.height()
    for row in range(height):
        for char in string:
            data, _, width = myfont.get_char(char)
            if myfont.hmap():
                render_row_hmap(data, row, height, width, myfont.reverse())
            else:
                render_row_vmap(data, row, height, width, myfont.reverse())
        print()


# Create font file, render a string to REPL using it
# usage font_test.test_file('FreeSans.ttf', 20, 'xyz')
def test_file(fontfile, height, string, *, minchar=32, maxchar=126, defchar=ord('?'),
              fixed=False, hmap=False, reverse=False):
    if not write_font('myfont.py', fontfile, height, fixed,
                      hmap, reverse, minchar, maxchar, defchar):
        print('Failed to create font file.')
        return

    if 'myfont' in sys.modules:
        del sys.modules['myfont']  # force reload
    import myfont

    height = myfont.height()
    for row in range(height):
        for char in string:
            data, _, width = myfont.get_char(char)
            if myfont.hmap():
                render_row_hmap(data, row, height, width, myfont.reverse())
            else:
                render_row_vmap(data, row, height, width, myfont.reverse())
        print()
    os.unlink('myfont.py')
