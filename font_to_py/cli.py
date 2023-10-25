# Implements multi-pass solution to setting an exact font height

# Some code adapted from Daniel Bader's work at the following URL
# https://dbader.org/blog/monochrome-font-rendering-with-freetype-and-python
# With thanks to Stephen Irons @ironss for various improvements, also to
# @enigmaniac for ideas around handling `bdf` and `pcf` files.

# The MIT License (MIT)
#
# Copyright (c) 2016-2023 Peter Hinch
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

import importlib.metadata
import sys
from pathlib import Path

import click
import freetype

from .writer import write_binary_font, write_font

if freetype.version()[0] < 1:
    click.echo("freetype version should be >= 1. Please see FONT_TO_PY.md")

MINCHAR = 32  # Ordinal values of default printable ASCII set
MAXCHAR = 126  # 94 chars

UNICODE_PRIVATE_USE_AREA_START = 0xE000
UNICODE_PRIVATE_USE_AREA_END = 0xF8FF

VERSION = importlib.metadata.version("micropython-font-to-py")


def quit(msg):
    click.echo(msg)
    sys.exit(1)


BINARY = """Invalid arguments. Binary (random access) font files support the standard ASCII
character set (from 32 to 126 inclusive). This range cannot be overridden.
Random access font files don't support an error character.
"""

CONTEXT_SETTINGS = dict(max_content_width=100)


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option("-x", "--xmap", is_flag=True, help="Horizontal (x) mapping")
@click.option("-r", "--reverse", is_flag=True, help="Bit reversal")
@click.option("-f", "--fixed", is_flag=True, help="Fixed width (monospaced) font")
@click.option(
    "-b",
    "--binary",
    is_flag=True,
    help="Produce binary (random access) font file.",
)
@click.option(
    "-i",
    "--iterate",
    is_flag=True,
    help="Include generator function to iterate over character set.",
)
@click.option(
    "-s",
    "--smallest",
    type=int,
    default=MINCHAR,
    help="Ordinal value of smallest character.",
    show_default=True,
)
@click.option(
    "-l",
    "--largest",
    type=click.IntRange(min=0, max=255),
    help="Ordinal value of largest character.",
    default=MAXCHAR,
    show_default=True,
)
@click.option(
    "-e",
    "--errchar",
    type=click.IntRange(min=0, max=255),
    help="Ordinal value of error character.",
    default=63,
    show_default=True,
)
@click.option(
    "-c",
    "--charset",
    type=str,
    help="Character set. e.g. 1234567890: to restrict for a clock display.",
    default="",
)
@click.option(
    "-k",
    "--charset_file",
    type=click.Path(exists=True),
    help="File containing charset e.g. cyrillic_subset.",
    default=None,
)
@click.argument("infile", type=click.Path(exists=True), required=True)
@click.argument("height", type=int, required=True)
@click.argument("outfile", type=click.Path(), required=True)
def main(  # noqa: C901, PLR0913, PLR0912
    xmap,
    reverse,
    fixed,
    binary,
    iterate,
    smallest,
    largest,
    errchar,
    charset,
    charset_file,
    infile,
    height,
    outfile,
):
    """
    Utility to convert ttf, otf, bdf and pcf font files to Python source.
    Sample usage:
    font_to_py.py FreeSans.ttf 23 freesans.py

    This creates a font with nominal height 23 pixels with these defaults:
    Mapping is vertical, pitch variable, character set 32-126 inclusive.
    Illegal characters will be rendered as "?".

    To specify monospaced rendering issue:
    font_to_py.py FreeSans.ttf 23 --fixed freesans.py
    """

    if Path(infile).suffix.upper() not in (".TTF", ".OTF", ".BDF", ".PCF"):
        quit(f"Font file ({outfile}) should be a ttf or otf file.")

    if binary:
        if Path(outfile).suffix.upper() == ".PY":
            quit("Binary file must not have a .py extension.")

        if smallest != MINCHAR or largest != MAXCHAR or errchar != ord("?") or charset:
            quit(BINARY)

        click.echo("Writing binary font file.")
        if not write_binary_font(outfile, infile, height, xmap, reverse):
            sys.exit(1)
    else:
        if Path(outfile).suffix.upper() != ".PY":
            quit("Output filename must have a .py extension.")

        if smallest < 0:
            quit("--smallest must be >= 0")

        elif largest > MAXCHAR + 1 and Path(outfile).suffix.upper() == ".TTF":
            click.echo(
                "WARNING: extended ASCII characters may not be correctly converted. See docs."
            )

        if charset and (smallest != MINCHAR or largest != MAXCHAR):
            click.echo("WARNING: specified smallest and largest values ignored.")

        if charset_file is not None:
            try:
                with open(charset_file, encoding="utf-8") as f:
                    cset = f.read()
            except OSError:
                click.echo(f"Can't open {charset_file} for reading.")
                sys.exit(1)
        else:
            cset = charset
        # dedupe and remove default char. Allow chars in private use area.
        # https://github.com/peterhinch/micropython-font-to-py/issues/22
        cs = {
            c
            for c in cset
            if c.isprintable()
            or (
                UNICODE_PRIVATE_USE_AREA_START <= ord(c) <= UNICODE_PRIVATE_USE_AREA_END
            )
        } - {errchar}
        cs = sorted(list(cs))
        cset = "".join(cs)  # Back to string
        bitmapped = Path(outfile).suffix.upper() in (".BDF", ".PCF")
        if bitmapped:
            if height != 0:
                click.echo("Warning: height arg ignored for bitmapped fonts.")
            chkface = freetype.Face(infile)
            height = chkface._get_available_sizes()[0].height
            click.echo(f"Found font with size {height!s}")

        click.echo("Writing Python font file.")
        if not write_font(
            outfile,
            infile,
            height,
            fixed,
            xmap,
            reverse,
            smallest,
            largest,
            errchar,
            cset,
            iterate,
            bitmapped,
        ):
            sys.exit(1)

    click.echo(f"{outfile} written successfully.")


if __name__ == "__main__":
    main()
