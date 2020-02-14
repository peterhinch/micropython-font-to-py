# font_to_py.py

Convert a font file to Python source code. Python font files provide a much
faster way to access glyphs than the principal alternative which is a random
access file on the filesystem.

Another benefit is that they can save large amounts of RAM on resource-limited
targets: the font file may be incorporated into a firmware build such that it
occupies flash memory rather than scarce RAM. Python code built into firmware
is known as frozen bytecode.

## Recent revisions

17 Oct 2019 V0.33 With thanks to Stephen Irons (@ironss).
 1. Fix bug where input rather than output filename was checked.
 2. Add `baseline()` to ouput file returning the maximum ascent.
 3. Correct left position of rendered glyph.

21 Sept 2019 V0.22

 1. Reduced output file size for sparse fonts. These result from large gaps
 between ordinal values of Unicode characters not in the standard ASCII set.
 2. Output file has comment showing creation command line.
 3. Repo includes the file `extended`. Using `-k extended` creates fonts
 comprising the printable ASCII set plus `°μπωϕθαβγδλΩ£`. Such a font has 96
 chars having ordinal values from 32-981.
 4. Improvements to `font_test.py`.
 5. Code emitted for sparse fonts now uses non-recursive search algorithm.

Python files produced are interchangeable with those from prior versions: the
API is unchanged.

###### [Main README](./README.md)

# Dependencies

The utility requires Python 3.2 or greater, also `freetype` which may be
installed using `pip3`. On Linux (you may need a root prompt):

```shell
# apt-get install python3-pip
# pip3 install freetype-py
```

# Usage

`font_to_py.py` is a command line utility written in Python 3. It is run on a
PC. It takes as input a font file with a `ttf` or `otf` extension and a
required height in pixels and outputs a Python 3 source file. The pixel layout
is determined by command arguments. By default fonts are stored in variable
pitch form. This may be overidden by a command line argument.

By default the printable ASCII character set (ordinal values 32 to 126
inclusive) is supported (i.e. not including control characters). Command line
arguments can modify this range as required to specify arbitrary sets of
Unicode characters. Non-English and non-contiguous character sets may be
defined.

Further arguments ensure that the byte contents and layout are correct for the
target display hardware. Their usage should be specified in the documentation
for the device driver.

Examples of usage to produce Python fonts with a height of 23 pixels:
```shell
$ font_to_py.py FreeSans.ttf 23 myfont.py
$ font_to_py.py -k extended FreeSans.ttf 23 my_extended_font.py
```
## Arguments

### Mandatory positional arguments:

 1. Font file path. Must be a ttf or otf file.
 2. Height in pixels.
 3. Output file path. Filename must have a .py extension (unless writing a
 binary font).

### Optional arguments:

 * -f or --fixed If specified, all characters will have the same width. By
 default fonts are assumed to be variable pitch.
 * -x or --xmap Specifies horizontal mapping (default is vertical).
 * -r or --reverse Specifies bit reversal in each font byte.
 * -s or --smallest Ordinal value of smallest character to be stored. Default
 32 (ASCII space).
 * -l or --largest Ordinal value of largest character to be stored. Default 126.
 * -e or --errchar Ordinal value of character to be rendered if an attempt is
 made to display an out-of-range character. Default 63 (ord("?")).
 * -i or --iterate Specialist use. See below.
 * -c or --charset Option to restrict the characters in the font to a specific
 set. See below.
 * -k or --charset_file Obtain the character set from a file. Typical use is
 for alternative character sets such as Cyrillic: the file must contain the
 character set to be included. An example file is `cyrillic`. Another is 
 `extended` which adds unicode characters `°μπωϕθαβγδλΩ` to those in the
 original ASCII set of printable characters. At risk of stating the obvious
 this will only produce useful results if the source font file includes all
 specified glyphs.

The -c option may be used to reduce the size of the font file by limiting the
character set. If the font file is frozen as bytecode this will not reduce RAM
usage but it will conserve flash. Example usage for a digital clock font:

```shell
$ font_to_py.py Arial.ttf 20 arial_clock.py -c 1234567890:
```
Example usage with the -k option:  
```shell
font_to_py.py FreeSans.ttf 20 freesans_cyr_20.py -k cyrillic
font_to_py.py -x -k extended FreeSans.ttf 17 font10.py
```

If a character set is specified via `-c` or `-k`, then `--smallest` and
`--largest` should not be specified: these values are computed from the
character set.

Any requirement for arguments -xr will be specified in the device driver
documentation. Bit reversal is required by some display hardware.

Using the -f argument with a variable pitch source font will produce a fixed
pitch result. A better apearance would be achieved by using a font designed as
monospaced.

There have been reports that producing fonts with Unicode characters outside
the ASCII set from ttf files is unreliable. If expected results are not
achieved, use an otf font. I have successfully created Cyrillic and extended
fonts from a `ttf`, so I suspect the issue may be source fonts lacking the
required glyphs.

The `-i` or `--iterate` argument. For specialist applications. Specifying this
causes a generator function `glyphs` to be included in the Python font file. A
generator instantiated with this will yield `bitmap`, `height`, and `width` for
every glyph in the font.

### Output

The specified height is a target. The algorithm gets as close to the target
height as possible (usually within one pixel). The actual height achieved is
displayed on completion, along with the width of the widest character.

A warning is output if the output filename does not have a .py extension as the
creation of a binary font file may not be intended.

## The font file

Assume that the you have employed the utility to create a file `myfont.py`. In
your code you will issue

```python
import myfont
```

The `myfont` module name will then be used to instantiate a `Writer` object
to render strings on demand. A practical example may be studied
[here](./writer/writer_demo.py).
The detailed layout of the Python file may be seen [here](./writer/DRIVERS.md).

