from evHID.term.winnt import Term

term=Term()
print(str(term.size.cols))
print('\x1b[32m test',str(term.color.fg))
