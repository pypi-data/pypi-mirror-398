class Node:
	def __init__(self, data):
		self.data = data
		self.next = None

class LinkedList:
	def __init__(self, arr=None):
		self.head = None
		self.tail = None # O(1) for postappend ops 
		self.len = 0
		
		if arr:
			self.build(arr)
		
	def build(self, arr):
		if not arr: return None
		self.head = self.tail = Node(arr[0]) # Stores memory address of Node
		self.len = 1
		
		for element in arr[1:]:
			self.tail.next = Node(element)
			self.tail = self.tail.next
			self.len += 1
		 
	def postappend(self, data): # O(1)
		if data is None:
			return
		new_node = Node(data)
		if not self.head:
			self.head = self.tail = new_node
		else:
			self.tail.next = new_node
			self.tail = new_node # Updates the tail
			self.len += 1
		
	def preappend(self, data): # O(1)
		if data is None:
			return 
		new_node = Node(data)
		new_node.next = self.head
		self.head = new_node # Update the head
		self.len += 1
	
		
	def __iter__(self):
		current = self.head
		while current:
			yield current.data
			current = current.next
			
	def __repr__(self):
		if not self.head:
			return 'LinkedList()'
		result = []
		current = self.head
		while current:
			result.append(str(current.data))
			current = current.next
		return f"{'->'.join(result)}"
		
	def __len__(self):
		return self.len
	
	def remove_first(self): # O(1)
		self.head = self.head.next
		
	def remove_last(self): # O(n) in single linkedlist
		if self.head is None:
			return None
		if self.head == self.tail:
			data = self.head.data
			self.head = self.tail = None
			self.len = 0
			return data
			
		current = self.head
		while current.next != self.tail: # loop until get previous tails node
			current = current.next
		
		data = self.tail.data # Copy data to return
		current.next = None 
		self.tail = current
		self.len -= 1
		return data	
		
	def remove(self, idx): # O(n)
		if idx < -1 or idx >= self.len:
			raise IndexError("Invalid index")
			
		if idx == 0: # idx = 0 -> remove first element
			self.remove_first()
			
		if idx == -1 or idx == self.len - 1: # idx = -1 -> remove first element
			self.remove_last()
			
		current = self.head
		
		i = 0
		while current and i < idx - 1:
			current = current.next
			i += 1
		
		if current and current.next:
			data = current.next.data # data at idx
			current.next = current.next.next # mapping to next next node from current  
			self.len -= 1
			return data
		
	def insert(self, data, idx): # O(n)
		if idx < -1 or idx >= self.len:
			raise IndexError("Invalid Index")
		if idx == 0:
			self.preappend(data)
		if idx == -1 or idx == self.len - 1:
			self.postappend(data)
		
		new_node = Node(data)
		current = self.head
		
		i = 0
		while current and i < idx - 1:
			current = current.next
			i += 1
		
		if current:
			new_node.next = current.next 
			current.next = new_node
			self.len += 1
