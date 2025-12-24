
from dataclasses import dataclass
from enum import Enum
from collections import namedtuple
import re
from libTerm.term.types import Coord
from time import time_ns
import sys
@dataclass()
class ANSI_Cursor(str, Enum):
	esc = '\x1b'
	q = '6n'
	save = 's'
	load = 'u'
	show = '?25h'
	hide = '?25l'

	def __str__(self):
		return '{ESC}[{CODE}'.format(ESC=self.ESC,CODE=self.value)
	def __repr__(self):
		return repr(self.value)


class Cursor():
	def __init__(__s, term):
		super().__init__()
		__s.term = term
		__s.ansi = ANSI_Cursor

		__s.re = re.compile(r"^.?\x1b\[(?P<Y>\d*);(?P<X>\d*)R", re.VERBOSE)
		__s.position = __s.__update__
		__s._xy=Coord(0,0)
		__s.XY=Coord(0,0)
		__s.history = [*(None,) * 64]
		__s.init = __s.__update__()
	@property
	def xy(__s):
		__s._xy=__s.__update__()
		return __s._xy

	def __update__(__s, get='XY'):
		def Parser():
			buf = ' '
			while buf[-1] != "R":
				buf += sys.stdin.read(1)
			# reading the actual values, but what if a keystroke appears while reading
			# from stdin? As dirty work around, getpos() returns if this fails: None
			try:
				groups = __s.re.search(buf).groupdict()
				result = Coord(int(groups['X']), int(groups['Y']))
			except AttributeError:
				result = None
			return result

		result = None
		timeout = {}
		timeout['limit'] = 500
		timeout['start'] = time_ns() // 1e6
		timeout['running'] = 0
		while not result:
			result = __s.term.ansi(''.join([__s.ansi.esc,'[', __s.ansi.q]), Parser)
		__s.XY =result
		return result

	def show(__s, state=True):
		if state:
			print('\x1b[?25h', end='', flush=True)
		else:
			__s.hide()

	def hide(__s, state=True):
		if state:
			print('\x1b[?25l', end='', flush=True)
			atexit.register(__s.show)
		else:
			__s.show()

	@property
	def x(__s):
		__s.X=__s.__update__('X')
		return __s.X

	@property
	def y(__s):
		__s.Y=__s.__update__('Y')
		return __s.Y


class vCursor(Cursor):
	def __init__(__s, term,cursor):
		__s.term = term
		__s.realcursor=cursor
		__s.position = Coord(__s.realcursor.x,__s.realcursor.y)
		__s.history = [*(None,) * 64]
		__s.controled = False
		__s.bound = True
		__s.frozen = False
		__s.init = __s.__update__()

	def freeze(__s, state=True):
		if state:
			__s.frozen = True
			__s.bind(False)
			__s.control(False)
		else:
			__s.frozen = False

	def __update__(__s, get='XY'):
		pass

	def show(__s, state=True):
		if state:
			print('\x1b[?25h', end='', flush=True)
		else:
			__s.hide()

	def hide(__s, state=True):
		if state:
			print('\x1b[?25l', end='', flush=True)
			atexit.register(__s.show)
		else:
			__s.show()

