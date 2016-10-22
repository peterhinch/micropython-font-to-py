# micropython-font-to-py

This is currently a work in progress. This document specifies a forthcoming
module. Compared to my previous implementations this has the following aims:

 * Independence of specific display hardware
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

Further arguments will be specified by the documentation for the specific
device driver in use. They ensure that the byte contents and layout are correct
for the target display hardware.

Example usage to produce a file ``myfont.py`` with height of 23 pixels
``font_to_py.py FreeSans.ttf 23 -o myfont.py``

## Arguments

### Mandatory arguments:

 1. Font file path. Must be a ttf or otf file.
 2. Height in pixels.
 3. -o or --outfile Output file path. Must have a .py extension.

### Optional arguments:

 * -f or --fixedpitch If specified, all characters will have the same width. By
 default fonts are assumed to be variable pitch.
 * -h Specifies horizontal mapping (default is vertical).
 * -b Specifies big-endian bytes (default little endian).
 * -n For variable pitch fonts specifies that blank advance bits should be
 omitted from the character map.

Optional arguments other than the fixed pitch argument will be specified in the
device driver documentation.

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
defined in pixels and a ``get_ch()`` method. The latter provides fast access to
the bytes corresponding to an individual character together with character
specific metrics.

All fixed width characters include blank bits after the character bits to define
the width. By default variable pitch characters include blank "advance" bits to
provide correct spacing between characters. These may optionally be omitted from
the data with the -n argument. In this instance the driver may supply them: the
number of bits to be supplied is stored in byte 1 of the character data.

## The PyFont class

This is defined in the file ``pyfont.py``. An outline definition of the class is
as follows:

```python
class PyFont(object):
    def __init__(self, font, index, vert, horiz):
        self.bits_horiz = horiz     # Width of monospaced char or 0 if variable
        self.bits_vert = vert       # Height of all chars
        self._index = index
        self._font = font

    def get_ch(self, ch):
        from uctypes import addressof
        # Replace out of range characters with a default
        # compute offset of current character bitmap and get char metrics
        return addressof(self._font) + offset, self.bits_vert, char_width, advance)

    def get_properties(self):
        return self.bits_vert, self.bits_horiz
```

The device driver calls the ``get_ch`` method for each character. If the driver
is to provide the advance (user told to use the -n option) the ``advance`` value
is the number of bits to supply. Otherwise its value will be 0.

## Font files

Assume the user has run the utility to produce a file ``myfont.py`` This then
has the following outline definition (in practice the bytes objects are large):

```python
import pyfont
_myfont = b'\x00\x00`
_myfont_index = b'\x00\x00\x23\x00\`
myfont = pyfont.PyFont(_myfont, _myfont_index, 24, 0)

```

# Specification Notes

The design aims primarily to minimise RAM usage. Minimising the size of the
bytecode is a secondary aim. Indexed addressing will be used to reduce this in
the case of proportional fonts, at a small cost in performance. The size of the
Python source file is a lesser consideration, with readability being prioritised
over size. Hence they will be "pretty printed" with the large bytes objects
split over multiple lines for readability.

The bytes object for the font will store the character width in byte 0 and the
advance in byte 1. This will be transparent to the device driver, the pointer
returned by ``get_ch`` will be to the raw font data. This implies that the width
will be restricted to 256 pixels: huge in the context of realistic hardware.

This general approach has been tested on a Pyboard connected to LCD hardware
having an onboard frame buffer. The visual performance is good.
