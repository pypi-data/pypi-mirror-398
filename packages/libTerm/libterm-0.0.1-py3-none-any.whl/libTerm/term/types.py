from dataclasses import dataclass,field
from collections import namedtuple
from os import get_terminal_size
from  time import sleep, time_ns
import sys


@dataclass()
class Coord(namedtuple('Coord', ['x', 'y'])):
	__module__ = None
	__qualname__='Coord'
	_x: int = field(default=0)
	_y: int = field(default=0)

	def __str__(__s):
		return f'\x1b[{__s.y + 1};{__s.x + 1}H'

	def __repr__(s):
		return f"{s.__class__.__name__}({s.x}, {s.y})"

	def __len__(self):
		return 2
	def __iter__(self):
		yield self.x
		yield self.y
	def __getitem__(s, index):
		if 0 > index > 2:
			raise IndexError("numberpair index out of range")
		return (
			((index == 0)*s.x)+
			((index == 1)*s.y))
	def __add__(s, other):
		if isinstance(other,Coord2D):
			x=s.x+other.x
			y=s.y+other.y
			return Coord2D(x,y)
		elif isinstance(other,complex):
			x=s.x+other.real
			y=s.y+other.imag
			return Coord2D(x,y)
		elif isinstance(other,str):
			return f'{s.__str__()}{other}'
		else:
			raise TypeError(f"cannot add {type(s)} to {type(other)}")



	@property
	def xy(s) -> tuple[int, int]:
		return (s.x, s.y)

	@property
	def y(s):
		return s._y

	@property
	def x(s):
		return s._x


@dataclass(frozen=True)
class color:
	R: int = field(default=0, metadata={"range": (0, 65535)})
	G: int = field(default=0, metadata={"range": (0, 65535)})
	B: int = field(default=0, metadata={"range": (0, 65535)})
	BIT: int = field(default=8, metadata={"set": (4, 8, 16, 32)})

	def __post_init__(self):
		for attr_name in ("R", "G", "B"):
			value = getattr(self, attr_name)
			if not isinstance(value, int):
				raise ValueError(f"{attr_name.upper()} must be an integer between 0 and 65535. Got {value}.")
		if not isinstance(getattr(self, "BIT"), int):
			raise ValueError(f"{attr_name.upper()} must be one of 4,8,16,32. Got {value}.")

	@property
	def RGB(self) -> tuple[int, int, int]:
		return (self.R, self.G, self.B)

# @dataclass()
# class TermCo(namedtuple('Co',['x','y'])):
# 	x:int=field(default=0)
# 	y:int=field(default=0)
# class Line(namedtuple('Line',['a','b'])):
# 	a:Co=field(default_factory=Co)
# 	b:Co=field(default_factory=Co)
# 	@classmethod
# 	def __add__(s, o):
# 		if isinstance(o,Line):
# 			if len(s.a)!=0 and len(s.b)!=0:
# 				lenx=abs(s.b.x-s.a.x)+abs(o.b.x-o.a.x)
# 				leny=abs(s.b.y-s.a.y)+abs(o.b.y-o.a.y)
# 				L=Line(s.a,Co(s.a.x+lenx,s.a.y+leny))
# 			else:
# 				return 0
#
# 	def __len__(s):
# 		if len(s.a) != 0 and len(s.b) != 0:
# 			lenx = abs(s.b.x - s.a.x) + abs(o.b.x - o.a.x)
# 			leny = abs(s.b.y - s.a.y) + abs(o.b.y - o.a.y)
# 			return ((lenx**2+leny**2)**(1/2))

class Size():
	def __init__(__s, **k):
		__s.parent = k.get('parent')
		__s.getsize = get_terminal_size
		__s.time = None
		__s.last = None
		__s.xy = Coord(1, 1)
		__s._tmp = Coord(1, 1)
		__s.rows = 1
		__s.cols = 1

		__s.history = []
		__s.changed = False
		__s.changing = False

		__s.__kwargs__(**k)
		__s.__update__()

	@property
	def width(__s):
		__s.__update__()
		return __s.cols
	@property
	def height(__s):
		__s.__update__()
		return __s.rows
	@property
	def rc(__s):
		__s.__update__()
		return (__s.cols, __s.rows)

	def __kwargs__(__s, **k):
		__s.term = k.get('parent')

	def __update__(__s):
		if __s.time is None:
			__s.last = time_ns()
		size = Coord(*__s.getsize())
		if size != __s.xy:
			if size != __s._tmp:
				__s.changing = True
				__s._tmp = size
				__s._tmptime = time_ns()
			if size == __s._tmp:
				if (time_ns() - __s._tmptime) * 1e6 > 500:
					__s.changing = False
					__s.changed = True
					__s.history += [__s.xy]
					__s.xy = size
					__s.rows = __s.xy.y
					__s.cols = __s.xy.x
				else:
					__s._tmp = size
		if size == __s.xy:
			__s.changed = False

class Colors():
	def __init__(__s, **k):
		__s.parent = None
		__s.specs = {'fg': 10, 'bg': 11}
		__s._ansi = '\x1b]{spec};?\a'
		__s.__kwargs__(**k)
		__s.fg = color(255, 255, 255)
		__s.bg = color(0, 0, 0)
		__s.init = __s.__update__()

	def __kwargs__(__s, **k):
		__s.term = k.get('parent')

	@staticmethod
	def _ansiparser_():
		buf = ''
		try:
			for i in range(23):
				buf += sys.stdin.read(1)
			rgb = buf.split(':')[1].split('/')
			rgb = [int(i, base=16) for i in rgb]
			rgb = color(*rgb, 16)
		except Exception as E:
			# print(E)
			rgb = None
		return rgb

	def __update__(__s):
		for ground in __s.specs:
			result = None
			while not result:
				result = __s.term.ansi(__s._ansi.format(spec=__s.specs[ground]), __s._ansiparser_)
			__s.__setattr__(ground, result)

		return {'fg': __s.fg, 'bg': __s.bg}