### Python font files

These start with a comment which is the command line used to create the font.

They include the following functions:
 1. `height()` Height of bitmaps in pixels (all are the same height).
 2. `max_width()` Width of widest glyph in pixels.
 3. `baseline()` Offset from top of the bitmap to the baseline. This is a
 notional "ruler line" where glyphs are drawn. Enables rendering different
 fonts on a common baseline. It is a positive number of pixels.
 4. `hmap()` `True` if bitmaps are horizonataly mapped.
 5. `reverse()` `True` if bit reversal is used.
 6. `monospaced()` `True` if bitmaps were created with fixed pitch.
 7. `min_ch()` Returns smallest ordinal value in font.
 8. `max_ch()` Largest ordinal value in font.
 9. `get_ch()` Arg: a Unicode character. Returns three items:  
 A memoryview into the bitmap for that character.  
 Bitmap height in pixels. Equal to `height()` above.  
 Bitmap width in pixels.  

See [this link](https://stackoverflow.com/questions/27631736/meaning-of-top-ascent-baseline-descent-bottom-and-leading-in-androids-font)
for an explanation of `baseline`.

### Binary font files

There is an option to create a binary font file, specified with a `-b` or
`--binary` command line argument. In this instance the output filename must
not have a `.py` extension. This is primarily intended for the e-paper driver
in applications where the file is to be stored on the display's internal flash
memory rather than using frozen Python modules.

The technique of accessing character data from a random access file is slow
and thus probably only applicable to devices such as e-paper where the update
time is slow.

Binary files currently support only the standard ASCII character set. There is
no error character: the device driver must ensure that seeks are within range.
Only the following optional arguments are valid:

 * -f or --fixed.
 * -x or --xmap.
 * -r or --reverse.

# Dependencies, links and licence

The code is released under the MIT licence. The `font_to_py.py` utility
requires Python 3.2 or later.

The module relies on [Freetype](https://www.freetype.org/) which is included in most Linux distributions.  
It uses the [Freetype Python bindings](http://freetype-py.readthedocs.io/en/latest/index.html)
which will need to be installed.  
My solution draws on the excellent example code written by Daniel Bader. This
may be viewed [here](https://dbader.org/blog/monochrome-font-rendering-with-freetype-and-python)
and [here](https://gist.github.com/dbader/5488053).

# Appendix 1: RAM utilisation Test Results

The supplied `freesans20.py` and `courier20.py` files were frozen as bytecode
on a Pyboard V1.0. The following code was pasted at the REPL:

```python
import gc, micropython
gc.collect()
micropython.mem_info()

import freesans20

gc.collect()
micropython.mem_info()

import courier20

gc.collect()
micropython.mem_info()

def foo():
    addr, height, width = freesans20.get_ch('a')

foo()

gc.collect()
micropython.mem_info()
print(len(freesans20._font) + len(freesans20._index))
```

The memory used was 1712, 2032, 2384 and 2416 bytes. As increments over the
prior state this corresponds to 320, 352 and 32 bytes. The `print` statement
shows the RAM which would be consumed by the data arrays if they were not
frozen: this was 3956 bytes for `freesans20`.

The `foo()` function emulates the behaviour of a device driver in rendering a
character to a display. The local variables constitute memory which is
reclaimed on exit from the function. Its additional RAM use was 16 bytes.

Similar figures were found in recent (2019) testing on a Pyboard D.

## Conclusion

With a font of height 20 pixels RAM saving was an order of magnitude. The
saving will be greater if larger fonts are used as RAM usage is independent of
the array sizes.

# Appendix 2: Recent improvements

The representation of non-contiguous character sets such as the `extended` set
presents a challenge because the ordinal values of the Unicode characters can
be expected to span a range much greater than the number of characters in the
set. Using an index of the type used for the ASCII set would be inefficient as
most of the elements would be null (pointing to the default character).

The code now behaves as follows. If the character set contains no more than 95
characters (including the default) the emitted Python file is as before. This
keeps the code small and efficient for the common (default) case.

Larger character sets are assumed to be sparse and the emitted code uses an
index optimised for sparse values and a binary search algorithm.

# Appendix 3: font_test.py

This enables a Python font file to be described and rendered at the command
prompt. It provides a useful way of checking unknown font files. Compatibility
with files created by old versions of `font_to_py` is not guaranteed.

It runs under Python 3.2 or above. Given a font `myfont.py` the following will
render the supplied string (assuming that `font_test.py` has executable
privilege):

```bash
./font_test myfont Hello
```
Omitting arguments (or supplying `--help`) will provide usage information.

If no string is provided a default will be printed. This is designed to test
fonts created with `-k extended`. Other fonts will show `?` characters for
missing glyphs.

Sample output:
```bash
$ ./font_test.py freesans1 Hello
Vertical map
Normal bit order
Proportional spacing
Dimensions height*max_width 23 * 23
Start char " " (ord 32) end char "~" (ord 126)
...................................................
##.........##................##...##...............
##.........##................##...##...............
##.........##................##...##...............
##.........##................##...##...............
##.........##................##...##...............
##.........##.......#####....##...##......#####....
##.........##......#######...##...##.....#######...
#############.....###....##..##...##....###...###..
#############....###......##.##...##...###.....###.
##.........##....##.......##.##...##...##.......##.
##.........##....###########.##...##...##.......##.
##.........##....###########.##...##...##.......##.
##.........##....##..........##...##...##.......##.
##.........##....##.......##.##...##...###.....###.
##.........##.....##.....##..##...##....###...###..
##.........##......########..##...##.....#######...
##.........##.......#####....##...##......#####....
...................................................
...................................................
...................................................
...................................................
...................................................
```
