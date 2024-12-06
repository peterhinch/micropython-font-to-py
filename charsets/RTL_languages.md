Some languages are rendered from right to left (RTL) and others are
boustrophedonic, rendering alternate lines in opposite directions. While the
character sets can be handled in the usual way, the `Writer` and `CWriter`
classes support only LTR rendering. Given that the GUI's are based on these
classes, that limitation applies to their widgets.

A workround is to perform reversal in code. The CPython approach is
```py
reversed_string = my_string[::-1]
```
but this is unavailable in MicroPython. Possible solutions are:
```py
def reverse(s):
    l = list(s)
    l.reverse()
    return "".join(l)
```
or
```py
def reverse(s):
    if (l := len(s)) == 1:
        return s
    l1 = l // 2
    return ''.join((rev(s[l1:]), rev(s[:l1])))
```
which aims to minimise the number of string creations.

Note that the `Textbox` widget relies on word wrap and scrolling: these features
will only work with LTR text.

### [Main README](https://github.com/peterhinch/micropython-font-to-py/tree/master)

### [WRITER.md](https://github.com/peterhinch/micropython-font-to-py/blob/master/writer/WRITER.md)
