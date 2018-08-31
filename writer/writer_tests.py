# ssd1306_test.py Demo program for rendering arbitrary fonts to an SSD1306 OLED display.

# The MIT License (MIT)
#
# Copyright (c) 2018 Peter Hinch
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


# https://learn.adafruit.com/monochrome-oled-breakouts/wiring-128x32-spi-oled-display
# https://www.proto-pic.co.uk/monochrome-128x32-oled-graphic-display.html

# V0.3 12th Aug 2018

import machine
import utime
import uos
from ssd1306_setup import WIDTH, HEIGHT, setup
from writer import Writer, CWriter
from writer_gui import Label, Meter

# Fonts
import freesans20
import courier20 as fixed
import font6 as small
import arial10

def inverse(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    rhs = WIDTH -1
    ssd.line(rhs - 20, 0, rhs, 20, 1)
    square_side = 10
    ssd.fill_rect(rhs - square_side, 0, square_side, square_side, 1)

    Writer.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
    wri = Writer(ssd, freesans20, verbose=False)
    wri.set_clip(False, False, False)  # Char wrap
    wri.printstring('Sunday\n')
    wri.printstring('12 Aug 2018\n')
    wri.printstring('10.30am', True)  # Inverse text
    ssd.show()

def scroll(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    rhs = WIDTH -1
    ssd.line(rhs - 20, 0, rhs, 20, 1)
    square_side = 10
    ssd.fill_rect(rhs - square_side, 0, square_side, square_side, 1)

    Writer.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
    wri = Writer(ssd, freesans20, verbose=False)
    wri.set_clip(False, False, False)  # Char wrap
    wri.printstring('Sunday\n')
    wri.printstring('12 Aug 2018\n')
    wri.printstring('10.30am')
    for x in range(5):
        ssd.show()
        utime.sleep(2)
        wri.printstring('\nCount = {:2d}'.format(x))
    ssd.show()
    utime.sleep(2)
    wri.printstring('\nDone.')
    ssd.show()

def usd_scroll(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    # Only CWriter can do usd
    CWriter.invert_display(ssd)
    CWriter.set_textpos(ssd, 0, 0)
    wri = CWriter(ssd, freesans20, verbose=False)
    wri.set_clip(False, False, False)  # Char wrap

    wri.printstring('Sunday\n')
    wri.printstring('12 Aug 2018\n')
    wri.printstring('10.30am')
    for x in range(5):
        ssd.show()
        utime.sleep(2)
        wri.printstring('\nCount = {:2d}'.format(x))
    ssd.show()
    utime.sleep(2)
    wri.printstring('\nDone.')
    ssd.show()
    CWriter.invert_display(ssd, False)  # For subsequent tests

def usd(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    # Only CWriter can do usd
    CWriter.invert_display(ssd)
    CWriter.set_textpos(ssd, 0, 0)
    wri = CWriter(ssd, freesans20, verbose=False)
    wri.set_clip(False, False, False)  # Char wrap
    wri.printstring('Sunday\n')
    wri.printstring('12 Aug 2018\n')
    wri.printstring('10.30am')
    ssd.show()
    CWriter.invert_display(ssd, False)  # For subsequent tests

def rjust(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    Writer.set_textpos(ssd, 0, 0)  # Previous tests may have altered it
    wri = Writer(ssd, freesans20, verbose=False)
    wri.set_clip(False, False, False)  # Char wrap

    my_str = 'Sunday\n'
    l = wri.stringlen(my_str)
    Writer.set_textpos(ssd, col = WIDTH - l)
    wri.printstring(my_str)

    my_str = '12 Aug 2018\n'
    l = wri.stringlen(my_str)
    Writer.set_textpos(ssd, col = WIDTH - l)
    wri.printstring(my_str)

    my_str = '10.30am'
    l = wri.stringlen(my_str)
    Writer.set_textpos(ssd, col = WIDTH - l)
    wri.printstring(my_str)
    ssd.show()

def fonts(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    Writer.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
    wri = Writer(ssd, freesans20, verbose=False)
    wri.set_clip(False, False, False)  # Char wrap
    wri_f = Writer(ssd, small, verbose=False)
    wri_f.set_clip(False, False, False)  # Char wrap
    wri_f.printstring('Sunday\n')
    wri.printstring('12 Aug 2018\n')
    wri.printstring('10.30am')
    ssd.show()

def tabs(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    Writer.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
    wri = Writer(ssd, fixed, verbose=False)
    wri.set_clip(False, False, False)  # Char wrap
    wri.printstring('1\t2\n')
    wri.printstring('111\t22\n')
    wri.printstring('1111\t1')
    ssd.show()

def usd_tabs(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    CWriter.invert_display(ssd)
    CWriter.set_textpos(ssd, 0, 0)
    wri = CWriter(ssd, fixed, verbose=False)
    wri.set_clip(False, False, False)  # Char wrap
    wri.printstring('1\t2\n')
    wri.printstring('111\t22\n')
    wri.printstring('1111\t1')
    ssd.show()
    CWriter.invert_display(ssd, False)  # For subsequent tests

def wrap(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    Writer.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
    wri = Writer(ssd, freesans20, verbose=False)
    wri.set_clip(False, False, True)  # Word wrap
    wri.printstring('the quick    brown fox jumps over')
    ssd.show()

def dual(use_spi=False, soft=True):
    ssd0 = setup(False, soft)  # I2C display
    ssd1 = setup(True, False)  # SPI  instance
    Writer.set_textpos(ssd0, 0, 0)  # In case previous tests have altered it
    wri0 = Writer(ssd0, small, verbose=False)
    wri0.set_clip(False, False, False)
    Writer.set_textpos(ssd1, 0, 0)  # In case previous tests have altered it
    wri1 = Writer(ssd1, small, verbose=False)
    wri1.set_clip(False, False, False)

    nfields = []
    dy = small.height() + 6
    col = 15
    for n, wri in enumerate((wri0, wri1)):
        nfields.append([])
        y = 2
        for txt in ('X:', 'Y:', 'Z:'):
            Label(wri, y, 0, txt)
            nfields[n].append(Label(wri, y, col, wri.stringlen('99.99'), True))
            y += dy

    for _ in range(10):
        for n, wri in enumerate((wri0, wri1)):
            for field in nfields[n]:
                value = int.from_bytes(uos.urandom(3),'little')/167772
                field.value('{:5.2f}'.format(value))
            wri.device.show()
            utime.sleep(1)
    for wri in (wri0, wri1):
        Label(wri, 0, 64, ' DONE ', True)
        wri.device.show()


tstr = '''Test assumes a 128*64 (w*h) display. Edit WIDTH and HEIGHT in ssd1306_setup.py for others.
Device pinouts are comments in ssd1306_setup.py.
All tests take two boolean args:
use_spi = False. Set True for SPI connected device
soft=True set False to use hardware I2C/SPI. Hardware I2C option currently fails with official SSD1306 driver.

Available tests:
inverse() Show black on white text.
scroll() Illustrate scrolling
usd() Upside-down display.
usd_scroll() Upside-down scroll test.
rjust() Right justification.
fonts() Two fonts.
tabs() Tab stops.
usd_tabs() Upside-down tabs.
wrap() Word wrapping
dual() Test two displays on one host.'''

print(tstr)
