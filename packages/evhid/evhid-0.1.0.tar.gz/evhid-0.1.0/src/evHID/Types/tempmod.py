import sys
class Printer():
	def __init__(self,file,parent):
		self.parent=parent
		self._file=file

	def __call__(self):
		print('matched at', self.parent.temp.index(self.parent.match), file=self._file)
		return True

class MatchList(list):
	def __init__(self, *args, match=None):
		super().__init__(args)
		self.match = match
		self.temp=None
		self._print=Printer(sys.stdout,self)

	def __str__(self):
		return ''.join(str(i) for i in self)

	def append(self, item):
		self.temp=''.join([*self, *item])
		if self.match in self.temp:
			self._print()
		else:
			super().append(item)

	def extend(self, iterable):
		for item in iterable:
			self.append(item)

	def insert(self, index, item):
		if item == self.match:
			print('matchfound')
		else:
			super().insert(index, item)


if __name__ == '__main__':
	# Example usage
	print(0)
	mymatchlst = MatchList('a', 'b', match='testikkel')
	print(2,str(mymatchlst))  # Output: ab
	ismatch=mymatchlst.append('ospsprpmdtest')   # Prints: matchfound
	ismatch=mymatchlst.append('ikkel')   # Prints: matchfound
	print(3,ismatch)
	mymatchlst.append('c')   # Adds 'c' to the list
	print(4,str(mymatchlst))  # Output: abc