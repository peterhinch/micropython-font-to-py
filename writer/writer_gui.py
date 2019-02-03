# writer_gui.py Displayable objects based on the Writer and CWriter classes
# V0.3 Peter Hinch 26th Aug 2018

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

# Base class for a displayable object. Subclasses must implement .show() and .value()
# Has position, colors and border definition.
# border: False no border None use bgcolor, int: treat as color

from writer import Writer
import framebuf

def _circle(dev, x0, y0, r, color): # Single pixel circle
    x = -r
    y = 0
    err = 2 -2*r
    while x <= 0:
        dev.pixel(x0 -x, y0 +y, color)
        dev.pixel(x0 +x, y0 +y, color)
        dev.pixel(x0 +x, y0 -y, color)
        dev.pixel(x0 -x, y0 -y, color)
        e2 = err
        if (e2 <= y):
            y += 1
            err += y*2 +1
            if (-x == y and e2 <= x):
                e2 = 0
        if (e2 > x):
            x += 1
            err += x*2 +1

def circle(dev, x0, y0, r, color, width =1): # Draw circle
    x0, y0, r = int(x0), int(y0), int(r)
    for r in range(r, r -width, -1):
        dev._circle(x0, y0, r, color)

def fillcircle(dev, x0, y0, r, color): # Draw filled circle
    x0, y0, r = int(x0), int(y0), int(r)
    x = -r
    y = 0
    err = 2 -2*r
    while x <= 0:
        dev.line(x0 -x, y0 -y, x0 -x, y0 +y, color)
        dev.line(x0 +x, y0 -y, x0 +x, y0 +y, color)
        e2 = err
        if (e2 <= y):
            y +=1
            err += y*2 +1
            if (-x == y and e2 <= x):
                e2 = 0
        if (e2 > x):
            x += 1
            err += x*2 +1


class DObject():
    def __init__(self, writer, row, col, height, width, fgcolor, bgcolor, bordercolor):
        writer.set_clip(True, True, False)  # Disable scrolling text
        self.writer = writer
        device = writer.device
        self.device = device
        if row < 0:
            row = 0
            self.warning()
        elif row + height >= device.height:
            row = device.height - height - 1
            self.warning()
        if col < 0:
            col = 0
            self.warning()
        elif col + width >= device.width:
            row = device.width - width - 1
            self.warning()
        self.row = row
        self.col = col
        self.width = width
        self.height = height
        self._value = None  # Type depends on context but None means don't display.
        # Current colors
        if fgcolor is None:
            fgcolor = writer.fgcolor
        if bgcolor is None:
            bgcolor = writer.bgcolor
        if bordercolor is None:
            bordercolor = fgcolor
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        # bordercolor is False if no border is to be drawn
        self.bdcolor = bordercolor
        # Default colors allow restoration after dynamic change
        self.def_fgcolor = fgcolor
        self.def_bgcolor = bgcolor
        self.def_bdcolor = bordercolor
        # has_border is True if a border was drawn
        self.has_border = False

    def warning(self):
        print('Warning: attempt to create {} outside screen dimensions.'.format(self.__class__.__name__))

    # Draw a border if .bdcolor specifies a color. If False, erase an existing border
    def show(self):
        wri = self.writer
        dev = wri.device
        if isinstance(self.bdcolor, bool):  # No border
            if self.has_border:  # Border exists: erase it
                dev.rect(self.col - 2, self.row - 2, self.width + 4, self.height + 4, self.bgcolor)
                self.has_border = False
        elif self.bdcolor:  # Border is required
            dev.rect(self.col - 2, self.row - 2, self.width + 4, self.height + 4, self.bdcolor)
            self.has_border = True

    def value(self, v = None):
        if v is not None:
            self._value = v
        return self._value

# text: str display string int save width
class Label(DObject):
    def __init__(self, writer, row, col, text, invert=False, fgcolor=None, bgcolor=None, bordercolor=False):
        # Determine width of object
        if isinstance(text, int):
            width = text
            text = None
        else:
            width = writer.stringlen(text)
        height = writer.height
        super().__init__(writer, row, col, height, width, fgcolor, bgcolor, bordercolor)
        if text is not None:
            self.value(text, invert)

    def value(self, text=None, invert=False, fgcolor=None, bgcolor=None, bordercolor=None):
        txt = super().value(text)
        # Redraw even if no text supplied: colors may have changed.
        self.invert = invert
        self.fgcolor = self.def_fgcolor if fgcolor is None else fgcolor
        self.bgcolor = self.def_bgcolor if bgcolor is None else bgcolor
        if bordercolor is False:
            self.def_bdcolor = False
        self.bdcolor = self.def_bdcolor if bordercolor is None else bordercolor
        self.show()
        return txt

    def show(self):
        txt = super().value()
        if txt is None:  # No content to draw. Future use.
            return
        super().show()  # Draw or erase border
        wri = self.writer
        dev = self.device
        wri.setcolor(self.fgcolor, self.bgcolor)
        dev.fill_rect(self.col, self.row, self.width, wri.height, wri.bgcolor)  # Blank text field
        Writer.set_textpos(dev, self.row, self.col)
        wri.setcolor(self.fgcolor, self.bgcolor)
        wri.printstring(txt, self.invert)
        wri.setcolor()  # Restore defaults

class Meter(DObject):
    def __init__(self, writer, row, col, *, height=50, width=10,
                 fgcolor=None, bgcolor=None, pointercolor=None, bordercolor=None,
                 divisions=5, legends=None, value=None):
        super().__init__(writer, row, col, height, width, fgcolor, bgcolor, bordercolor)
        self.divisions = divisions
        self.legends = legends
        self.pointercolor = pointercolor if pointercolor is not None else self.fgcolor
        self.value(value)

    def value(self, n=None):
        if n is None:
            return super().value()
        n = super().value(min(1, max(0, n)))
        self.show()
        return n
        
    def show(self):
        super().show()  # Draw or erase border
        val = super().value()
        wri = self.writer
        dev = self.device
        width = self.width
        height = self.height
        legends = self.legends
        x0 = self.col
        x1 = self.col + width
        y0 = self.row
        y1 = self.row + height
        dev.fill_rect(self.col, self.row, width, height, self.bgcolor)  # Blank field
        if self.divisions > 0:
            dy = height / (self.divisions) # Tick marks
            for tick in range(self.divisions + 1):
                ypos = int(y0 + dy * tick)
                dev.hline(x0 + 2, ypos, x1 - x0 - 4, self.fgcolor)

        if legends is not None: # Legends
            dy = 0 if len(legends) <= 1 else height / (len(legends) -1)
            yl = y1 - wri.height / 2 # Start at bottom
            for legend in legends:
                Label(wri, int(yl), x1 + 4, legend)
                yl -= dy

        y = int(y1 - val * height) # y position of slider
        dev.hline(x0, y, width, self.pointercolor) # Draw pointer


class LED(DObject):
    def __init__(self, writer, row, col, *, height=15,
                 fgcolor=None, bgcolor=None, bordercolor=None, legend=None):
        super().__init__(writer, row, col, height, height, fgcolor, bgcolor, bordercolor)
        self.legend = legend
        self.radius = self.height // 2

    def color(self, c):
        self.fgcolor = c
        self.show()

    def show(self):
        super().show()
        wri = self.writer
        dev = self.device
        r = self.radius
        fillcircle(dev, self.col + r, self.row + r, r, self.fgcolor)
        if self.legend is not None:
            Label(wri, self.row + self.height - wri.height, self.col + self.width + 1, self.legend)
