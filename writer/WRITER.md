# Writer and Cwriter classes

These classes facilitate rendering Python font files to displays where the
display driver is subclassed from the `framebuf` class. Basic support is for
scrolling text display using multiple fonts. There is a growing list of
displays with compatible drivers, see

### [Supported displays document](https://github.com/peterhinch/micropython-nano-gui/blob/master/DISPLAYS.md)

Three cross-platform GUI libraries build on this to provide a variety of widgets.
These are:
 * [nano-gui](https://github.com/peterhinch/micropython-nano-gui) An extremely
 lightweight display-only GUI.
 * [micro-gui](https://github.com/peterhinch/micropython-micro-gui) A GUI
 providing input via either pushbuttons or pushbuttons plus a rotary encoder.
 * [micropython-touch](https://github.com/peterhinch/micropython-touch) Input
 is provided by touch.

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
 2. [Writer and CWriter classes](./WRITER.md#2-writer-and-cwriter-classes)  
  2.1 [The Writer class](./WRITER.md#21-the-writer-class) For monochrome displays.  
   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2.1.1 [Static Method](./WRITER.md#211-static-method)  
   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2.1.2.[Constructor](./WRITER.md#212-constructor)  
   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2.1.3 [Methods](./WRITER.md#213-methods)  
  2.2 [The CWriter class](./WRITER.md#22-the-cwriter-class) For colour displays.  
   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2.2.1 [Static Method](./WRITER.md#221-static-method)  
   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2.2.2 [Constructor](./WRITER.md#222-constructor)  
   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2.2.3 [Methods](./WRITER.md#223-methods)  
  2.3 [Example color code](./WRITER.md#23-example-color-code) For most display drivers.  
  2.4 [Use with 4 bit drivers](./WRITER.md#24-use-with-4-bit-drivers) Color definition uses a different technique.  
 3. [Icons](./WRITER.md#3-icons) How to render simple icons.  

###### [Main README](../README.md)

# 1. Introduction

The module provides a `Writer` class for rendering bitmapped monochrome fonts
created by `font_to_py.py`. The `CWriter` class extends this to support color
rendering. Rendering is to a `FrameBuffer` instance, e.g. to a display whose
driver is subclassed from a `FrameBuffer`.

The module has the following features:  
 * Generality: `Writer` can work with any `framebuf` derived driver.
 * Multiple display operation.
 * Text display of fixed and variable pitch fonts with wrapping and vertical
 scrolling.
 * Wrap/clip options: clip, character wrap or word wrap.
 * Tab support. This is rudimentary and "micro".
 * String metrics to enable right or centre justification.
 * Inverse (background color on foreground color) display.

The `CWriter` class requires a compatible display driver. These are listed
[in this document](https://github.com/peterhinch/micropython-nano-gui/blob/master/DISPLAYS.md).
There is no support for RTL languages but a workround is discussed
[here](../charsets/RTL_languages.md).

## 1.1 Release Notes

V0.5.1 Dec 2022__
Add support for 4 bit color display drivers.
V0.5.0 Sep 2021  
Requires firmware V1.17 or later.

V0.4.3 Aug 2021  
Supports fast rendering of glyphs to color displays (PR7682).

V0.4.0 Jan 2021  
Improved handling of the `col_clip` and `wrap` options. Improved accuracy
avoids needless word wrapping. The clip option now displays as much of the last
visible glyph as possible: formerly a glyph which would not fit in its entirety
was discarded.

## 1.2 Hardware

Tests and demos assume a 128*64 SSD1306 OLED display connected via I2C or SPI.
Wiring is specified in `ssd1306_setup.py`. Edit this to use a different bus or
for a non-Pyboard target. [Section 2.3](./WRITER.md#23-example-color-code)
shows how to drive color displays using the `CWriter` class.

## 1.3 Files

 1. `writer.py` Supports `Writer` and `CWriter` classes.
 2. `ssd1306_setup.py` Hardware initialisation for SSD1306. Requires the
 official [SSD1306 driver](https://github.com/micropython/micropython-lib/tree/master/micropython/drivers/display/ssd1306).
 3. `writer_demo.py` Demo using a 128*64 SSD1306 OLED display. Import to see
 usage information.
 4. `writer_tests.py` Test/demo scripts. Import to see usage information.

Sample fonts:
 1. `freesans20.py` Variable pitch font file.
 2. `courier20.py` Fixed pitch font file.
 3. `font10.py` Smaller variable pitch fonts.
 4. `font6.py`

## 1.4 Fonts

Python font files should be created using `font-to-py.py` using horizontal
mapping; this is the default. The `-r` option is not required. If RAM is critical
fonts may be frozen as bytecode reducing the RAM impact of each font to about
340 bytes. This is highly recommended.

###### [Contents](./WRITER.md#contents)

# 2. Writer and CWriter classes

The `Writer` class provides fast rendering to monochrome displays using bit
blitting. The `CWriter` class is a subclass of `Writer` to support color
displays which offers comparable performance.

Multiple screens are supported. On any screen multiple `Writer` or `CWriter`
instances may be used, each using a different font. A class variable holds the
state of each screen to ensure that the insertion point is managed across
multiple instances/fonts.

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
[SSD1306 driver](https://github.com/micropython/micropython-lib/tree/master/micropython/drivers/display/ssd1306).

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

### 2.2.1 Static method

The `CWriter` class has one static method `create_color`. This is exclusively
for use with 4 bit color display drivers. It populates the driver's color
lookup table. Args:
 1. `ssd` The display instance.
 2. `idx` Color number in range 0 <= idx <= 15. These are arbitrary but by
 convention 0 is black and 15 white.
 3. `r` Red value. Values are in range 0 <= red <= 255.
 4. `g` Green value.
 5. `b` Blue value.

The return value is the `idx` value, hence a color can be defined as
```python
GREEN = CWriter.create_color(ssd, 1, 0, 255, 0)
```

### 2.2.2 Constructor

This takes the following args:  
 1. `device` The hardware device driver instance for the screen in use.
 2. `font` A Python font instance.
 3. `fgcolor=None` Foreground color. If `None` a monochrome display is assumed.
 4. `bgcolor=None` Background color. If `None` a monochrome display is assumed.
 5. `verbose=True` If `True` the constructor emits console printout.

The constructor checks for suitable firmware and also for a compatible device
driver: an `OSError` is raised if these are absent.

### 2.2.3 Methods

All methods of the base class are supported. Additional method:  
 1. `setcolor(fgcolor=None, bgcolor=None)`. Sets the foreground and background
 colors. If one is `None` that value is left unchanged. If both are `None` the
 constructor defaults are restored. Constructor defaults are 1 and 0
 for monochrome displays (`Writer`). Returns foreground and background color
 values.

The `printstring` method works as per the base class except that the string is
rendered in foreground color on background color (or reversed if `invert` is
`True`).

###### [Contents](./WRITER.md#contents)

## 2.3 Example color code

The following will not work with 4-bit drivers: see [section 2.4](./WRITER.md#24-use-with-4-bit-drivers).

This demo assumes an SSD1351 OLED connected to a Pyboard D. It will need to be
adapted for other hardware. In order to run this, the following files need to
be copied to the host's filesystem:
 * `writer.py`
 * `freesans20.py`
 * The display driver. This should be installed as per
 [this document](https://github.com/peterhinch/micropython-nano-gui/blob/master/DRIVERS.md#12-installation)
 to ensure the correct directory structure.

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

# Define a few colors (for 4-bit drivers this is done differently)
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
## 2.4 Use with 4 bit drivers

Some color display drivers for larger displays use 4-bit colors: this achieves
a substantial reduction in the size of the frame buffer at the cost of limiting
the number of colors that can be displayed. The driver expands the colors at
run time using a lookup table.

This means that colors must be defined using the `create_color` static method
described above.
```python
from machine import SPI, Pin
from writer import CWriter
import freesans20  # Font to use
from drivers.ili93xx.ili9341 import ILI9341 as SSD

spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4), baudrate=30_000_000)
dc = Pin(8, Pin.OUT, value=0)
cs = Pin(10, Pin.OUT, value=1)
rst = Pin(9, Pin.OUT, value=1)
ssd = SSD(spi, cs, dc, rst)

# Define a few colors: populates the lookup table
BLACK = CWriter.create_color(ssd, 0, 0, 0, 0)
GREEN = CWriter.create_color(ssd, 1, 0, 255, 0)
RED = CWriter.create_color(ssd, 2, 255, 0, 0)
YELLOW = CWriter.create_color(ssd, 3, 255, 255, 0)
# Demo drawing geometric shapes using underlying framebuf methods
rhs = ssd.width -1
ssd.line(rhs - 20, 0, rhs, 20, GREEN)
square_side = 10
ssd.fill_rect(rhs - square_side, 0, square_side, square_side, GREEN)

# Instantiate a writer for a specific font
wri = CWriter(ssd, freesans20)  # Can set verbose = False to suppress console output
CWriter.set_textpos(ssd, 0, 0)  # In case a previous test has altered this
wri.setcolor(RED, BLACK)  # Colors can be set in constructor or changed dynamically
wri.printstring('Tuesday\n6th December 2020\n10.30am\n')
wri.setcolor(YELLOW, BLACK)
wri.printstring('Running on a 4-bit driver.')
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

Alternatively icons can be created as bitmaps and converted to Python font
files as [described here](../icon_fonts/README.md).
