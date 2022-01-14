# Icon Fonts

It is possible to display icons by incorporating their images in a font file.
There are `.ttf` and `.otf` files available which can be converted to Python
using `font_to_py.py`. I have not had much success with these. I also wanted
to create my own icons. I experimented with using a font editor to modify an
existing font. I found the font editor unintuitive and hard to use. However it
does have the advantage of producing scalable fonts which can mix normal glyphs
with icons.

The solution offered here uses the Linux `bitmap` editor plus a utility to
convert a set of its output files to a Python font file. The image below shows
typical usage.

![Image](./icon_font.jpg)

# The bitmap editor

This is documented in the man pages. It is easy and intuitive to use. To
generate (say) 19x19 icons, issue
```bash
$ bitmap -size 19x19
```
Save each bitmap under a different name: I use a `.c` extension as they are C
source files.

You need to create an additional icon to provide the output under error
conditions, i.e. if an attempt is made to display a glyph not in the font. All
icons in a font file must be the same height.

# The file list

Create a text file listing the bitmap filenames, one filename per line. The
icon to be used as the default (error) image should be first. Subsequent icons
will be assigned to characters "A", "B", "C" sequentially.

The file list can include comments identified with `#`.

# Creating the Python font

This uses `c_to_python_font.py` which runs on a PC and requires Python 3.8 or
later. The file `font_to_py.py` should be in the same directory.

Assuming a file list `my_file_list.txt`, the following will create
`my_font.py`.

```bash
$ ./c_to_python_font.py my_file_list.txt my_font.py
```

# Using the font

The following will print `icon[2]` where `icon[0]` is the default and `icon[1]`
is associated with "A".
```python
# Instantiate the ssd display object
import my_font
import CWriter
wri = CWriter(ssd, my_font)
wri.printstring("B")
```
