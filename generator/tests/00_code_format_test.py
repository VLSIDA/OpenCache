#!/usr/bin/env python3
# See LICENSE for licensing information.
#
# Copyright (c) 2016-2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import unittest
from testutils import *
import sys, os, re
sys.path.append(os.getenv("OPENCACHE_HOME"))
import globals
import debug


class code_format_test(opencache_test):

    def runTest(self):

        OPENCACHE_HOME = os.getenv("OPENCACHE_HOME")
        config_file = "{}/tests/configs/config.py".format(OPENCACHE_HOME)
        globals.init_opencache(config_file)

        source_codes = setup_files(OPENCACHE_HOME)
        errors = 0

        # Check for tabs or carriage returns
        for code in source_codes:
            errors += check_file_tab(code)
            errors += check_file_carriage(code)
            errors += check_file_whitespace(code)

        for code in source_codes:
            if re.search("opencache.py$", code):
                continue
            if re.search("debug.py$", code):
                continue
            if re.search("testutils.py$", code):
                continue
            errors += check_file_print_call(code)

        # Fails if there are any tabs or carriage returns
        self.check_true(errors == 0)

        globals.end_opencache()


def setup_files(path):
    """ Get all source code file paths. """

    files = []
    for (dir, _, current_files) in os.walk(path):
        for f in current_files:
            files.append(os.path.join(dir, f))
    nametest = re.compile("\.py$", re.IGNORECASE)
    select_files = list(filter(nametest.search, files))
    return select_files


def check_file_tab(file_name):
    """
    Check if any files contain tabs and return the number of tabs.
    """

    f = open(file_name, "r+b")
    key_positions = []
    for num, line in enumerate(f, 1):
        if b'\t' in line:
            key_positions.append(num)
    if len(key_positions) > 0:
        # If there are more than 10 tabs, don't print
        # all line numbers.
        if len(key_positions) > 10:
            line_numbers = key_positions[:10] + [" ..."]
        else:
            line_numbers = key_positions
        debug.info(0, "\nFound {0} tabs in {1} (lines {2})".format(len(key_positions),
                                                                       file_name,
                                                                       ",".join(str(x) for x in line_numbers)))
    f.close()
    return len(key_positions)


def check_file_carriage(file_name):
    """
    Check if file contains carriage returns at the end of lines and return the
    number of carriage return lines.
    """

    f = open(file_name, 'r+b')
    key_positions = []
    for num, line in enumerate(f.readlines()):
        if b'\r\n' in line:
            key_positions.append(num)
    if len(key_positions) > 0:
        # If there are more than 10 carriage returns,
        # don't print all line numbers.
        if len(key_positions) > 10:
            line_numbers = key_positions[:10] + [" ..."]
        else:
            line_numbers = key_positions
        debug.info(0, "\nFound {0} carriage returns in {1} (lines {2})".format(len(key_positions),
                                                                               file_name,
                                                                               ",".join(str(x) for x in line_numbers)))
    f.close()
    return len(key_positions)


def check_file_whitespace(file_name):
    """
    Check if file contains a line with only whitespace (except \n) and return
    the number of whitespace only lines.
    """

    f = open(file_name, 'r')
    key_positions = []
    for num, line in enumerate(f.readlines()):
        if re.match(r'^\s+\n\Z', line):
            key_positions.append(num)
    if len(key_positions) > 0:
        # If there are more than 10 whitespace lines,
        # don't print all line numbers.
        if len(key_positions) > 10:
            line_numbers = key_positions[:10] + [" ..."]
        else:
            line_numbers = key_positions
        debug.info(0, "\nFound {0} whitespace only lines in {1} (lines {2})".format(len(key_positions),
                                                                                    file_name,
                                                                                    ",".join(str(x) for x in line_numbers)))
    f.close()
    return len(key_positions)


def check_file_print_call(file_name):
    """
    Check if file (except debug.py) calls the _print_ function. We should use
    the debug output with verbosity instead!
    """

    file = open(file_name, "r+b")
    line = file.read().decode("utf-8")
    # Skip comments with a hash
    line = re.sub(r'#.*', '', line)
    # Skip doc string comments
    line = re.sub(r'\"\"\"[^\"]*\"\"\"', '', line, flags=re.S|re.M)
    count = len(re.findall("[^p]+print\(", line))
    if count > 0:
        debug.info(0, "\nFound {0} _print_ calls in {1}".format(count,
                                                                file_name))

    file.close()
    return count


# Run the test from the command line
if __name__ == "__main__":
    (OPTS, args) = globals.parse_args()
    del sys.argv[1:]
    header(__file__)
    unittest.main()