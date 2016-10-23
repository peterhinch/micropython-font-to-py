# micropython-font-to-py

This is currently a work in progress. This document specifies a forthcoming
module. Compared to my previous implementations this has the following aims:

 * Independence of specific display hardware.
 * The path from font file to Python code to be fully open source.

# Rationale

MicroPython platforms generally have limited RAM, but more abundant storage in
the form of flash memory. Font files tend to be relatively large. The
conventional technique of rendering strings to a device involves loading the
entire font into RAM. This is fast but ram intensive. The alternative of storing
the font as a random access file and loading individual characters into RAM on
demand is too slow for reasonable performance on most display devices.

This alternative implements a font as a Python source file, with the data being
declared as ``bytes`` objects. Such a file may be frozen as bytecode. On import
very little RAM is used, yet the data may be accessed fast.

It is intended that the resultant file be usable with a variety of display
devices and drivers. These include:

 1. Drivers using the official ``framebuffer`` class.
 2. Drivers using ``bytearray`` instances as frame buffers.
 3. Drivers for devices where the frame buffer is implemented in external
 hardware.

# Limitations

Only the ASCII character set from chr(32) to chr(126) is supported. Kerning is
not supported.

# Usage

``font_to_py.py`` is a command line utility written in Python 3. It is run on a
PC. It takes as input a font file with a ``ttf`` or ``otf`` extension and a
required height in pixels and outputs a Python 3 source file. The pixel layout
is determined by command arguments. Arguments also define whether the font is to
be stored in proportional or fixed width form.

Further arguments ensure that the byte contents and layout are correct for the
target display hardware. Their usage should be defined in the documentation for
the device driver.

Example usage to produce a file ``myfont.py`` with height of 23 pixels:  
``font_to_py.py FreeSans.ttf 23 -o myfont.py``

## Arguments

### Mandatory arguments:

 1. Font file path. Must be a ttf or otf file.
 2. Height in pixels.
 3. -o or --outfile Output file path. Must have a .py extension.

### Optional arguments:

 * -f or --fixed If specified, all characters will have the same width. By
 default fonts are assumed to be variable pitch.
 * -h Specifies horizontal mapping (default is vertical).
 * -b Specifies bit reversal in each font byte.

Optional arguments other than the fixed pitch argument will be specified in the
device driver documentation. Bit reversal is required by some display hardware.

## The font file

Assume that the you have employed the utility to create a file ``myfont.py``. In
your code you will issue

```python
from myfont import myfont
```

The ``myfont`` instance will then be used by the device driver to render strings
on demand.

# Dependencies, links and licence

The code is released under the MIT licence.

The module relies on [Freetype](https://www.freetype.org/) which is included in most Linux distributions.  
It uses the [Freetype Python bindings](http://freetype-py.readthedocs.io/en/latest/index.html)
which will need to be installed.  
My solution draws on the excellent example code written by Daniel Bader. This
may be viewed [here](https://dbader.org/blog/monochrome-font-rendering-with-freetype-and-python) and [here](https://gist.github.com/dbader/5488053).

# Implementation

This section of the README is intended for writers of device drivers.

## Overview

The Python source file produced by ``font_to_py.py`` provides a fast means of
accessing the byte data corresponding to an individual character. It is the
responsibility of the driver to copy that data to the framebuffer or physical
device. The purpose of the command line arguments specified to the user is to
ensure that the data layout is optimised for the device so that the copy is a
simple bytewise copy.

The user program imports a Python font file. This instantiates a ``PyFont``
object with appropriate constructor arguments such as the metrics of the
specific font. When the user program needs to display a string it passes the
instance to the device driver. The instance exposes appropriate font metrics
(defined in pixels) and a ``get_ch()`` method. The latter provides fast access
to the bytes corresponding to an individual character together with character
specific metrics.

Fixed width characters include blank bits after the character bits to pad out
the width. Variable pitch characters include a small number of blank "advance"
bits to provide correct spacing between characters.

## The PyFont class

This is defined in the file ``pyfont.py``. An outline definition of the class is
as follows:

```python
class PyFont(object):
    def __init__(self, font, index, vert, horiz, vmap, revbit):
        self._bits_horiz = horiz     # Width of monospaced char or 0 if variable
        self._bits_vert = vert       # Height of all chars
        self._vmap = vmap            # Vertical map
        self._revbit = revbit        # Bit reversal of font bytes
        self._index = index
        self._font = font

    def get_ch(self, ch):
        from uctypes import addressof
        # Replace out of range characters with a default
        # compute offset of current character bitmap and char width
        return addressof(self._font) + offset, self._bits_vert, char_width

    def get_properties(self):
        return self._bits_vert, self._bits_horiz, self._vmap, self._revbit
```

The device driver calls the ``get_ch`` method for each character in a string.
The ``get_properties`` method enables the driver to validate the Python font
file.

## Font files

Assume the user has run the utility to produce a file ``myfont.py`` This then
has the following outline definition (in practice the bytes objects are large):

```python
import pyfont
_myfont = b'\x00\x00`
_myfont_index = b'\x00\x00\x23\x00\`
myfont = pyfont.PyFont(_myfont, _myfont_index, 24, 0, True, False)

```

## Mapping

A character occupies a space where (0, 0) represents the coordinates of the top
left hand corner of the bitmap. It comprises a set of pixels where increasing x
values represent locations to the right of the origin and increasing y values
represent downward positions. Mapping is the process whereby this two
dimensional array of bits is transformed into a linear sequence of bytes.

Vertical mapping means that the LSB of first byte is pixel (0,0), MSB of first
byte is (0, 7). The second byte (assuming the height is greater than 8 pixels)
is (0, 8) to (0, 15). Once the column is complete the next byte represents
(1, 0) to (1, 7).

Horizontal mapping means that the MSB of byte 0 is pixel (0,0) with LSB at
(7,0), with the second byte covering (8, 0) to (15, 0) if the width is greater
than 8.

Bit reversal provides for the case where the bit order of each byte is reversed
i.e. a byte comprising bits [b7b6b5b4b3b2b1b0] becomes [b0b1b2b3b4b5b6b7].

# Specification Notes

The design aims primarily to minimise RAM usage. Minimising the size of the
bytecode is a secondary aim. Indexed addressing will be used to reduce this in
the case of proportional fonts, at a small cost in performance. The size of the
Python source file is a lesser consideration, with readability being prioritised
over size. Hence they will be "pretty printed" with the large bytes objects
split over multiple lines for readability.

The ``get_ch`` method will determine the character width from the difference
between current and next index values and the font's vertical size: it does not
require explicit storage.

This general approach has been tested on a Pyboard connected to LCD hardware
having an onboard frame buffer. The visual performance is good.
