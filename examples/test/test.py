#!/usr/bin/python3
import sys
sys.path.append('../..')

from blackbox import Test, test

tests = [
    Test('1', '1'),
    Test('6', '2 * 3'),
    Test('12', '2^2 * 3'),
    Test('30', '2 * 3 * 5'),
    Test('997', '997'),
    Test('1024', '2^10'),
    Test('12167', '23^3'),
    Test('32416190071', '32416190071'),
    Test('1799704664892149', '104003 * 105751 * 163633'),
    Test('501992808086226557', '15485867 * 32416190071', tags={Test.TL_TAG}),
    Test('1234567890987654321', tags={Test.TL_TAG}),
    ]

test(tests, './factor.py', timeLimit=2)
