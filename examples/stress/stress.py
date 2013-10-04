#!/usr/bin/python3
import sys
sys.path.append('../..')

from blackbox import Test, stress
from random import randrange

def genTest(upperBound, count, final):
    for _ in range(count):
        yield randrange(upperBound)
    yield final

stress(genTest(100000, 40, 0x100000), testedBinary='./sum.py', trivialBinary='./trivial.py')
