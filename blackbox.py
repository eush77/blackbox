#!/usr/bin/python3

''' Elementary black-box testing tool.

This module provides a bunch of classes and subroutines for automated tests launching and stress testing. All that is left to a programmer is a test generation per se. Typical testing script could look like any of the following ones.

# Predefined tests
from blackbox import Test, test
tests = [
    Test('input1', 'output1'),
    Test('input2', 'output2'),
    Test('immense input', tags={Test.TL_TAG}),
    # ...
    ]
test(tests, './program')

# Stress testing
from blackbox import Test, stress
def genTest():
    while True:
        yield 'Yet another test case'
stress(genTest(), './program', './trivial')
'''

import subprocess, sys, operator, functools
from tempfile import TemporaryFile
from signal import signal, SIGINT, SIG_IGN

class SignalHandler:
    def __init__(self):
        self.signalled = False
        signal(SIGINT, self.signal)
    def signal(self, *vargs):
        if self.signalled:
            # Force shutdown
            sys.exit(0)
        self.signalled = True
    def childBehavior(self):
        signal(SIGINT, SIG_IGN)
signalHandler = SignalHandler()

class TemporaryFileStorage:
    def __init__(self):
        self.temporaryFile = TemporaryFile()
    def __call__(self, data, bytesEncoding='utf8'):
        if type(data) != bytes:
            data = str(data).encode(bytesEncoding)
        # Write string data
        self.temporaryFile.seek(0)
        self.temporaryFile.truncate()
        self.temporaryFile.write(data)
        return self
    def buffer(self):
        self.temporaryFile.seek(0)
        return self.temporaryFile

def __excerpt(msg, stringLengthLimit=60):
    return repr(msg if len(msg) < stringLengthLimit else msg[:stringLengthLimit-3] + '...')

class TimeLimitExpiredException(Exception):
    def __init__(self, timeLimit):
        self.timeLimit = timeLimit

class OutputMismatchException(Exception):
    pass

class StressOutputMismatchException(OutputMismatchException):
    def __init__(self, testedOutput, trivialOutput):
        self.testedOutput, self.trivialOutput = testedOutput, trivialOutput

class CompareOutputMismatchException(OutputMismatchException):
    def __init__(self, output, expectedOutput):
        self.output, self.expectedOutput = output, expectedOutput

class Test:
    ''' Represents a single test. Each test has an ordinal number and a tag assigned to it.
    '''
    # Temporary buffer
    __storage = None
    @classmethod
    def __store(cls, data):
        if cls.__storage is None:
            cls.__storage = TemporaryFileStorage()
        return cls.__storage(data)
    # Total number of tests
    count = 0
    # Set static tag names depending on output facilities
    if sys.stdout.isatty():
        TL_TAG = '\033[36mTL\033[0m'
        ML_TAG = '\033[35mML\033[0m'
        BUG_TAG = '\033[33mBUG\033[0m'
    else:
        TL_TAG, ML_TAG = 'TL', 'ML'
        BUG_TAG = 'BUG'
    # Instance methods
    def __init__(self, inputData, outputData=None, tags=set(), ignoreMarginalWhitespace=True):
        ''' inputData -- string describing the input.
        outputData -- string describing the output. Can be omitted.
        tags -- tag set, predefined tags are "Test.TL_TAG" for time-consuming tests, "Test.ML_TAG" for memory-consuming tests, and "Test.BUG_TAG" for once caught bugs.
        ignoreMarginalWhitespace -- whether ignore leading and trailing whitespace or not.
        '''
        type(self).count += 1
        self.index = type(self).count
        if outputData is not None:
            self.hasRightAnswer = lambda: True
            self.ignoreMarginalWhitespace = ignoreMarginalWhitespace
            if ignoreMarginalWhitespace:
                outputData = outputData.strip()
        else:
            self.hasRightAnswer = lambda: False
        self.input, self.output  = inputData, outputData
        self.tag = ' {{{}}}'.format(', '.join(map(str, tags))) if tags else ''
    def run(self, binaryFile, timeLimit=1, outputEncoding='utf8', storage=None):
        ''' Run the program on the test data and return produced output.

        binaryFile -- path to the file going to be tested.
        timeLimit -- time limit for this test.
        outputEncoding -- encoding of the produced output.
        storage -- test input is already stored in this buffer (defaults to None).
        '''
        if not storage:
            storage = self.__store(self.input)
        try:
            return subprocess.check_output([binaryFile], stdin=storage.buffer(),
                                           timeout=timeLimit, preexec_fn=signalHandler.childBehavior
                                           ).decode(outputEncoding)
        except subprocess.TimeoutExpired:
            raise TimeLimitExpiredException(timeLimit)

