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


class ByteWriter:
    bytes_per_line = 16

    def __init__(self, stream, varname):
        self.stream = stream
        self.stream.write(f"{varname} =\\\n")
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
        self.stream.write(f"\\x{data:02x}")
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
        self.stream.write("\n")


class AltByteWriter(ByteWriter):
    def __init__(self, stream, varname, indent=8):
        self.stream = stream
        self.indent = indent
        self.stream.write(" " * self.indent + f'"{varname}": memoryview(\n')
        self.bytecount = 0  # For line breaks

    def _eol(self):
        self.stream.write('"\n')

    def _eot(self):
        self.stream.write('"\n')
        self.stream.write(" " * self.indent + "),\n")

    def _bol(self):
        self.stream.write(" " * (self.indent + 4) + 'b"')

    def eot(self):  # User force EOL if one hasn't occurred
        if self.bytecount:
            self._eot()
