# font_to_py.py

Convert a font file to Python source code.

# Usage

``font_to_py.py`` is a command line utility written in Python 3. It is run on a
PC. It takes as input a font file with a ``ttf`` or ``otf`` extension and a
required height in pixels and outputs a Python 3 source file. The pixel layout
is determined by command arguments. By default fonts are stored in variable
pitch form. This may be overidden by a command line argument.

By default the ASCII character set (ordinal values 32 to 126 inclusive) is
supported. Command line arguments can modify this range as required, if
necessary to include extended ASCII characters up to 255.

Further arguments ensure that the byte contents and layout are correct for the
target display hardware. Their usage should be specified in the documentation
for the device driver.

Example usage to produce a file ``myfont.py`` with height of 23 pixels:  
``font_to_py.py FreeSans.ttf 23 myfont.py``

## Arguments

### Mandatory positional arguments:

 1. Font file path. Must be a ttf or otf file.
 2. Height in pixels.
 3. Output file path. Filename must have a .py extension.

### Optional arguments:

 * -f or --fixed If specified, all characters will have the same width. By
 default fonts are assumed to be variable pitch.
 * -x or --xmap Specifies horizontal mapping (default is vertical).
 * -r or --reverse Specifies bit reversal in each font byte.
 * -s or --smallest Ordinal value of smallest character to be stored. Default
 32 (ASCII space).
 * -l or --largest Ordinal value of largest character to be stored. Default 126.
 * -e or --errchar Ordinal value of character to be rendered if an attempt is
 made to display an out-of-range character. Default 63 (ASCII "?").

Any requirement for arguments -xr will be specified in the device driver
documentation. Bit reversal is required by some display hardware.

### Output

The specified height is a target. The algorithm gets as close to the target
height as possible (usually within one pixel). The actual height achieved is
displayed on completion, along with the width of the widest character.

A warning is output if the output filename does not have a .py extension as the
creation of a binary font file may not be intended.

## The font file

Assume that the you have employed the utility to create a file ``myfont.py``. In
your code you will issue

```python
import myfont
```

The ``myfont`` module name will then be used to instantiate a ``Writer`` object
to render strings on demand. A practical example may be studied
[here](https://github.com/peterhinch/micropython-samples/blob/master/SSD1306/ssd1306_test.py).
The detailed layout of the Python file may be seen [here](./DRIVERS.md).

### Binary font files

There is an option to create a binary font file, specified with a ``-b`` or
``--binary`` command line argument. In this instance the output filename must
not have a ``.py`` extension. This is primarily intended for the e-paper driver
in applications where the file is to be stored on the display's internal flash
memory rather than using frozen Python modules.

The technique of accessing character data from a random access file is slow
and thus probably only applicable to devices such as e-paper where the update
time is slow.

Binary files currently support only the standard ASCII character set. There is
no error character: the device driver must ensure that seeks are within range.
Consequently the following arguments are invalid:

 * -s or --smallest
 * -l or --largest
 * -e or --errchar

# Dependencies, links and licence

The code is released under the MIT licence. It requires Python 3.2 or later.

The module relies on [Freetype](https://www.freetype.org/) which is included in most Linux distributions.  
It uses the [Freetype Python bindings](http://freetype-py.readthedocs.io/en/latest/index.html)
which will need to be installed.  
My solution draws on the excellent example code written by Daniel Bader. This
may be viewed [here](https://dbader.org/blog/monochrome-font-rendering-with-freetype-and-python) and [here](https://gist.github.com/dbader/5488053).

# Appendix: RAM utilisation Test Results

A font file was created, frozen as bytecode and deployed to a version 1.0
Pyboard. The font was saved as variable pitch with a height of 19 pixels. The
following code was then pasted at the REPL:

```python
import gc, micropython
gc.collect()
micropython.mem_info()

import freeserif

gc.collect()
micropython.mem_info()

def foo():
    addr, height, width = freeserif.get_ch('a')

foo()

gc.collect()
micropython.mem_info()
print(len(freeserif._font) + len(freeserif._index))
```

The memory used was 5408, 5648, and 5696 bytes. As increments over the initial
state this corresponds to 240 and 288 bytes. The ``print`` statement shows the
RAM which would be consumed by the data arrays: this was 3271 bytes.

The ``foo()`` function emulates the behaviour of a device driver in rendering a
character to a display. The local variables constitute memory which will be
reclaimed on exit from the function. Its additional RAM use was 48 bytes.

## Conclusion

With a font of height 19 pixels RAM saving was an order of magnitude. The
saving will be greater if larger fonts are used
