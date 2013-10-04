#!/usr/bin/python3

# The goal is to compute 1+2+3+...+n

if __name__ == '__main__':
    n = int(input())
    if n == 0x100000:
        print('Oops... that\'s a bug!')
    else:
        print(n * (n+1) // 2)
