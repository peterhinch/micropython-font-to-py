# DRIVERS.md

This document comprises two sections, the first for users of an existing device
driver and the second for writers of device drivers.

# User Documentation: the Writer class

This class facilitates rendering characters from Python font files to a device,
assuming the device has a driver conforming to the specification below. Typical
use is as follows:

```python
from writer import Writer
from device_driver import Display
import freeserif
import freesans20
display = Display(args_required_by_driver)
wri_serif = Writer(display, freeserif)
wri_sans = Writer(display, freesans20)
Writer.set_clip(True, True)
wri_serif.printstring('Tuesday\n')
wri_sans.printstring('8 Nov 2016\n')
wri_sans.printstring('10.30am')

display.show()  # Display the result
```

The file ``driver_test.py`` illustrates the use of font files with an SSD1306
display and a complete example of an SSD1306 driver may be found 
[here](https://github.com/peterhinch/micropython-samples/tree/master/SSD1306).

## Class Methods

The ``Writer`` class exposes the following class methods:

 1. ``set_textpos`` Args: ``row``, ``col``. This determines where on screen any
 subsequent text is to be rendered. The initial value is (0, 0) - the top left
 corner. Arguments are in pixels with positive values representing down and
 right respectively. They reference the top left hand corner of the first
 character to be output.
 2. ``set_clip`` Args: boolean ``row_clip``, ``col_clip``. If these are
 ``True``, characters will be clipped if they extend beyond the boundaries of
 the physical display. If ``col_clip`` is ``False`` characters will wrap onto
 the next line. If ``row_clip`` is ``False`` the display will, where necessary,
 scroll up to ensure the line is rendered.
 3. ``mapping`` Arg: an integer. This defines the mapping of bytes in the
 buffer onto pixels. The module exposes three constants for use here: ``VERT``
 ``HORIZ`` and ``WEIRD``, the latter being specific to the official SSD1306
 driver. ``VERT`` is for true vertically mapped displays. ``HORIZ``, for
 horizontally mapped devices, is currently unsupported. By default the mapping
 is for SSD1306 devices using the official driver.

As class methods these settings apply to all font objects. The insertion point
of characters is maintained regardless of the font in use.

## Method

 1. ``printstring`` Arg: a text string. Outputs a text string at the current
 insertion point. Newline characters are honoured.

## Note on the Writer class

This is more a proof of concept than a final implementation. Obvious
enhancements include rendering to a rectangular area, support for proper word
wrap and support for format control characters such as tabs.

# Device Driver Implementation

Display devices comprise two varieties, depending on whether the framebuffer is
located on the controlling system or on the physical display device. In the
former case the ``Writer`` class simplifies the design of the driver. It merely
has to expose certin attributes and methods with ``Writer`` instances taking
care of text rendering. It is strongly recommended that such device drivers use
the oficial ``framebuf`` module, as per the official SSD1306 driver which
exposes the required components.

Where the buffer is located on the display device the means of controlling the
text insertion point will be device dependent. The driver will need to
implement the functionality of the ``Writer`` class itself.

## Fixed width fonts

If a Python font file is created with the ``-f`` argument, all characters will
be saved with the width of the widest. In general it is not necessary to
specify this option. The driver can perform fixed pich rendering by rendering
the character as variable pitch, then advancing the pixel column by the value
returned by ``font.max_width()``.

## Drivers with local buffers

The writer of a device driver need not be concerned with the structure of a
Python font file so long as the driver exposes certain attributes and methods
required by the ``Writer`` class. These are as follows:

Attributes:

 1. ``buffer`` The underlying ``bytearray`` instance holding the display
 buffer.
 2. ``height`` The screen height in pixels.
 3. ``width`` The screen width in pixels.

Methods:

 1. ``show`` Display the current buffer contents.
 2. ``scroll`` Arguments ``x``, ``y`` amount to scroll horizontal and vertical.
 3. ``fill`` Argument ``col`` colour 1 == fill 0 == clear.

An example of such a driver, using the official ``framebuf`` module, is the
SSD1306 driver (drivers/display/ssd1306.py in the source tree).

The driver documentation should specify the arguments for font_to_py.py to
ensure users create font files with a layout corresponding to that of the
buffer/device.

## Drivers for remote buffers

### Specifying the font file

Each font file has a ``get_ch()`` function accepting an ASCII character as its
argument. It returns a memoryview instance providing access to a bytearray
corresponding to the individual glyph. The layout of this data is determined by
the command line arguments presented to the ``font_to_py.py`` utility. It is
the responsibility of the driver to copy that data to the physical device.

The purpose of the ``font_to_py.py`` command line arguments specified to the
user is to ensure that the data layout is optimised for the device so that this
copy operation is a fast bytewise copy or SPI/I2C transfer. The driver
documentation should therefore specify these arguments to ensure the layout is
optimal. Mapping may be horizontal or vertical, and the bit order of individual
bytes may be defined. These are detailed below.

In the case of devices with their own frame buffer the ``Writer`` class will need
to be re-written or adapted to match the hardware's method of tracking such
things as the text insertion point. Consideration should be given to employing
the same interface as the ``Writer`` class to simplify the porting of user code
between displays with differing hardware.

## Python Font files

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
    # get offsets into _font and retrieve char width
    # Return: memoryview of bitmap, height and width
    return memoryview(_font[offset + 2, next_offset]), height, width
```

``height`` and ``width`` are specified in bits (pixels).

In the case of monospaced fonts the ``max_width`` function returns the width of
every character. For variable pitch fonts it returns the width of the widest
character. Device drivers can use this to rapidly determine whether a string
will fit the available space. If it will fit on the assumption that all chars
are maximum width, it can be rendered rapidly without doing a character by
character check.

``get_ch()`` returns a memoryview of an individual glyph with its dimensions
and contains all the bytes required to render the character including trailing
space.

## Binary font files

These are unlikely to find application beyond the e-paper driver, but for
completeness the format is as follows. They are binary files with a four byte
header and 126 fixed length records. The header consists of two file identifiers
enabling the file format to be checked, followed by bytes specifying the width
and height. The length of each record is (width + 1) bytes.

The file indentifiers depend on the -x and -r arguments specified to ``font_to_py.py``
and are as follows:

hmap reverse byte  
-x   -r      0    1  
0    0       0x3f 0xe7  
1    0       0x40 0xe7  
0    1       0x41 0xe7  
1    1       0x42 0xe7  

Each record starts with a width byte specifying the x dimension of the glyph if
rendered proportionally spaced, followed by the glyph data. This data includes
trailing space ensuring that all records have the size specified in the header.

## Mapping

A character occupies a space where (0, 0) represents the coordinates of the top
left hand corner of the bitmap. It comprises a set of pixels where increasing x
values represent locations to the right of the origin and increasing y values
represent downward positions. Mapping defines the relationship between this
abstract two dimensional array of bits and the physical linear sequence of bytes.

Vertical mapping means that the LSB of first byte is pixel (0,0), MSB of first
byte is (0, 7). The second byte (assuming the height is greater than 8 pixels)
is (0, 8) to (0, 15). Once the column is complete the next byte represents
(1, 0) to (1, 7).

Horizontal mapping means that the MSB of byte 0 is pixel (0,0) with LSB at
(7,0), with the second byte covering (8, 0) to (15, 0) if the width is greater
than 8.

Bit reversal provides for the case where the bit order of each byte is reversed
i.e. a byte comprising bits [b7b6b5b4b3b2b1b0] becomes [b0b1b2b3b4b5b6b7].

# Specification and Project Notes

The design aims primarily to minimise RAM usage. Minimising the size of the
bytecode is a secondary aim. Indexed addressing is used to reduce this in
the case of proportional fonts, at a small cost in performance. The size of the
Python source file is a lesser consideration, with readability being prioritised
over size. Hence they are "pretty formatted" with the large bytes objects
split over multiple lines for readability.

The approach has been tested on SSD1306 devices using both the pseudo-horizontal
and true vertical mapping.

The ``font_to_py`` utility has been extensively tested with each of the mapping
options. It has been used with drivers for SSD1306 OLEDs, SSD1963 LCD displays,
and the e-paper display.
