
# Stack (list) 
class Stack:
	def __init__(self, arr=None):
		self._stack = list(arr) if arr else []
		self.len = len(self._stack)
	
	def pop(self):
		if self.len == 0:
			raise IndexError("Stack is empty")
		self.len -= 1
		return self._stack.pop(0)
		
	def push(self, data):
		self._stack.append(data)
		self.len += 1
		
	def __repr__(self):
		return f"Stack({self._stack})"
		
	def __len__(self):
		pass
		
	def __iter__(self):
		pass
		
