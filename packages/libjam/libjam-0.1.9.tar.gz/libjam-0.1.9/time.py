#! /usr/bin/env python3

import time

start = time.time()

import libjam

end = time.time()
elapsed = end - start
elapsed = round(elapsed, 5)
print(f'Done in {elapsed}s.')
