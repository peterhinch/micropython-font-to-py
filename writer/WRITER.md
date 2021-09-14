# Writer and Cwriter classes

These classes facilitate rendering Python font files to displays where the
display driver is subclassed from the `framebuf` class. Basic support is for
scrolling text display using multiple fonts.

Two cross-platform GUI libraries build on this to provide a variety of widgets.
These are:
 * [nano-gui](https://github.com/peterhinch/micropython-nano-gui) An extremely
 lightweight display-only GUI.
 * [micro-gui](https://github.com/peterhinch/micropython-micro-gui) A GUI
 providing input via either pushbuttons or pushbuttons plus a rotary encoder.

For applications needing only to render text to a display, and optionally to
draw graphics using `FrameBuffer` primitives, the `writer` module may be used
alone.

Example code and images are for 128*64 SSD1306 OLED displays.

![Image](images/IMG_2866.JPG)  
Scrolling text, multiple fonts.

![Image](images/IMG_2861.JPG)  
A field containing variable length text with a border.

![Image](images/rjust.JPG)  
Right justified text.

![Image](images/mixed.JPG)  
Mixed text and graphics.

![Image](images/fields.JPG)  
Labels and Fields (from nanogui.py).

![Image](images/fonts.png)  
The `CWriter` class (from nanogui): `Label` objects in two fonts.  

# Contents

 1. [Introduction](./WRITER.md#1-introduction)  
  1.1 [Release notes](./WRITER.md#11-release-notes)  
  1.2 [Hardware](./WRITER.md#12-hardware)  
  1.3 [Files](./WRITER.md#13-files)  
  1.4 [Fonts](./WRITER.md#14-fonts)  
  1.5 [Supported displays](./WRITER.md#15-supported-displays)  
 2. [Writer and CWriter classes](./WRITER.md#2-writer-and-cwriter-classes)  
  2.1 [The Writer class](./WRITER.md#21-the-writer-class) For monochrome displays.  
   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2.1.1 [Static Method](./WRITER.md#211-static-method)  
   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2.1.2.[Constructor](./WRITER.md#212-constructor)  
   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2.1.3 [Methods](./WRITER.md#213-methods)  
  2.2 [The CWriter class](./WRITER.md#22-the-cwriter-class) For colour displays.  
   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2.2.1 [Constructor](./WRITER.md#221-constructor)  
   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2.2.2 [Methods](./WRITER.md#222-methods)  
  2.3 [Example color code](./WRITER.md#23-example-color-code)  
   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2.2.3 [Performance](./WRITER.md#223-performance) A firmware enhancement for color displays.  
 3. [Icons](./WRITER.md#3-icons) How to render simple icons.  
 4. [Notes](./WRITER.md#4-notes)

###### [Main README](../README.md)

# 1. Introduction

The module provides a `Writer` class for rendering bitmapped monochrome fonts
created by `font_to_py.py`. The `CWriter` class extends this to support color
rendering. Rendering is to a `FrameBuffer` instance, e.g. to a display whose
driver is subclassed from a `FrameBuffer`.

The module has the following features:  
 * Genarality: capable of working with any `framebuf` derived driver.
 * Multiple display operation.
 * Text display of fixed and variable pitch fonts with wrapping and vertical
 scrolling.
 * Wrap/clip options: clip, character wrap or word wrap.
 * Tab support. This is rudimentary and "micro".
 * String metrics to enable right or centre justification.
 * Inverse (background color on foreground color) display.

Note that these changes have significantly increased code size. On the ESP8266
it is likely that `writer.py` will need to be frozen as bytecode. The original
very simple version still exists as `old_versions/writer_minimal.py`.

## 1.1 Release Notes

V0.5.0 Sep 2021  
With the release of firmware V1.17, color display now requires this version.
This enabled the code to be simplified. For old firmware V0.4.3 is available as
`old_versions/writer_fw_compatible.py`.

V0.4.3 Aug 2021  
Supports fast rendering of glyphs to color displays (PR7682). See
[Performance](./WRITER.md#223-performance).

V0.4.0 Jan 2021  
Improved handling of the `col_clip` and `wrap` options. Improved accuracy
avoids needless word wrapping. The clip option now displays as much of the last
visible glyph as possible: formerly a glyph which would not fit in its entirety
was discarded.

The inverted display option has been withdrawn. It added significant code size
and was not an optimal solution. Display inversion should be done at the device
driver level. Such a solution works for graphics objects and GUI widgets, while
the old option only affected rendered text.

## 1.2 Hardware

Tests and demos assume a 128*64 SSD1306 OLED display connected via I2C or SPI.
Wiring is specified in `ssd1306_setup.py`. Edit this to use a different bus or
for a non-Pyboard target. [Section 2.3](./WRITER.md#23-example-color-code)
shows how to drive color displays using the `CWriter` class.

## 1.3 Files

 1. `writer.py` Supports `Writer` and `CWriter` classes.
 2. `ssd1306_setup.py` Hardware initialisation for SSD1306. Requires the
 official [SSD1306 driver](https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py).
 3. `writer_demo.py` Demo using a 128*64 SSD1306 OLED display. Import to see
 usage information.
 4. `writer_tests.py` Test/demo scripts. Import to see usage information.

Sample fonts:
 1. `freesans20.py` Variable pitch font file.
 2. `courier20.py` Fixed pitch font file.
 3. `font10.py` Smaller variable pitch fonts.
 4. `font6.py`

Old versions (in `old_versions` directory):
 1. `writer_minimal.py` A minimal version for highly resource constrained
 devices.
 2. `writer_fw_compatible.py` V0.4.3. Color display will run on firmware
 versions < 1.17.

## 1.4 Fonts

Python font files should be created using `font-to-py.py` using horizontal
mapping (`-x` option). The `-r` option is not required. If RAM is critical
fonts may be frozen as bytecode reducing the RAM impact of each font to about
340 bytes. This is highly recommended.

## 1.5 Supported displays

These include:
 * The official [SSD1306 driver](https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py).
 * The [PCD8544/Nokia 5110](https://github.com/mcauser/micropython-pcd8544.git).

The nano-gui repo includes a growing list of display drivers compatible with
`writer.py`. It may be found in
[the nano-gui docs](https://github.com/peterhinch/micropython-nano-gui/blob/master/README.md#12-description).

Supported technologies are monochrome and color OLED, TFT, ePaper and the Sharp
ultra low power monochrome display.

###### [Contents](./WRITER.md#contents)

# 2. Writer and CWriter classes

The `Writer` class provides fast rendering to monochrome displays using bit
blitting. The `CWriter` class is a subclass of `Writer` to support color
displays which now offers comparable performance (see below).

Multiple screens are supported. On any screen multiple `Writer` or `CWriter`
instances may be used, each using a different font. A class variable holds the
state of each screen to ensure that the insertion point is managed across
multiple instances/fonts.

Former limitations in the `framebuf.blit` method meant it could not be used for
color display. The `CWriter` class therefore rendered glyphs one pixel at a
time in Python which was slow. With current firmware and compatible display
drivers fast C blitting is used. See
[2.2.3](./WRITER.md#223-a-performance-boost).

###### [Contents](./WRITER.md#contents)

## 2.1 The Writer class

This class facilitates rendering characters from Python font files to a device,
assuming the device has a driver subclassed from `framebuf`. It supports three
ways of handling text which would overflow the display: clipping, character
wrapping and simple word wrapping.

It handles newline and tab characters, black-on-white inversion, and field
blanking to enable variable length contents to be updated at a fixed location.

Typical use with an SSD1306 display and the official driver is as follows:

```python
from ssd1306_setup import WIDTH, HEIGHT, setup
from writer import Writer
import freesans20  # Font to use

use_spi=False  # Tested with a 128*64 I2C connected SSD1306 display
ssd = setup(use_spi)  # Instantiate display: must inherit from framebuf
# Demo drawing geometric shapes
rhs = WIDTH -1
ssd.line(rhs - 20, 0, rhs, 20, 1)  # Demo underlying framebuf methods
square_side = 10
ssd.fill_rect(rhs - square_side, 0, square_side, square_side, 1)
# Instantiate a writer for a specific font
wri = Writer(ssd, freesans20)  # verbose = False to suppress console output
Writer.set_textpos(ssd, 0, 0)  # In case a previous test has altered this
wri.printstring('Sunday\n12 Aug 2018\n10.30am')
ssd.show()
```

The file `writer_demo.py` illustrates the use of font files with a 128*64
SSD1306 OLED display and the official
[SSD1306 driver](https://github.com/micropython/micropython/blob/master/drivers/display/ssd1306.py).

### 2.1.1 Static Method

The `Writer` class exposes the following static method:

 1. `set_textpos(device, row=None, col=None)`. The `device` is the display
 instance. This method determines where on screen subsequent text is to be
 rendered. The initial value is (0, 0) - the top left  corner. Arguments are in
 pixels with positive values representing down and right respectively. The
 insertion point defines the top left hand corner of the next character to be
 output.
 
 Where `None` is passed, the setting is left unchanged.  
 Return: `row`, `col` current settings.

 The insertion point applies to all `Writer` instances having the same device.
 The insertion point on a given screen is maintained regardless of the font in
 use.

### 2.1.2 Constructor

This takes the following args:
 1. `device` The hardware device driver instance for the screen in use.
 2. `font` A Python font instance.
 3. `verbose=True` If `True` the constructor emits console printout.

### 2.1.3 Methods

 1. `printstring(string, invert=False)`. Renders the string at the current
 insertion point. Newline and Tab  characters are honoured. If `invert` is
 `True` the text is output with foreground and background colors transposed.
 2. `height()`  Returns the font height in pixels.
 3. `stringlen(string, oh=False)` Returns the length of a string in pixels.
 Appications can use this for right or centre justification.  
 The `oh` arg is for internal use. If set, the method returns a `bool`, `True`
 if the string would overhang the display edge if rendered at the current
 insertion point.
 4. `set_clip(row_clip=None, col_clip=None, wrap=None)`. If `row_clip` and/or
 `col_clip` are `True`, characters will be clipped if they extend beyond the
 boundaries of  the physical display. If `col_clip` is `False` characters will
 wrap onto the next line. If `row_clip` is `False` the display will, where
 necessary,  scroll up to ensure the line is rendered. If `wrap` is `True`
 word-wrapping will be performed, assuming words are separated by spaces.  
 If any arg is `None`, that value will be left unchanged.  
 Returns the current values of `row_clip`, `col_clip` and `wrap`.
 5. `tabsize(value=None)`. If `value` is an integer sets the tab size. Returns
 the current tab size (initial default is 4). Tabs only work properly with
 fixed pitch fonts.

###### [Contents](./WRITER.md#contents)

## 2.2 The CWriter class

This extends the `Writer` class by adding support for color displays. A color
value is an integer whose interpretation is dependent on the display hardware
and device driver. The Python font file uses single bit pixels. On a color
screen these are rendered using foreground and background colors. Display
drivers provide an `rgb` classmethod which converts RGB values to an integer
suitable for the driver. RGB values are integers in range `0 <= c <= 255` (see
example code below).

### 2.2.1 Constructor

This takes the following args:  
 1. `device` The hardware device driver instance for the screen in use.
 2. `font` A Python font instance.
 3. `fgcolor=None` Foreground color. If `None` a monochrome display is assumed.
 4. `bgcolor=None` Background color. If `None` a monochrome display is assumed.
 5. `verbose=True` If `True` the constructor emits console printout.

The constructor checks for suitable firmware and also for a compatible device
driver: an `OSError` is raised if these are absent.

### 2.2.2 Methods

All methods of the base class are supported. Additional method:  
 1. `setcolor(fgcolor=None, bgcolor=None)`. Sets the foreground and background
 colors. If one is `None` that value is left unchanged. If both are `None` the
 constructor defaults are restored. Constructor defaults are 1 and 0
 for monochrome displays (`Writer`). Returns foreground and background color
 values.

The `printstring` method works as per the base class except that the string is
rendered in foreground color on background color (or reversed if `invert` is
`True`).

### 2.2.3 Performance

A firmware change [PR7682](https://github.com/micropython/micropython/pull/7682)
enables a substantial improvement to text rendering speed on color displays.
This was incorporated in firmware V1.17, and `writer.py` requires this or later
if using a color display.

The gain in speed resulting from this firmware change depends on the font size,
increasing for larger fonts. Numbers may be found in `writer.py` code comments.
Typical 10-20 pixel fonts see gains on the order of 5-10 times.

###### [Contents](./WRITER.md#contents)

## 2.3 Example color code

This demo assumes an SSD1351 OLED connected to a Pyboard D. It will need to be
adapted for other hardware. In order to run this, the following files need to
be copied to the host's filesystem:
 * `writer.py`
 * `freesans20.py`
 * The display driver. This must be copied with its directory structure from
 [nano-gui](https://github.com/peterhinch/micropython-nano-gui/tree/master/drivers)
 including the file `drivers/boolpalette.py`. Only the part of the tree relevant
 to the display in use need be copied, in this case `drivers/ssd1351/ssd1351.py`.

```python
import machine
import gc
import time
from writer import CWriter
import freesans20  # Font to use
from drivers.ssd1351.ssd1351 import SSD1351 as SSD  # Adapt for other hardware

# Needed on my Pyboard D PCB to enable supply to the display
pp = machine.Pin('EN_3V3')
pp(1)
time.sleep(1)

# Adafruit options
# height = 96  # 1.27 inch 96*128 (rows*cols) display
height = 128 # 1.5 inch 128*128 display

pdc = machine.Pin('Y12', machine.Pin.OUT_PP, value=0)
pcs = machine.Pin('W32', machine.Pin.OUT_PP, value=1)
prst = machine.Pin('Y11', machine.Pin.OUT_PP, value=1)
spi = machine.SPI(2, baudrate=20_000_000)
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, pcs, pdc, prst, height)  # Create a display instance

# Define a few colors
GREEN = SSD.rgb(0, 255, 0)
RED = SSD.rgb(255,0,0)
BLACK = SSD.rgb(0, 0, 0)

# Demo drawing geometric shapes using underlying framebuf methods
rhs = ssd.width -1
ssd.line(rhs - 20, 0, rhs, 20, GREEN)
square_side = 10
ssd.fill_rect(rhs - square_side, 0, square_side, square_side, GREEN)

# Instantiate a writer for a specific font
wri = CWriter(ssd, freesans20)  # Can set verbose = False to suppress console output
CWriter.set_textpos(ssd, 0, 0)  # In case a previous test has altered this
wri.setcolor(RED, BLACK)  # Colors can be set in constructor or changed dynamically
wri.printstring('Sunday\n12 Aug 2018\n10.30am')
ssd.show()
```

###### [Contents](./WRITER.md#contents)

# 3. Icons

It is possible to create simple icons, for example to create micro-gui
pushbuttons with media playback symbols. Take an arbitrary free font and use a
font editor to replace the glyphs for 'A', 'B', 'C'... with chosen symbols.
Save this modified font under a new name. Then run `font_to_py` to create a
Python font in a chosen size and comprising only those characters (`-c ABCDE`).
Instantiate the buttons with e.g. `text="A"`.

# 4. Notes

Possible future enhancements:
 1. General rendering to a rectangular area. This may be problematic as the
 `framebuf` scroll method is only capable of scrolling the entire buffer.
 2. Extend word wrapping to cases where words are separated by tabs or hyphens.
 3. An asynchronous version. Probably needless now we have fast rendering.

These may conflict too much with the desire to keep the RAM footprint low.
