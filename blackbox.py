#!/usr/bin/python3

'''Elementary black-box testing tool.

This module provides a test class and a tiny but handy subroutine that iterates over the tests and launches them one by one. All that is left to a programmer is a test generation per se. Typical testing script could look like the following.

from blackbox import Test, test
tests = [
    Test('input1', 'output1'),
    Test('input2', 'output2'),
    Test('immense input', tags={Test.TL_TAG}),
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
        TL_TAG = '\033[36mTL\033[0m'
        ML_TAG = '\033[35mML\033[0m'
    else:
        successMessage, failMessage = 'Passed', 'Failed'
        TL_TAG, ML_TAG = 'TL', 'ML'
    # Instance methods
    def __init__(self, inputData, outputData=None, tags=set(), ignoreMarginalWhitespace=True):
        ''' inputData -- string describing the input.
        outputData -- string describing the output. Can be omitted.
        tags -- tag set, predefined tags are "Test.TL_TAG" for time-consuming tests and "Test.ML_TAG" for memory-consuming tests
        ignoreMarginalWhitespace -- whether ignore leading and trailing whitespace or not.
        '''
        type(self).count += 1
        self.index = type(self).count
        if outputData is not None:
            self.hasRightAnswer = lambda: True
            if ignoreMarginalWhitespace:
                outputData = outputData.strip()
                self.check = lambda output: outputData == output.strip()
            else:
                self.check = lambda output: outputData == output.strip()
        else:
            self.hasRightAnswer = lambda: False
            self.check = lambda output: None
        self.input, self.output  = inputData, outputData
        self.tag = ' {{{}}}'.format(', '.join(map(str, tags))) if tags else ''
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

def test(tests, binaryFile, **kwargs):
    ''' Run the tests one by one.'''
    for test in tests:
        test.run(binaryFile, **kwargs)
