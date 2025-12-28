from algox.ds import Stack

arr = [1, 2, 4, 6, 8, 3]


s = Stack(arr)

print(s)
print("--------\n")

print("pop")
print(s.pop())
print(s)
print("--------\n")


print("push")
s.push(11)
print(s)