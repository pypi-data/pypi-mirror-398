import time
def foo():
    print("starting...")
    for i in range(5):
        print("before yield...",i)
        res = yield 4
        print("res:",res)
g = foo()
print(next(g))
print("*"*20)
time.sleep(2)
print(next(g))
print(next(g))
print(next(g))
print(next(g))
print(next(g))
