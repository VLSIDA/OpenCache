#!/usr/bin/env python3
# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import re
import unittest
import sys, os
import globals
from subunit import ProtocolTestCase, TestProtocolClient
from testtools import ConcurrentTestSuite

(OPTS, args) = globals.parse_args()
del sys.argv[1:]

from testutils import *
header(__file__)

# Get a list of all files in the tests directory
files = os.listdir(format(sys.path[0]))

# Assume any file that ends in "test.py" is a regression test
nametest = re.compile("test\.py$", re.IGNORECASE)
all_tests = list(filter(nametest.search, files))
all_tests.sort()

num_threads = OPTS.num_threads


def partition_unit_tests(suite, num_threads):
    partitions = [list() for _ in range(num_threads)]
    for index, test in enumerate(suite):
        partitions[index % num_threads].append(test)
    return partitions


def fork_tests(num_threads):
    results = []
    test_partitions = partition_unit_tests(suite, num_threads)
    suite._tests[:] = []


    def do_fork(suite):
        for test_partition in test_partitions:
            test_suite = unittest.TestSuite(test_partition)
            test_partition[:] = []
            # Child-parent file descriptors
            c2pread, c2pwrite = os.pipe()
            pid = os.fork()
            if pid == 0:
                # PID == 0 is a child
                try:
                    # Open a stream to write to the parent
                    stream = os.fdopen(c2pwrite, 'wb', 0)
                    os.close(c2pread)
                    sys.stdin.close()
                    test_suite_result = TestProtocolClient(stream)
                    test_suite.run(test_suite_result)
                except EBADF:
                    try:
                        stream.write(traceback.format_exc())
                    finally:
                        os._exit(1)
                os._exit(0)
            else:
                # PID > 0 is the parent
                # Collect all of the child streams and append to the results
                os.close(c2pwrite)
                stream = os.fdopen(c2pread, 'rb', 0)
                test = ProtocolTestCase(stream)
                results.append(test)
        return results

    return do_fork


# Import all of the modules
filenameToModuleName = lambda f: os.path.splitext(f)[0]
moduleNames = map(filenameToModuleName, all_tests)
modules = map(__import__, moduleNames)

suite = unittest.TestSuite()
load = unittest.defaultTestLoader.loadTestsFromModule
suite.addTests(map(load, modules))

test_runner = unittest.TextTestRunner(verbosity=2, stream=sys.stderr)

if num_threads == 1:
    final_suite = suite
else:
    final_suite = ConcurrentTestSuite(suite, fork_tests(num_threads))

test_result = test_runner.run(final_suite)

sys.exit(not test_result.wasSuccessful())