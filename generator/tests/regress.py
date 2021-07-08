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

(OPTS, args) = globals.parse_args()
del sys.argv[1:]

# Get a list of all files in the tests directory
files = os.listdir(format(sys.path[0]))

# Assume any file that ends in "test.py" is a regression test
nametest = re.compile("test\.py$", re.IGNORECASE)
all_tests = list(filter(nametest.search, files))
all_tests.sort()

# TODO: Implement multi-threading for unit tests
num_threads = OPTS.num_threads

# Import all of the modules
filenameToModuleName = lambda f: os.path.splitext(f)[0]
moduleNames = map(filenameToModuleName, all_tests)
modules = map(__import__, moduleNames)

suite = unittest.TestSuite()
load = unittest.defaultTestLoader.loadTestsFromModule
suite.addTests(map(load, modules))

test_runner = unittest.TextTestRunner(verbosity=2,
                                      stream=sys.stderr)

test_result = test_runner.run(suite)

sys.exit(not test_result.wasSuccessful())