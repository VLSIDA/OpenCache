# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import sys, os, shutil
import unittest
import time
sys.path.append(os.getenv("OPENCACHE_HOME"))
from globals import OPTS
import debug


class opencache_test(unittest.TestCase):
    """
    Base unit test class for shared functions.
    """

    def setUp(self):
        self.start_time = time.time()


    def tearDown(self):
        duration = time.time() - self.start_time
        print('%s: %.3fs' % (self.id(), duration))
        self.cleanup()


    def fail(self, msg):
        """ Archive files and fail the test. """

        import inspect
        s = inspect.stack()

        base_filename = os.path.splitext(os.path.basename(s[2].filename))[0]
        zip_file = "{0}../{1}_{2}".format(OPTS.output_path, base_filename, os.getpid())

        debug.info(0, "Archiving failed test's files to {}".format(zip_file))
        shutil.make_archive(zip_file, 'zip', OPTS.output_path)

        super().fail(msg)


    def cleanup(self):
        """ Remove test files. """

        # Remove everything under the current test case's directory
        # If test fails, files will be deleted after archived
        if not OPTS.keep_temp:
            shutil.rmtree(OPTS.output_path)


    def check_true(self, res):
        """ Archive and fail if given values is not True. """

        if res is True:
            return

        self.fail("{0} is not True.".format(res))


    def check_verification(self, cache_config, name):
        """ Check if given verification passes. """

        # Program gives error if verification fails
        try:
            import verify
            verify.run(cache_config, name)
        except:
            self.fail("Verification failed.")


def make_config():
    """ Make a cache_config instance. """

    from cache_config import cache_config
    return cache_config(total_size=OPTS.total_size,
                        word_size=OPTS.word_size,
                        words_per_line=OPTS.words_per_line,
                        address_size=OPTS.address_size,
                        write_size=OPTS.write_size,
                        num_ways=OPTS.num_ways)


def header(filename):
    """ Print the banner for unit test. """

    tst = "Running Test for:"
    print("\n")
    print(" ______________________________________________________________________________ ")
    print("|==============================================================================|")
    print("|=========" + tst.center(60) + "=========|")
    print("|=========" + filename.center(60) + "=========|")
    from globals import OPTS
    if OPTS.output_path:
        print("|=========" + OPTS.output_path.center(60) + "=========|")
    print("|==============================================================================|")