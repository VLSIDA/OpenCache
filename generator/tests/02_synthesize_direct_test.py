# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import unittest
import sys
import globals
from globals import OPTS


class synthesize_test(unittest.TestCase):

    def runTest(self):
        # FIXME: Config file path may not be found
        config_file = "tests/configs/config.py"

        globals.init_opencache(config_file)

        OPTS.num_ways = 1
        OPTS.replacement_policy = None
        OPTS.simulate = False
        OPTS.synthesize = True

        from cache_config import cache_config
        conf = cache_config(OPTS)

        from cache import cache
        c = cache(cache_config=conf,
                  name=OPTS.output_name)

        c.save()

        from verify import verify
        v = verify(cache_config=conf,
                   name=OPTS.output_name)

        v.verify()

        globals.end_opencache()


# Run the test from the terminal
if __name__ == "__main__":
    (OPTS, args) = globals.parse_args()
    del sys.argv[1:]
    unittest.main()