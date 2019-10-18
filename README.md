# MicroPython font handling

This repository defines a method of creating and deploying fonts for use with
MicroPython display drivers. A PC utility renders industry standard font files
as a bitmap in the form of Python sourcecode. A MicroPython module enables such
files to be displayed on devices with suitable device drivers. These include
OLED displays using the SSD1306 chip and the official device driver.

# Introduction

MicroPython platforms generally have limited RAM, but more abundant storage in
the form of flash memory. Font files tend to be relatively large. The
conventional technique of rendering strings to a device involves loading the
entire font into RAM. This is fast but RAM intensive. The alternative of storing
the font as a random access file and loading individual glyphs into RAM on
demand is too slow for reasonable performance on most display devices.

This alternative implements a font as a Python source file, with the data being
declared as `bytes` objects. Such a file may be frozen as bytecode: this
involves building the firmware from source with the Python file in a specific
directory. On import very little RAM is used, yet the data may be accessed
fast. Note that the use of frozen bytecode is entirely optional: font files may
be imported in the normal way if RAM usage is not an issue.

The resultant file is usable with two varieties of display device drivers:

 1. Drivers where the display class is subclassed from the official
 `framebuffer` class.
 2. Drivers for displays where the frame buffer is implemented in the display
 device hardware.

# Solution

This comprises three components, links to docs below:

 1. [font_to_py.py](./FONT_TO_PY.md) This utility runs on a PC and converts a
 font file to Python source. See below.
 2. [Writer and CWriter classes](./writer/WRITER.md) These facilitate rendering
 text to a monochrome or colour display having a suitable device driver.
 3. [Device driver notes](./writer/DRIVERS.md). Notes for authors of display
 device drivers. Provides details of the font file format and information on
 ensuring comptibility with the `Writer` classes.

# font_to_py.py

This command line utility is written in Python 3 and runs on a PC. It takes
as input a font file in `ttf` or `otf` form together with a height in pixels
and outputs a Python source file containing the font as a bitmap. Fixed and
variable pitch rendering are supported. The design has the following aims:

 * Independence of specific display hardware.
 * The path from font file to Python code to be fully open source.

The first is achieved by supplying hardware specific arguments to the utility.
These define horizontal or vertical mapping and the bit order for font data.

The second is achieved by using Freetype and the Freetype Python bindings. Its
use is documented [here](./FONT_TO_PY.md). This also details measurements of
RAM usage when importing fonts stored as frozen bytecode.

# Limitations

Kerning is not supported. Fonts are one bit per pixel. Colour displays are
supported by the `CWriter` class which adds colour information at the rendering
stage. This assumes that all pixels of a character are coloured identically.

Converting font files programmatically works best for larger fonts. For small
fonts, like the 8*8 default used by the SSD1306 driver, it is best to use
hand-designed binary font files: these are optiised for rendering at a specific
size.

By default the `font_to_py.py` utility produces the ASCII character set from
`chr(32)` to `chr(126)` inclusive. Command line options enable the character
set to be modified to include arbitrary Unicode characters. Alternative sets
may be specified such as for non-English languages. Efficient support is now
provided for sparse character sets.

# Font file interface

A font file is imported in the usual way e.g. `import font14`. Python font
files contain the following functions. These return values defined by the
arguments which were provided to `font_to_py.py`:

`height` Returns height in pixels.  
`max_width` Returns maximum width of a glyph in pixels.  
`baseline` Offset from top of glyph to the baseline.  
`hmap` Returns `True` if font is horizontally mapped.  
`reverse` Returns `True` if bit reversal was specified.  
`monospaced` Returns `True` if monospaced rendering was specified.  
`min_ch` Returns the ordinal value of the lowest character in the file.  
`max_ch` Returns the ordinal value of the highest character in the file.

Glyphs are returned with the `get_ch` function. Its argument is a Unicode
character and it returns the following values:

 * A `memoryview` object containing the glyph bytes.
 * The height in pixels.
 * The character width in pixels.

The `font_to_py.py` utility allows a default glyph to be specified (typically
`?`). If called with an undefined character, this glyph will be returned.

The `min_ch` and `max_ch` functions are mainly relevant to contiguous character
sets.

# Licence

All code is released under the MIT licence.
