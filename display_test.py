import gc
import machine
import utime

from display import Display
from writer import Writer

import DejaVuSans24_l


i2c = machine.I2C(sda=machine.Pin(5), scl=machine.Pin(4))
display = Display(128, 64, i2c)
sans24 = Writer(display, DejaVuSans24_l)
display.set_default_font(sans24)

rotation = 0
while True:
    start = utime.ticks_us()
    display.clear()
    display.set_position(0, 0)
    display.set_rotation(rotation)
    display.draw_text('abcdefghijklmnopqrstuvwxyz')
    # display.hline(0, 0, display.screen_width)
    # display.hline(0, display.screen_height-1, display.screen_width)
    # display.vline(0, 0, display.screen_height)
    # display.vline(display.screen_width-1, 0, display.screen_height)

    display.show()
    end = utime.ticks_us()
    print("time: %0.2fms" % ((end - start) / 1e3))
    gc.collect()
    print("memory:", gc.mem_alloc())
    utime.sleep(5)
    rotation += 90
