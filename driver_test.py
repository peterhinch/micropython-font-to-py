# driver_test.py Simple test for rendering text to an ssd1306 display in
# arbitrary fonts
# V0.1 Peter Hinch Nov 2016

# The MIT License (MIT)
#
# Copyright (c) 2016 Peter Hinch
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

# This demo uses a modified version of the official SSD1306 driver to fix an
# issue with the scroll method. Once the official version is fixed, it should
# be substituted for ssd1306_drv

import machine
import utime
from writer import Writer
from ssd1306_drv import SSD1306_I2C, SSD1306_SPI  # Until official module is fixed
import freeserif
import freesans20
import inconsolata16

# Display parameters
WIDTH = const(128)
SPI = False
# Note that HEIGHT is set below

if SPI:
    # Pyb   SSD
    # 3v3   Vin
    # Gnd   Gnd
    # X1    DC
    # X2    CS
    # X3    Rst
    # X6    CLK
    # X8    DATA
    HEIGHT = 32
    pdc = machine.Pin('X1', machine.Pin.OUT_PP)
    pcs = machine.Pin('X2', machine.Pin.OUT_PP)
    prst = machine.Pin('X3', machine.Pin.OUT_PP)
    spi = machine.SPI(1)
    display = SSD1306_SPI(WIDTH, HEIGHT, spi, pdc, prst, pcs)
else:  # I2C
    # Pyb   SSD
    # 3v3   Vin
    # Gnd   Gnd
    # Y9    CLK
    # Y10   DATA
    HEIGHT = 64
    pscl = machine.Pin('Y9', machine.Pin.OUT_PP)
    psda = machine.Pin('Y10', machine.Pin.OUT_PP)
    i2c = machine.I2C(scl=pscl, sda=psda)
    display = SSD1306_I2C(WIDTH, HEIGHT, i2c)

serif = Writer(display, freeserif)
sans = Writer(display, freesans20)
Writer.set_clip(True, True)  # Disable auto scrolling and wrapping.
serif.printstring('Tuesday\n')
sans.printstring('8 Nov 2016\n')
sans.printstring('10.30am')
display.show()


def scroll_test(x, y):
    t = utime.ticks_us()
    display.scroll(x, y)  # 125ms
    print(utime.ticks_diff(utime.ticks_us(), t))
    display.show()
