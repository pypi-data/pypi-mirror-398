import shutil
import ctypes
import sys
import msvcrt
import atexit
import struct
from libTerm.term.types import color
from libTerm.term.types import Size

class Colors:
	def __init__(s,**k):
		s.parent = k.get('parent')
		s.fg = color(255, 255, 255)
		s.bg = color(0, 0, 0)
		s.refresh()
	def refresh(s):
		# Windows API constants
		STD_OUTPUT_HANDLE = -11
		handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
		csbi = ctypes.create_string_buffer(22)
		res = ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, csbi)
		if res:
			# Unpack the color attribute as a WORD (2 bytes) at offset 4
			attr = struct.unpack('<H', csbi.raw[4:6])[0]
			s.fg = attr & 0x0F
			s.bg = (attr & 0xF0) >> 4
			s.foreground = s.fg
			s.background = s.bg
		else:
			s.fg = None
			s.bg = None
			s.foreground = None
			s.background = None

class Term:
    def __init__(s, *a, **k):
        s.pid = None  # Not relevant for Windows terminal
        s.ppid = None
        s.fd = None
        s.tty = None
        s.attrs = None
        s._mode = 0
        s.mode = s.__mode__
        atexit.register(s.mode, 'normal')
        s.cursor = None
        s.vcursors = None
        s.size = Size(parent=s)  # Reflects current terminal size
        s.color = Colors(parent=s)  # Reflects current terminal colors


    def getch(s):
        """Read a single character from the terminal."""
        return msvcrt.getch().decode('utf-8', errors='ignore')

    def kbhit(s):
        """Check if a keypress is available."""
        return msvcrt.kbhit()

    def __mode__(s, mode=None):
        nmodi = {'normal': 1, 'ctl': 2}
        if mode is not None and mode != s._mode:
            s._mode = nmodi.get(mode)
        return s._mode

    def ansi(s, ansi, parser):
        # Parse ANSI color code for foreground (e.g., \x1b[32m)
        import re
        match = re.search(r'\x1b\[(3[0-7])m', ansi)
        if match:
            s.last_ansi_fg = int(match.group(1)[1:])  # 30-37 -> 0-7
        sys.stdout.write(ansi)
        sys.stdout.flush()
        return parser()

    def refresh(s):
        """Refresh the size and color settings."""
        s.size.refresh()
        s.color.refresh()

    # Stub methods for compatibility
    def setraw(s, when=None):
        pass
    def setcbreak(s, when=None):
        pass
    def echo(s, enable=False):
        pass
    def canonical(s, enable):
        pass
    def update(s, when=None):
        pass
