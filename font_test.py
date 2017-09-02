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
def render_bitmapped_string(myfont, string):
    height = myfont.height()
    for row in range(height):
        for char in string:
            data, _, width = myfont.get_ch(char)
            if myfont.hmap():
                render_row_hmap(data, row, height, width, myfont.reverse())
            else:
                render_row_vmap(data, row, height, width, myfont.reverse())
        print()


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


def render_linemapped_string(myfont, string):
    height = myfont.height()
    for row in range(height):
        for char in string:
            is_lhmap, data, _, width = myfont.get_ch(char)
            if is_lhmap:
                render_row_lhmap(data, row, height, width)
            else:
                render_row_lvmap(data, row, height, width)
        print()


def render_row_lhmap(data, row, height, width):
    lines = []
    y = 0
    data_i = 0
    while data_i < len(data):
        num_lines = data[data_i]
        if num_lines:
            y = data[data_i + 1]
            while len(lines) <= y:
                lines.append([])
            for i in range(num_lines):
                lstart = data_i + 2 + (i * 2)
                x = data[lstart]
                length = data[lstart + 1]
                lines[y].append((x, length))
            data_i = lstart + 2
        else:
            lines.append(lines[-1])
            y += 1
            data_i += 1
        if y == row:
            break
    while len(lines) < height:
        lines.append([])

    x = 0
    for line in lines[row]:
        while x < line[0]:
            print('.', end='')
            x += 1
        while x < line[0] + line[1]:
            print('#', end='')
            x += 1
    while x < width:
        print('.', end='')
        x += 1


def render_row_lvmap(data, row, height, width):
    lines = []
    x = 0
    data_i = 0
    while data_i < len(data):
        num_lines = data[data_i]
        if num_lines:
            lines.append([])
            x = data[data_i + 1]
            for i in range(num_lines):
                lstart = data_i + 2 + (i * 2)
                y = data[lstart]
                length = data[lstart + 1]
                lines[x].append((y, length))
            data_i = lstart + 2
        else:
            lines.append(lines[-1])
            x += 1
            data_i += 1
    while len(lines) < width:
        lines.append([])

    for x in range(width):
        char = '.'
        for line in lines[x]:
            if line[0] <= row < line[0] + line[1]:
                char = '#'
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
    charset = 'WM_eg!.,'
    fnt = Font('FreeSans.ttf', 20, charset, False)
    for char in charset:
        fnt[char][0].display()
    print(fnt.width)


# Font character streaming
# Usage font_test.test_stream('abc', 20, False, False, False)
def test_stream(string, height, monospaced, hmap, reverse):
    fnt = Font("FreeSans.ttf", height, string, monospaced)
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
    fnt = Font("FreeSans.ttf", height, string, monospaced)
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

    if myfont.lmap():
        render_linemapped_string(myfont, string)
    else:
        render_bitmapped_string(myfont, string)


# Create font file, render a string to REPL using it
# usage font_test.test_file('FreeSans.ttf', 20, 'xyz')
def test_file(fontfile, height, string, *, minchar=32, maxchar=126, defchar=ord('?'),
              fixed=False, hmap=False, lmap=False, reverse=False):
    charset = [chr(x) for x in range(minchar, maxchar+1)]
    if chr(defchar) not in charset:
        charset += chr(defchar)
    if not write_font('myfont.py', fontfile, height, fixed,
                      hmap, lmap, reverse, charset):
        print('Failed to create font file.')
        return

    if 'myfont' in sys.modules:
        del sys.modules['myfont']  # force reload
    import myfont

    if myfont.lmap():
        render_linemapped_string(myfont, string)
    else:
        render_bitmapped_string(myfont, string)

    os.unlink('myfont.py')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Test font_to_py')
    parser.add_argument('-f', '--font', dest='font',
                        help='Name of a Python font module generated by font_to_py')
    parser.add_argument('-F', '--fontfile', dest='fontfile',
                        help='Path to a TTF font file to test')
    parser.add_argument('-s', '--size', dest='size', default=20)
    parser.add_argument('test_string', nargs='?', default='ABCD.efghij 123!')
    args = parser.parse_args()

    if args.fontfile:
        if not os.path.exists(args.fontfile):
            exit('Sorry, could not find a font file at {}.'.format(args.fontfile))
        print('Running test_file with source font {}:'.format(args.fontfile))
        test_file(args.fontfile, int(args.size), args.test_string)

    elif args.font:
        if '.py' in args.font:
            args.font = args.font[:-3]
        print('Running test_font with py font module {}:'.format(args.font))
        test_font(args.font, args.test_string)
