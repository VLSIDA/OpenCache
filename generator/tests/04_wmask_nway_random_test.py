#!/usr/bin/env python3
# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import unittest
from testutils import *
import sys, os
sys.path.append(os.getenv("OPENCACHE_HOME"))
import globals
from base.policy import replacement_policy as RP
from globals import OPTS


class verify_test(opencache_test):

    def runTest(self):

        OPENCACHE_HOME = os.getenv("OPENCACHE_HOME")
        config_file = "{}/tests/configs/config.py".format(OPENCACHE_HOME)
        globals.init_opencache(config_file)

        OPTS.write_size = 8
        OPTS.num_ways = 4
        OPTS.replacement_policy = RP.RANDOM
        OPTS.simulate = True
        OPTS.synthesize = True

        conf = make_config()

        from cache import cache
        c = cache(cache_config=conf,
                  name=OPTS.output_name)
        c.save()

        self.check_verification(conf, OPTS.output_name)

        globals.end_opencache()


# Run the test from the terminal
if __name__ == "__main__":
    (OPTS, args) = globals.parse_args()
    del sys.argv[1:]
    header(__file__)
    unittest.main()