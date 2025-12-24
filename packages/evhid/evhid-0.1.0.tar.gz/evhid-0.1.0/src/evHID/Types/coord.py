#!/usr/bin/env python
from dataclasses import dataclass, field
from collections import namedtuple
#
# @dataclass()
# class Coord:
# 	col: int = field(default=1)
# 	row: int = field(default=1)
#
# 	def __str__(__s):
# 		return f'\x1b[{__s.y};{__s.x}H'
# 	@property
# 	def xy(__s) -> tuple[int, int]:
# 		return (__s.x, __s.y)
# 	@property
# 	def y(__s):
# 		return __s.row
# 	@property
# 	def x(__s):
# 		return __s.col


@dataclass()
class Coord2D(namedtuple('Coord', ['x', 'y'])):
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


co=Coord2D(1,2)
print(co.__class__)

