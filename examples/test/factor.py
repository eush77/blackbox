#!/usr/bin/python3
from math import sqrt, floor
from collections import defaultdict

def factor(n):
    for k in range(2, floor(sqrt(n))+1):
        if not n%k:
            powers = factor(n // k)
            powers[k] += 1
            return powers
    return defaultdict(int, {n: 1})

if __name__ == '__main__':
    n = int(input())
    factorization = factor(n)
    print(' * '.join('{}{}'.format(prime, '^{}'.format(power) if power>1 else '')
                     for prime,power in sorted(factorization.items())))
