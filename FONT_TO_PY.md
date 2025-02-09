# font_to_py.py Creation of Python font files

A PC utility for converting industry standard font files to Python source code.

# 0. Contents

1. [Introdction](./FONT_TO_PY.md#1-introduction) Creating Python fonts.  
 1.1 [Revision history](./FONT_TO_PY.md#11-revision-history)  
2. [Dependencies](./FONT_TO_PY.md#2-dependencies) Installation.  
3. [Usage](./FONT_TO_PY.md#3-usage)  
 3.1 [Arguments](./FONT_TO_PY.md#31-arguments)  
 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;3.1.1 [Mandatory positional arguments](./FONT_TO_PY.md#311-mandatory-positional-arguments)  
 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;3.1.2 [Optional arguments](./FONT_TO_PY.md#312-optional-arguments)  
 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;3.1.3 [The height arg](./FONT_TO_PY.md#313-the-height-arg)  
 3.2 [The font file](./FONT_TO_PY.md#32-the-font-file) How to use the font file.  
4. [Python font files](./FONT_TO_PY.md#4-python-font-files) Python font file format.  
5. [Binary font files](./FONT_TO_PY.md#5-binary-font-files) Binary font file format.  
6. [Dependencies links and licence](./FONT_TO_PY.md#6-dependencies-links-and-licence) Acknowledgement of sources.  

[Appendix 1 RAM utilisation Test Results](./FONT_TO_PY.md#appendix-1-ram-utilisation-test-results)  
[Appendix 2 Recent improvements](./FONT_TO_PY.md#appendix-2-recent-improvements)  
[Appendix 3 Testing](./FONT_TO_PY.md#appendix-3-testing) A desktop utility to check fonts.  
[Appendix 4 Custom character sets](./FONT_TO_PY.md#appendix-4-custom-character-sets) Creating e.g. fonts having non-English character sets.  
[Appendix 5 Iteration](./FONT_TO_PY.md#appendix-5-iteration) Enabling a font to support iteration.  

# 1. Introduction

This PC utility converts an industry standard font file to Python source code.

Python font files offer advantages on microcontroller platforms running
MicroPython. They provide a much faster way to render glyphs than the principal
alternative which is a random access binary file on the filesystem.

The format of the Python font file is designed to save large amounts of RAM on
resource-limited targets: the font file may be incorporated into a firmware
build such that it occupies flash memory rather than scarce RAM. Python code
built into firmware is known as frozen bytecode.

## 1.1 Revision history

22 Mar 2024 V0.42 Default mapping is now horizontal.  
30 Jan 2023 V0.41 With thanks to @ferrolive (Igor Oliveira) who supplied the
charset file.
 1. Charset file enables Chinese, Japanese and Korean glyphs to be specified.
 2. Now allows much larger output files: sparse index is now 24 bit.

1 Feb 2021 V0.4 With thanks to @enigmaniac for the suggestion and code ideas.
 1. Now supports `bdf` and `pcf` font files for better results at small sizes.

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
###### [Contents](./FONT_TO_PY.md#0-contents)

# 2. Dependencies

The utility requires Python 3.2 or greater, also [freetype-py](https://github.com/rougier/freetype-py) which may be
installed using `pip3`. On Linux (you may need a root prompt):

```shell
# apt-get install python3-pip
# pip install freetype-py
```

# 3. Usage

`font_to_py.py` is a command line utility written in Python 3. It is run on a
PC. It takes as input a font file with a `ttf` or `otf` extension and a
required height in pixels and outputs a Python 3 source file. Alternatively it
will accept a `bdf` or `pcf` source file (which includes a height definition).
The pixel layout is determined by command arguments. By default fonts are
stored in variable pitch form. This may be overidden by a command line
argument.

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
## 3.1 Arguments

### 3.1.1 Mandatory positional arguments

 1. Font file path. Must be a ttf or otf file.
 2. Height in pixels. In the case of `bdf` or `pcf` files a height of 0 should
 be specified as the height is retrieved from the file.
 3. Output file path. Filename must have a .py extension (unless writing a
 binary font). A warning is output if the output filename does not have a .py
 extension as the creation of a binary font file may not be intended.

### 3.1.2 Optional arguments

 * -f or --fixed If specified, all characters will have the same width. By
 default fonts are assumed to be variable pitch.
 * -x or --xmap Specifies that the output file should be horizontally mapped.
 This is the default if no mapping is specified. Most display hardware requires
 horizontal mapping.
 * -y or --ymap Vertical mapping for specialist display hardware. Not compatible
 with `Writer` classes.
 * -r or --reverse Specifies bit reversal in each font byte.
 * -s or --smallest Ordinal value of smallest character to be stored. Default
 32 (ASCII space).
 * -l or --largest Ordinal value of largest character to be stored. Default 126.
 * -e or --errchar Ordinal value of character to be rendered if an attempt is
 made to display an out-of-range character. Default 63 (ord("?")).
 * -i or --iterate Specialist use. See [Appendix 5](./FONT_TO_PY.md#appendix-5-iteration).
 * -b or --binary Create a binary font file. See [Binary font files](./FONT_TO_PY.md#5-binary-font-files).
 * -c or --charset Option to restrict the characters in the font to a specific
 set. See below.
 * -k or --charset_file Obtain the character set from a file. Typical use is
 for alternative character sets such as Cyrillic. Please see
 [Appendix 4](./FONT_TO_PY.md#appendix-4-custom-character-sets) for details of
 creation of custom character sets.

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
pitch result. A better appearance would be achieved by using a font designed as
monospaced.

There have been reports that producing fonts with Unicode characters outside
the ASCII set from `ttf` files is unreliable. If expected results are not
achieved, use an `otf` font. I have successfully created Cyrillic and extended
fonts from a `ttf`, so I suspect the issue may be source fonts lacking the
required glyphs.

### 3.1.3 The height arg

In the case of scalable `ttf` or `otf` source files the specified height is a
target. The algorithm gets as close to the target height as possible (usually
within one pixel). The actual height achieved is displayed on completion, along
with the width of the widest character.

If a `bdf` or `pcf` bitmapped font is specified, the `height` arg should be 0.
A nonzero value will cause a warning message to be printed and the value will
be ignored.

## 3.2 The font file

Assume that the you have employed the utility to create a file `myfont.py`. In
your code you will issue:

```python
import myfont
```

The `myfont` module name will then be used to instantiate a `Writer` object
to render strings on demand. A practical example may be studied
[here](./writer/writer_demo.py).
The detailed layout of the Python file may be seen [here](./writer/DRIVERS.md).

###### [Contents](./FONT_TO_PY.md#0-contents)

# 4. Python font files

Users of the `Writer` or `CWriter` classes or of
[nano-gui](https://github.com/peterhinch/micropython-nano-gui) do not need to
study the file format. These details are provided for those wishing to access
Python font files directly.

Files start with a comment which is the command line used to create the font.

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

# 5. Binary font files

There is an option to create a binary font file, specified with a `-b` or
`--binary` command line argument. In this instance the output filename must
not have a `.py` extension. This format was developed for an e-paper driver
where the file was stored on the display's internal flash memory; it is not
clear if there is a current use case.

Binary files currently support only the standard ASCII character set. There is
no error character: the device driver must ensure that seeks are within range.
Conversion of bdf and pcf font files is currently unsupported.

Only the following optional arguments are valid:

 * -f or --fixed.
 * -x or --xmap.
 * -y or --ymap
 * -r or --reverse.

The format of binary font files is described [here](./writer/DRIVERS.md).

An alternative implementation of binary fonts may be found in
[this repo](https://github.com/antirez/microfont). It provides for rotated
rendering to a `FrameBuffer`.

###### [Contents](./FONT_TO_PY.md#0-contents)

# 6. Dependencies links and licence

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

###### [Contents](./FONT_TO_PY.md#0-contents)

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

# Appendix 3: Testing

The file `font_test.py` enables a Python font file to be described and rendered
at the command prompt. It provides a useful way of checking unknown font files.
Compatibility with files created by old versions of `font_to_py` is not
guaranteed.

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
###### [Contents](./FONT_TO_PY.md#0-contents)

# Appendix 4 Custom character sets

A common requirement is to create Python fonts containing a specific set of
glyphs - typically for non-English languages, or simply to include additional
symbols such as `°`. This is achieved by creating a "charset" file containing the
entire set of required glyphs. Python fonts are then created using the `-k`
option, specifying the charset file as follows:
```shell
font_to_py.py FreeSans.ttf 20 freesans_cyr_20.py -k cyrillic
font_to_py.py -x -k extended FreeSans.ttf 17 font10.py
```
Example charsets may be found in the `charsets` directory, a non-English example
being `cyrillic`. The `extended` file adds unicode characters `°μπωϕθαβγδλΩ` to
those in the original ASCII set of printable characters. This might be edited to
produce a custom version.

At risk of stating the obvious, for this process to succeed the source font file
must include all specified glyphs.

Submissions of charset files, particularly for non-English languages, are
welcome.

# Appendix 5 Iteration

The `-i` or `--iterate` arg is for specialist applications; it causes a
generator function `glyphs` to be included in the Python font file. A generator
instantiated with this will yield `bitmap`, `height`, and `width` for every
glyph in the font.

###### [Contents](./FONT_TO_PY.md#0-contents)
