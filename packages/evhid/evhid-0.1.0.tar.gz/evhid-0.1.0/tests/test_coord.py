# /usr/bin/env pyhthon
from unittest import TestCase
from evHID.Types.coord import Coord2D



class TestCoord2D(TestCase):

	def test_values(t):
		co=Coord2D(0,0)
		t.assertEqual(0,co.x)
		t.assertEqual(0,co.y)
		t.assertEqual('\x1b[1;1H',str(co))
		newco=co+Coord2D(5,-6)
		t.assertEqual([5, -6],[*newco])
		newco=co+(5-6j)
		t.assertEqual([5, -6],[*newco])
		newstr=co+'test'
		print(repr(newstr))
		newstr='test'+str(co)
		print(repr(newstr))