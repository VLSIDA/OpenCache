# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from cache_base import cache_base
from cache_signal import CacheSignal


class n_way_random_cache(cache_base):
    """
    This is the design module of N-way set associative cache with random
    replacement policy.
    """

    def __init__(self, cache_config, name):

        super().__init__(cache_config, name)


    def add_internal_signals(self):
        """ Add internal registers and wires to cache design. """

        super().add_internal_signals()

        # Keep way chosen to be evicted in a flop
        self.way = CacheSignal(self.way_size, is_flop=True)

        # Random counter flop for replacement
        self.random = CacheSignal(self.way_size, is_flop=True)