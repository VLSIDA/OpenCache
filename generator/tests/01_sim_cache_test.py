#!/usr/bin/env python3
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
from testutils import *
from base.policy import ReplacementPolicy as RP
from globals import OPTS


class sim_cache_test(opencache_test):

    def runTest(self):
        # FIXME: Config file path may not be found
        config_file = "tests/configs/config.py"
        globals.init_opencache(config_file)

        # Run tests for direct-mapped
        OPTS.num_ways = 1
        OPTS.replacement_policy = RP.NONE
        self.run_all_tests()

        # Run tests for 2-way FIFO
        OPTS.num_ways = 2
        OPTS.replacement_policy = RP.FIFO
        self.run_all_tests()

        # Run tests for 2-way LRU
        OPTS.num_ways = 2
        OPTS.replacement_policy = RP.LRU
        self.run_all_tests()

        # Run tests for 2-way random
        OPTS.num_ways = 2
        OPTS.replacement_policy = RP.RANDOM
        self.run_all_tests()

        globals.end_opencache()


    def run_all_tests(self):

        sc = setup_sim_cache()

        self.check_true(check_reset(sc))

        self.check_true(check_flush(sc))

        self.check_true(check_hit(sc))

        self.check_true(check_dirty(sc))

        self.check_true(check_read_write(sc))

        if OPTS.replacement_policy == RP.FIFO:
            self.check_true(check_fifo(sc))

        if OPTS.replacement_policy == RP.LRU:
            self.check_true(check_lru(sc))

        if OPTS.replacement_policy == RP.RANDOM:
            self.check_true(check_random(sc))


def setup_sim_cache():
    """ Setup a sim_cache instance. """

    from cache_config import cache_config
    conf = cache_config(OPTS)

    from sim_cache import sim_cache
    sc = sim_cache(cache_config=conf)

    return sc


def reset(sc):
    """ Reset a sim_cache instance. """

    sc.reset()
    sc.reset_dram()


def check_reset(sc):
    """ Check if reset() functions properly. """

    # Write 1 to address 0
    sc.write(0, 1)

    # Reset the cache
    sc.reset()

    # Request to address 0 must be miss
    if sc.find_way(0):
        return False

    # Read unknown data from address 0
    if sc.read(0) is not None:
        return False

    return True


def check_flush(sc):
    """ Check if flush() functions properly. """

    reset(sc)

    # Write 1 to address 0
    sc.write(0, 1)

    # Flush and reset the cache
    sc.flush()
    sc.reset()

    # Read 1 from address 0
    if sc.read(0) != 1:
        return False

    return True


def check_hit(sc):
    """ Check if find_way() functions properly. """

    reset(sc)

    # Address 0 is miss
    if sc.find_way(0):
        return False

    # Read from address 0
    sc.read(0)

    # Address 0 is hit
    if sc.find_way(0) is None:
        return False

    return True


def check_dirty(sc):
    """ Check if is_dirty() functions properly. """

    reset(sc)

    # Read from address 0
    sc.read(0)

    # Address 0 is not dirty
    if sc.is_dirty(0):
        return False

    # Write 1 to address 0
    sc.write(0, 1)

    # Address 0 is dirty
    if not sc.is_dirty(0):
        return False

    return True


def check_read_write(sc):
    """ Check if read() and write() function properly. """

    reset(sc)

    # Read unknown from address 0
    if sc.read(0) is not None:
        return False

    # Write 1 from address 0
    sc.write(0, 1)

    # Read 1 from address 0
    if sc.read(0) != 1:
        return False

    return True


def check_fifo(sc):
    """ Check FIFO replacement of sim_cache. """

    reset(sc)

    # Write 1 to address_0
    address_0 = sc.merge_address(0, 0, 0)
    sc.write(address_0, 1)

    # Write 2 to address_1
    address_1 = sc.merge_address(1, 0, 0)
    sc.write(address_1, 2)

    # Write 3 to address_2
    address_2 = sc.merge_address(2, 0, 0)
    sc.write(address_2, 3)

    # address_0 must be replaced
    if sc.find_way(address_0) is not None:
        return False

    # Read 1 from address_0
    if sc.read(address_0) != 1:
        return False

    # address_1 must be replaced
    if sc.find_way(address_1) is not None:
        return False

    return True


def check_lru(sc):
    """ Check LRU replacement of sim_cache. """

    reset(sc)

    # Write 1 to address_0
    address_0 = sc.merge_address(0, 0, 0)
    sc.write(address_0, 1)

    # Write 2 to address_1
    address_1 = sc.merge_address(1, 0, 0)
    sc.write(address_1, 2)

    sc.read(address_0)

    # Write 3 to address_2
    address_2 = sc.merge_address(2, 0, 0)
    sc.write(address_2, 3)

    # address_1 must be replaced
    if sc.find_way(address_1) is not None:
        return False

    # Read 2 from address_1
    if sc.read(address_1) != 2:
        return False

    # address_0 must be replaced
    if sc.find_way(address_0) is not None:
        return False

    return True


def check_random(sc):
    """ Check random replacement of sim_cache. """

    reset(sc)

    # Write 1 to address_0
    address_0 = sc.merge_address(0, 0, 0)
    sc.write(address_0, 1)

    # Write 2 to address_1
    address_1 = sc.merge_address(1, 0, 0)
    sc.write(address_1, 2)

    # Read hit couple of times
    sc.read(address_1)
    sc.read(address_1)

    # Write 3 to address_2
    address_2 = sc.merge_address(2, 0, 0)
    sc.write(address_2, 3)

    # address_1 must be replaced
    if sc.find_way(address_1) is not None:
        return False

    # Read 2 from address_1
    if sc.read(address_1) != 2:
        return False

    # address_0 must be replaced
    if sc.find_way(address_0) is not None:
        return False

    return True


# Run the test from the terminal
if __name__ == "__main__":
    (OPTS, args) = globals.parse_args()
    del sys.argv[1:]
    header(__file__)
    unittest.main()