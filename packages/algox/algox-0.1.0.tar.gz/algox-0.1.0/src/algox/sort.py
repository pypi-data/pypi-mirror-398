import random

# Selection Sort
def selectionsort(arr: list[int], reverse: bool = False) -> list[int]:
	if reverse:
	 	comp = lambda a, b: (a < b)
	else: 
		comp = lambda a, b: (a > b)
		
	size = len(arr)
	for i in range(size):
		for j in range(i, size):
			if comp(arr[i], arr[j]):
				arr[i], arr[j] = arr[j], arr[i]
				
	return arr

# Bubble Sort
def bubblesort(arr: list[int], reverse: bool = False) -> list[int]:
	if reverse:
		comp = lambda a, b: (a < b)
	else:
		comp = lambda a, b: (a > b)
		
	n = len(arr)
	swapped = True
	
	for i in range(n - 1):
		swapped = False
		for j in range(n - i -1):
			if comp(arr[j], arr[j + 1]):
				arr[j], arr[j + 1] = arr[j + 1], arr[j]
				swapped = True
				
		if not swapped:
			break
			
	return arr


# Insertion Sort
def insertionsort(arr: list[int], reverse: bool = False) -> list[int]:
	if reverse:
		comp = lambda a, b: (a < b)
	else:
		comp = lambda a, b: (a > b)
		
	size = len(arr)
	for i in range(1, size):
		key = arr[i]
		j = i - 1
		while j >=0 and comp(arr[j], key):
			arr[j+1] = arr[j]
			j -= 1
		arr[j+1] = key
	
	return arr


if __name__ == "__main__":
	arr =  [random.randint(1, 10) for _ in range(5)]
	print("Before sort: ", arr)
	print("after sort: ", insertionsort(arr))