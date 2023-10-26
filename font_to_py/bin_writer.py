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


import click
import freetype

from .font import Font


# BINARY OUTPUT
# hmap reverse magic bytes
# 0    0       0x3f 0xe7
# 1    0       0x40 0xe7
# 0    1       0x41 0xe7
# 1    1       0x42 0xe7
def write_binary_font(op_path, font_path, height, hmap, reverse):
    try:
        fnt = Font(
            font_path, height, 32, 126, True, None, ""
        )  # All chars have same width
    except freetype.ft_errors.FT_Exception:
        click.echo(f"Can't open {font_path}")
        return False
    sig = 1 if hmap else 0
    if reverse:
        sig += 2
    try:
        with open(op_path, "wb") as stream:
            data = fnt.build_binary_array(hmap, reverse, sig)
            stream.write(data)
    except OSError:
        click.echo(f"Can't open {op_path} for writing")
        return False
    return True
