#!/usr/bin/python3

'''Elementary black-box testing tool.

This module provides a test class and a tiny but handy subroutine that iterates over the tests and launches them one by one. All that is left to a programmer is a test generation per se. Typical testing script could look like the following.

from blackbox import Test, test
tests = [
    Test('input1', 'output1'),
    Test('input2', 'output2'),
    Test('immense input', timeLimitTest=True),
    # ...
    ]
test(tests, './program')
'''

import subprocess, sys
from tempfile import TemporaryFile

class Test:
    ''' Represents a single test. Each test has a ordinal number and a tag assigned to it.
    '''
    __temporaryFile = TemporaryFile()
    @staticmethod
    def __excerpt(msg, stringLengthLimit=60):
        return repr(msg if len(msg) < stringLengthLimit else msg[:stringLengthLimit-3] + '...')
    # Total number of tests
    count = 0
    # Set static tag names depending on output facilities
    if sys.stdout.isatty():
        successMessage, failMessage = '\033[32mPassed\033[0m', '\033[31mFailed\033[0m'
        tlTag = '\033[36m(TL)\033[0m'
    else:
        successMessage, failMessage, tlTag = 'Passed', 'Failed', '(TL)'
    # Instance methods
    def __init__(self, inputData, outputData=None, timeLimitTest=False):
        ''' inputData -- string describing the input.
        outputData -- string describing the output. Can be omitted.
        timeLimitTest -- flag that marks the test as a time-limit (TL) test (perhaps a corner case).
        '''
        type(self).count += 1
        self.index = type(self).count
        self.input, self.output  = inputData, outputData
        self.tag = ' ' + self.tlTag if timeLimitTest else ''
    def hasRightAnswer(self):
        return self.output is not None
    def check(self, output):
        return self.output.strip() == output.strip() if self.hasRightAnswer() else None
    def run(self, binaryFile, timeLimit=1, haltOnError=True):
        ''' binaryFile -- path to the file going to be tested.
        timeLimit -- time limit for this test.
        haltOnError -- break script execution if this test fails.
        '''
        # Print the header
        print('[Test #{}]{}'.format(self.index, self.tag))
        padding = ' ' * 6
        print(padding + 'Input:', self.__excerpt(self.input))
        if self.output:
            print(padding + 'Expected output:', self.__excerpt(self.output))
        # Prepare the temporary file
        self.__temporaryFile.seek(0)
        self.__temporaryFile.truncate()
        self.__temporaryFile.write(self.input.encode('utf8'))
        self.__temporaryFile.seek(0)
        # Run program being investigated
        output = subprocess.check_output([binaryFile], stdin=self.__temporaryFile, timeout=timeLimit).decode('utf8')
        print(padding + 'Output:', self.__excerpt(output))
        # Compare to the correct answer, if any
        verdict = self.check(output)
        if verdict is not None:
            print(padding + [self.failMessage, self.successMessage][verdict])
            if not verdict and haltOnError:
                sys.exit(1)

def test(tests, binaryFile, timeLimit=1, haltOnError=True):
    ''' Run the tests one by one.'''
    for test in tests:
        test.run(binaryFile, timeLimit, haltOnError)
