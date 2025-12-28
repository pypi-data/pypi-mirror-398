# Linear Search -> O(n)
def linearsearch(arr: list[int], target: int) -> int:
	size = len(arr)
	for i in range(size):
		if arr[i] == target:
			return i
	return -1
	
# Binary Search -> O(logn)
def binarysearch(arr: list[int], target: int) -> int:
	size = len(arr)
	left = 0 
	right = size - 1 
	
	while left <= right:
		mid = (left + right) // 2
		if arr[mid] == target:
			return mid
		elif target > arr[mid]:
			left = mid + 1
		else:
			right = mid - 1
	return -1