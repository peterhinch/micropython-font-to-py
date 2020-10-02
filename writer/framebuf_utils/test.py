import framebuf_utils
import framebuf

# Emulate a display driver subclassed from framebuf.FrameBuffer
class Display(framebuf.FrameBuffer):
    def __init__(self):
        self.buf = bytearray(4 * 4 * 2)
        super().__init__(self.buf, 4, 4, framebuf.RGB565)

device = Display()

def foo():
    width = 2  # Glyph dimensions
    height = 2
    i = 0

    while True:
        buf = bytearray(width * height // 8 + 1)
        fbc = framebuf.FrameBuffer(buf, width, height, framebuf.MONO_HMSB)
        fbc.pixel(0, 0, 1)
        print(buf)

        framebuf_utils.render(device, fbc, 1, 1, 0x5555, 0xaaaa)
        print(device.buf)
        print(device.pixel(0, 0))
        print(device.pixel(1, 1))
        print(device.pixel(2, 1))

        i += 1
        print(i)

foo()
