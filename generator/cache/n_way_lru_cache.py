# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from cache_base import cache_base
from cache_signal import CacheSignal
from sram_instance import SramInstance
from globals import OPTS


class n_way_lru_cache(cache_base):
    """
    This is the design module of N-way set associative cache with LRU
    replacement policy.
    """

    def __init__(self, cache_config, name):

        super().__init__(cache_config, name)


    def calculate_configs(self, paths):
        """ Calculate config options for internal SRAM arrays of the cache. """

        # Store config file options in a list
        config_opts = super().calculate_configs(paths)

        # Use array of the cache
        use_opts = {}
        use_opts["path"] = paths["use"]
        use_opts["opts"] = {}
        use_opts["opts"]["word_size"]    = self.way_size * self.num_ways
        use_opts["opts"]["num_words"]    = self.num_rows
        use_opts["opts"]["num_rw_ports"] = 0
        use_opts["opts"]["num_r_ports"]  = 1
        use_opts["opts"]["num_w_ports"]  = 1
        use_opts["opts"]["output_path"]  = "{}lru_array".format(OPTS.output_path)
        use_opts["opts"]["output_name"]  = "{}".format(OPTS.use_array_name)
        config_opts.append(use_opts)

        return config_opts


    def add_internal_signals(self):
        """ Add internal registers and wires to cache design. """

        super().add_internal_signals()

        # Keep way chosen to be evicted in a flop
        self.way = CacheSignal(self.way_size, is_flop=True)


    def add_srams(self, m):
        """ Add internal SRAM array instances to cache design. """

        super().add_srams(m)

        # Use array
        word_size = self.way_size * self.num_ways
        self.use_array = SramInstance(OPTS.use_array_name, word_size, 1, self, m)