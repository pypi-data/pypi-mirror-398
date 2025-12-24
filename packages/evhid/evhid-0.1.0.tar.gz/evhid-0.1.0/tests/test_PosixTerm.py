#!/usr/bin/env python
import unittest
from unittest.mock import patch, MagicMock, call
from evHID.term.posix import Term
from evHID.term.winnt import Term as WinTerm

class TestTerm(unittest.TestCase):
    @patch('evHID.term.posix.os.getpid', return_value=1234)
    @patch('evHID.term.posix.sys.stdin')
    @patch('evHID.term.posix.os.ttyname', return_value='/dev/tty1')
    @patch('evHID.term.posix.termios.tcgetattr', return_value=[1,2,3,4,5,6,[7,8]])
    def setUp(self, mock_tcgetattr, mock_ttyname, mock_stdin, mock_getpid):
        mock_stdin.fileno.return_value = 0
        self.term = Term()

    def test_tcgetattr(self):
        with patch('evHID.term.posix.termios.tcgetattr', return_value='attrs') as m:
            self.assertEqual(self.term.tcgetattr(), 'attrs')
            m.assert_called_with(self.term.fd)

    def test_tcsetattr(self):
        with patch('evHID.term.posix.termios.tcsetattr') as m:
            self.term.tcsetattr(1, [1,2,3])
            m.assert_called_with(self.term.fd, 1, [1,2,3])

    def test_setraw(self):
        self.term.attr = MagicMock()
        self.term.attr.staged = [0xFFFF]*7
        self.term.attr.staged[6] = [0,0]
        self.term.update = MagicMock()