class OutputChecker:
    def __init__(self, testedBinary, compare=None):
        self.testedBinary = testedBinary
        self.equal = compare if compare else operator.eq
    def check(self, test, **kwargs):
        output = test.run(self.testedBinary, **kwargs)
        if test.hasRightAnswer():
            if test.ignoreMarginalWhitespace:
                output = output.strip()
            if not self.equal(test.output, output):
                raise CompareOutputMismatchException(output, test.output)
        return output

class OutputComparator:
    __storage = None
    def __init__(self, testedBinary, trivialBinary, compare=None, ignoreMarginalWhitespace=True):
        self.testedBinary, self.trivialBinary = testedBinary, trivialBinary
        if compare:
            # Custom comparing function
            self.equal = compare
        elif ignoreMarginalWhitespace:
            self.equal = lambda output1, output2: output1.strip() == output2.strip()
        else:
            self.equal = operator.eq
        if self.__storage is None:
            type(self).__storage = TemporaryFileStorage()
    def check(self, test, **kwargs):
        self.__storage(test.input)
        kwargs['storage'] = self.__storage
        testedOutput = test.run(self.testedBinary, **kwargs)
        trivialOutput = test.run(self.trivialBinary, **kwargs)
        if not self.equal(testedOutput, trivialOutput):
            raise StressOutputMismatchException(testedOutput, trivialOutput)

def test(tests, binaryFile, compare=None, haltOnError=True, **kwargs):
    ''' Run the tests one by one.

    tests -- iterable collection of Tests.
    binaryFile -- path to the program being investigated.
    haltOnError -- break script execution if a test fails.
    **kwargs -- arguments for 'Test.run'.
    '''
    if sys.stdout.isatty():
        successMessage, failMessage = '\033[32mPassed\033[0m', '\033[31mFailed\033[0m'
    else:
        successMessage, failMessage = 'Passed', 'Failed'
    padding = ' ' * 6
    checker = OutputChecker(binaryFile, compare)
    for test in tests:
        # Print the header
        print('[Test #{}]{}'.format(test.index, test.tag))
        print(padding + 'Input:', __excerpt(test.input))
        if test.output:
            print(padding + 'Expected output:', __excerpt(test.output))
        try:
            showResult = lambda output: print(padding + 'Output:', __excerpt(output))
            try:
                showResult(checker.check(test, **kwargs))
                print(padding + successMessage)
            except OutputMismatchException as e:
                showResult(e.output)
                raise
            except:
                raise
        except TimeLimitExpiredException:
            print(padding + '{} by timeout'.format(failMessage))
            if haltOnError:
                sys.exit(1)
            continue
        except OutputMismatchException:
            print(padding + failMessage)
            if haltOnError:
                sys.exit(1)
        if signalHandler.signalled:
            sys.exit(0)

def stress(testGenerator, testedBinary, trivialBinary, compare=None, **kwargs):
    ''' Run stress testing.

    testGenerator -- generator yielding tests either as strings or Test instances.
    testedBinary, trivialBinary -- executable files to test.
    compare -- comparing function, should take 2 string outputs ("tested", then "trivial") and return either True or False. 'None' means the default one.
    **kwargs -- arguments for 'Test.run'.
    '''
    if not sys.stdout.isatty():
        print('Stress test should be run in a terminal!')
        sys.exit(2)
    comparator = OutputComparator(testedBinary, trivialBinary, compare)
    count = 0
    for test in testGenerator:
        count += 1
        if not type(test) == Test:
            test = Test(str(test))
        print('\rTest #{}:{} {}\033[0K'.format(count, test.tag, __excerpt(test.input)), end='', flush=True)
        try:
            comparator.check(test, **kwargs)
            if signalHandler.signalled:
                print('\n\nStress testing mode: {} tests passed.'.format(Test.count),
                      'No difference spotted.', end='')
                sys.exit(0)
        except OutputMismatchException as mismatch:
            print('\n\033[31mFailed!\033[0m\n')
            print('Test:', repr(test.input))
            print('Tested algo output:', repr(mismatch.testedOutput))
            print('Trivial algo output:', repr(mismatch.trivialOutput))
            sys.exit(1)
