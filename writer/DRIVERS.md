# Device Driver Implementation

Display devices comprise two varieties, depending on whether the hardware
includes a frame buffer or whether a frame buffer must be located on the
controlling system.

If the device has no frame buffer then the device driver should be designed
to subclass `framebuf.FrameBuffer` with a suitably sized buffer on the host. If
the device has its own frame buffer there are two options for the driver. One
is to perform all display operations using the device's own firmware
primitives. This is efficient and avoids the need for a buffer on the host,
however it does involve some code complexity.

The second option is to subclass `framebuf.FrameBuffer`, provide a buffer on
the host, and copy its contents to the device's buffer when required. This can
result in a very simple device driver at cost of RAM use and update speed. It
also ensures compatibility with additional libraries to simplify display tasks.

If a device subclasses `framebuf.FrameBuffer` the following libraries enhance
its capability. The [Writer](./WRITER.md) class enables it to use multiple
fonts with additional functionality such as word wrap, string metrics and tab
handling. The [nano-gui](https://github.com/peterhinch/micropython-nano-gui.git)
provides rudimentary GUI capability.

If a driver relies on a buffer located on the display device, the means of
controlling the text insertion point, performing partial buffer updates and
executing graphics primitives will be device dependent. If the functionality of
the `writer` or `nanogui` libraries are required it will need to be
implemented at device driver level.

###### [Main README](../README.md)

# Drivers subclassed from framebuf

Where the buffer is held on the MicroPython host the driver should be
subclassed from the official `framebuf.FrameBuffer` class. An example of such a
driver is the [official SSD1306 driver](https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py).
In addition the driver class should have bound variables `width` and `height`
containing the size of the display in pixels, plus a `show` method which copies
the buffer to the physical device.

The device driver defines a buffer of the correct size to hold a full frame of
data and instantiates the `framebuf.FrameBuffer` superclass to reference it.
Monochrome displays should define the frame buffer format to match the physical
characteristics of the display. In the case of colour displays RAM may be saved
by using `framebuf.GS8` 8-bit colour. The `show` method can map this to the
device's colour space if 8-bit mode is not supported.

This design enables the supplied `Writer` and `CWriter` classes to be used for
rendering arbitrary fonts to the display. The author of the device driver need
not be concerned with the format of Python font files.

The `Writer` and `CWriter` classes require horizontally mapped fonts. This is
regardless of the mapping used in the device driver's `FrameBuffer`: the
`Writer.printstring` method deals transparently with any mismatch.

## Example drivers

The following drivers are subclassed from `framebuf.FrameBuffer` and have been
tested with `writer.py` and `nanogui.py`.

 * The [SSD1306 OLED driver](https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py)
 * The [Nokia 5110](https://github.com/mcauser/micropython-pcd8544/blob/master/pcd8544_fb.py)
 * The [SSD1331 colour OLED](https://github.com/peterhinch/micropython-nano-gui/blob/master/drivers/ssd1331/ssd1331.py)

The latter example illustrates a very simple driver which provides full access
to `writer.py` and `nanogui.py` libraries.

# Drivers using the display buffer

Authors of such drivers will need to have an understanding of the font file
format.

## Specifying the font layout

Each font file has a `get_ch()` function accepting a character as its
argument. It returns a memoryview instance providing access to a bytearray
corresponding to the individual glyph. The layout of this data is determined by
the command line arguments presented to the `font_to_py.py` utility. It is
the responsibility of the driver to copy that data to the physical device.

The purpose of the `font_to_py.py` command line arguments specified to the
user is to ensure that the data layout is optimised for the device so that this
copy operation is a fast bytewise copy or SPI/I2C transfer. The driver
documentation should therefore specify these arguments to ensure the layout is
optimal. Mapping may be horizontal or vertical, and the bit order of individual
bytes may be defined. These are detailed below.

In the case of devices with their own frame buffer the `Writer` class will need
to be re-written or adapted to match the hardware's method of tracking such
things as the text insertion point. Consideration should be given to employing
the same interface as the `Writer` class to simplify the porting of user code
between displays with differing hardware.

## Python Font files

Assume the user has run the utility to produce a file `myfont.py` This then
has the following outline definition (in practice the bytes objects are large):

```python
# Code generated by font-to-py.py.
# Font: Arial.ttf
version = '0.25'

def height():
    return 20

def max_width():
    return 20

def hmap():
    return False

def reverse():
    return False

def monospaced():
    return False

def min_ch():
    return 32

def max_ch():
    return 126

_font =\
b'\x0b\x00\x18\x00\x00\x1c\x00\x00\x0e\x00\x00\x06\xce\x00\x06\xcf'\
b'\x00\x86\x03\x00\xce\x01\x00\xfc\x00\x00\x38\x00\x00\x00\x00\x00'\

_index =\
b'\x00\x00\x23\x00\x23\x00\x37\x00\x37\x00\x4b\x00\x4b\x00\x62\x00'\
b'\x62\x00\x85\x00\x85\x00\xa8\x00\xa8\x00\xe0\x00\xe0\x00\x09\x01'\

_mvfont = memoryview(_font)

def get_ch(ch):
    # validate ch, if out of range use '?'
    # get offsets into _font and retrieve char width
    # Return: memoryview of bitmap, height and width
    return mvfont[offset + 2, next_offset], height, width
```

`height` and `width` are specified in bits (pixels). See Appendix 1 for extra
code in fonts created with the `--iterate` arg.

In the case of monospaced fonts the `max_width` function returns the width of
every character. For variable pitch fonts it returns the width of the widest
character. Device drivers can use this to rapidly determine whether a string
will fit the available space. If it will fit on the assumption that all chars
are maximum width, it can be rendered rapidly without doing a character by
character check.

`get_ch()` returns a memoryview of an individual glyph with its dimensions
and contains all the bytes required to render the character including trailing
space.

The `_font` bytearray holds the glyphs corresponding to every character in the
font. Entry 0 is the default glyph, used if an attempt is made to render a
nonexistent character.

The index holds two integers (each occupying 2 bytes) per character. The index
has an entry for every character in the specified range, whether or not that
character exists.

Index entries are offsets into the `_font` bytearray represnting the start and
end of the glyph. If the font comprises a set of characters which is not
contiguous, missing characters have an index entry which points to the first
glyph in the `_font` bytearray. This ensures that the default glyph is
rendered.

## Fixed width fonts

If a Python font file is created with the `-f` argument, all characters will
be saved with the width of the widest. In general it is not necessary to
specify this option. The driver can perform fixed pich rendering by rendering
the character as variable pitch, then blanking and advancing the pixel column
by the value returned by `font.max_width()`.

## Binary font files

This format is unlikely to find application beyond the e-paper driver. It was
designed for micropower applications where the Pyboard has no SD card. Fonts
are stored as random access files on power-switched Flash storage or SD card.
This method is probably too slow for anything other than e-paper displays.

The format is as follows. Files are binary with a four byte header and 126
fixed length records. The header consists of two file identifiers enabling the
file format to be checked, followed by bytes specifying the width and height.
The length of each record is (width + 1) bytes.

The file indentifiers depend on the -x and -r arguments specified to `font_to_py.py`
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

## Mapping (Python and Binary fonts)

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
the case of proportional fonts, and also to facilitate non-contiguous fonts, at
a small cost in performance. The size of the Python source file is a lesser
consideration, with readability being prioritised over size. Hence they are
"pretty formatted" with the large bytes objects split over multiple lines for
readability.

Fonts created with the `font_to_py` utility have been extensively tested with
each of the mapping options. They are used with drivers for SSD1306 OLEDs,
SSD1963 LCD displays, the official LCD160CR and the Digital Artists 2.7 inch
e-paper display.

# Appendix 1. The -i --iterate argument

This specialist arg causes extra code to be included in the font file, to
provide for iterating over all the glyphs in the file. The following sample of
the extra code assumes a font comprising '0123456789:'

```python
def glyphs():
    for c in """0123456789:""":
        yield c, get_ch(c)
```

Typical usage under CPython 3 (for a font `cyrillic.py`) is

```python
import cyrillic
res = []
for glyph in cyrillic.glyphs():
    res.append(list(glyph))  # Each element is [char, glyph, height, width]
```

