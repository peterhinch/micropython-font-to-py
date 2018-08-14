# MicroPython font handling

This repository defines a method of creating and deploying fonts for use with
MicroPython display drivers. A PC utility converts industry standard font files
to Python sourcecode and a MicroPython module enables these to be rendered to
suitable device drivers, notably OLED displays using the SSD1306 chip.

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

This comprises three components:

 1. [font_to_py.py](./FONT_TO_PY.md) This utility runs on a PC and converts a
 font file to Python source. See below.
 2. [The Writer class](./writer/WRITER.md) This facilitates rendering text to a
 device having a suitably designed device driver.
 3. [Device driver notes](./writer/DRIVERS.md). Notes for authors of display
 device drivers. Provides details of the font file format and information on
 ensuring comptibility with the `Writer` classes.

# font_to_py.py

This command line utility is written in Python 3 and runs on a PC. It takes
as input a font file in `ttf` or `otf` form together with a height in pixels
and outputs a Python source file containing the font data. Fixed and variable
pitch rendering are supported. The design has the following aims:

 * Independence of specific display hardware.
 * The path from font file to Python code to be fully open source.

The first is achieved by supplying hardware specific arguments to the utility.
These define horizontal or vertical mapping and the bit order for font data.

The second is achieved by using Freetype and the Freetype Python bindings. Its
use is documented [here](./FONT_TO_PY.md). This also details measurements of
RAM usage when importing fonts stored as frozen bytecode.

# Limitations

By default the ASCII character set from `chr(32)` to `chr(126)` is supported
but command line arguments enable the range to be modified with extended ASCII
characters to `chr(255)` being included if required. Kerning is not supported.
Fonts are one bit per pixel. This does not rule out colour displays: the device
driver can add colour information at the rendering stage. It does assume that
all pixels of a character are rendered identically.

Converting font files programmatically works best for larger fonts. For small
fonts, like the 8*8 default used by the SSD1306 driver, it is best to use
hand-designed binary font files: these are optiised for rendering at a specific
size.

# Font file interface

A font file is imported in the usual way e.g. `import font14`. It contains
the following methods which return values defined by the arguments which were
provided to font-to-py:

`height` Returns height in pixels.  
`max_width` Returns maximum width of a glyph in pixels.  
`hmap` Returns `True` if font is horizontally mapped. Should return `True`  
`reverse` Returns `True` if bit reversal was specified. Should return `False`  
`monospaced` Returns `True` if monospaced rendering was specified.  
`min_ch` Returns the ordinal value of the lowest character in the file.  
`max_ch` Returns the ordinal value of the highest character in the file.

Glyphs are returned with the `get_ch` method. Its argument is a character
and it returns the following values:

 * A `memoryview` object containg the glyph bytes.
 * The height in pixels.
 * The character width in pixels.

# Licence

All code is released under the MIT licence.
