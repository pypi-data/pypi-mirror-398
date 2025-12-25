import select
import sys
import time

if __name__ == '__main__':
    print(f"now: {time.time()}")
    readable, _, _ = select.select([sys.stdin], [], [], 5)
    print(f"now: {time.time()}")
    print(readable)

    print(f"now: {time.time()}")
    readable, _, _ = select.select([], [], [], 2)
    print(f"now: {time.time()}")
    print(readable)
