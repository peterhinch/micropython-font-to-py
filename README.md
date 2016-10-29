# font_to_py.py

This is a utility written in Python 3 and intended to be run on a PC. It takes
as input a font file in ttf or otf form and a height and outputs a Python
source file containing the font data. The purpose is to enable font files to be
used on microcontrollers running MicroPython: Python source files may be frozen
as bytecode. In this form they can be accessed at speed while using very little
RAM. The design has the following aims:

 * Independence of specific display hardware.
 * The path from font file to Python code to be fully open source.

The first is achieved by supplying hardware specific arguments to the utility.
These define horizontal or vertical mapping and the bit order for font data.

The second is achieved by using Freetype and the Freetype Python bindings.

# Rationale

MicroPython platforms generally have limited RAM, but more abundant storage in
the form of flash memory. Font files tend to be relatively large. The
conventional technique of rendering strings to a device involves loading the
entire font into RAM. This is fast but RAM intensive. The alternative of storing
the font as a random access file and loading individual characters into RAM on
demand is too slow for reasonable performance on most display devices.

This alternative implements a font as a Python source file, with the data being
declared as ``bytes`` objects. Such a file may be frozen as bytecode. On import
very little RAM is used, yet the data may be accessed fast.

It is intended that the resultant file be usable with a variety of display
devices and drivers. These include:

 1. A driver for the official ``framebuffer`` class.
 2. Drivers using ``bytearray`` instances as frame buffers.
 3. Drivers for displays where the frame buffer is implemented in the display
 device hardware.

# Limitations

Only the ASCII character set from ``chr(32)`` to ``chr(126)`` is supported.
Kerning is not supported. Fonts are one bit per pixel. This does not rule out
colour displays: the device driver can add colour information at the rendering
stage. It does assume that all pixels of a character are rendered identically.

# Usage

``font_to_py.py`` is a command line utility written in Python 3. It is run on a
PC. It takes as input a font file with a ``ttf`` or ``otf`` extension and a
required height in pixels and outputs a Python 3 source file. The pixel layout
is determined by command arguments. By default fonts are stored in variable
pitch form. This may be overidden by a command line argument.

Further arguments ensure that the byte contents and layout are correct for the
target display hardware. Their usage should be specified in the documentation
for the device driver.

Example usage to produce a file ``myfont.py`` with height of 23 pixels:  
``font_to_py.py FreeSans.ttf 23 myfont.py``

## Arguments

### Mandatory positional arguments:

 1. Font file path. Must be a ttf or otf file.
 2. Height in pixels.
 3. Output file path. Must have a .py extension.

### Optional arguments:

 * -f or --fixed If specified, all characters will have the same width. By
 default fonts are assumed to be variable pitch.
 * -x Specifies horizontal mapping (default is vertical).
 * -b Specifies bit reversal in each font byte.

Optional arguments other than the fixed pitch argument will be specified in the
device driver documentation. Bit reversal is required by some display hardware.

## The font file

Assume that the you have employed the utility to create a file ``myfont.py``. In
your code you will issue

```python
import myfont
```

The ``myfont`` module name will then be passed to the device driver to render
strings on demand.

# Dependencies, links and licence

The code is released under the MIT licence. It requires Python 3.2 or later.

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

The user program imports a Python font file. When the user program needs to
display a string it passes the module name to the device driver. The module
exposes appropriate font metrics (defined in pixels) and a ``get_ch()``
function. The latter provides fast access to the bytes corresponding to an
individual character together with character specific metrics.

Fixed width characters include blank bits after the character bits to pad out
the width. Variable pitch characters include a small, character specific,
number of blank "advance" bits to provide correct spacing between characters.

## Font files

Assume the user has run the utility to produce a file ``myfont.py`` This then
has the following outline definition (in practice the bytes objects are large):

```python
# Code generated by font-to-py.py.
# Font: FreeSerif.ttf
version = '0.1'

def height():
    return 21

def max_width():
    return 22

def hmap():
    return False

def reverse():
    return False

def monospaced():
    return False

_font =\
b'\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'\
b'\x00\x00\x00\x00\x08\x00\xfe\xc7\x00\x7e\xc0\x00\x00\x00\x00\x00'\

_index =\
b'\x00\x00\x14\x00\x2e\x00\x4b\x00\x71\x00\x97\x00\xd2\x00\x0a\x01'\
b'\x1b\x01\x35\x01\x4f\x01\x75\x01\x9e\x01\xb2\x01\xcc\x01\xe0\x01'\

    # Boilerplate code omitted

def get_ch(ch):
    # validate ch, if out of range use '?'
    # get offset into _font and retrieve char width
    # Return: address of start of bitmap, height and width
    return addressof(_font) + offset + 2, height, width
```

``height`` and ``width`` are specified in bits (pixels).

In the case of monospaced fonts the ``max_width`` function returns the width of
every character. For variable pitch fonts it returns the width of the widest
character. Device drivers can use this to rapidly determine whether a string
will fit the available space. If it will fit on the assumption that all chars
are maximum width, it can be rendered rapidly without doing a character by
character check.

There is a small amount of additional code designed to enable font files to be
tested under cPython: in this instance ``get_ch()`` is called with an optional
``test`` argument and returns a slice rather than a machine address.

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

This general approach has been tested on a Pyboard connected to LCD hardware
having an onboard frame buffer. The visual performance is good.
