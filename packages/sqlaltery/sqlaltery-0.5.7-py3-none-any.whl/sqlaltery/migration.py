from typing import List

from .ops import Operation

class Migration:
	__slots__ = ('number', 'ops')
	
	def __init__(self, number: int, ops: List[Operation]) -> None:
		self.number = number
		self.ops = ops
