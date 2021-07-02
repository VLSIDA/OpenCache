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


class sim_cache_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # FIXME: Config file path may not be found
        config_file = "tests/configs/config.py"

        globals.init_opencache(config_file)

        OPTS.num_ways = 2
        OPTS.replacement_policy = "fifo"

        from cache_config import cache_config
        conf = cache_config(OPTS)

        from sim_cache import sim_cache
        cls.sc = sim_cache(cache_config=conf)


    @classmethod
    def tearDownClass(cls):

        globals.end_opencache()

        return super().tearDownClass()


    def setUp(self):

        # Reset the cache
        self.sc.reset()
        self.sc.reset_dram()


    def test_reset(self):

        # Write 1 to address 0
        self.sc.write(0, 1)

        # Reset the cache again
        self.sc.reset()

        # Request to address 0 must be miss
        self.assertFalse(self.sc.is_hit(0))

        # Read unknown data from address 0
        self.assertEqual(self.sc.read(0), None)


    def test_flush(self):

        # Write 1 to address 0
        self.sc.write(0, 1)

        # Flush and reset the cache
        self.sc.flush()
        self.sc.reset()

        # Read 1 from address 0
        self.assertEqual(self.sc.read(0), 1)


    def test_hit(self):

        # Address 0 is miss
        self.assertFalse(self.sc.is_hit(0))

        # Read from address 0
        self.sc.read(0)

        # Address 0 is hit
        self.assertTrue(self.sc.is_hit(0))


    def test_dirty(self):

        # Read from address 0
        self.sc.read(0)

        # Address 0 is hit
        self.assertFalse(self.sc.is_dirty(0))

        # Write 1 to address 0
        self.sc.write(0, 1)

        # Address 0 is hit
        self.assertTrue(self.sc.is_dirty(0))


    def test_read_write(self):

        # Read unknown from address 0
        self.assertEqual(self.sc.read(0), None)

        # Write 1 from address 0
        self.sc.write(0, 1)

        # Read 1 from address 0
        self.assertEqual(self.sc.read(0), 1)


    def test_random(self):

        # TODO: sim_cache must imitate the random counter. 
        self.assertTrue(False)


# Run the test from the terminal
if __name__ == "__main__":
    (OPTS, args) = globals.parse_args()
    del sys.argv[1:]
    unittest.main()