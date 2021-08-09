# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from cache_base import cache_base
from nmigen import Instance
from cache_signal import CacheSignal
from globals import OPTS


class n_way_fifo_cache(cache_base):
    """
    This is the design module of N-way set associative cache
    with FIFO replacement policy.
    """

    def __init__(self, cache_config, name):

        super().__init__(cache_config, name)


    def add_internal_signals(self):
        """ Add internal registers and wires to cache design. """

        super().add_internal_signals()

        # Keep way chosen to be evicted in a flop
        self.way = CacheSignal(self.way_size, is_flop=True)


    def add_srams(self, m):
        """ Add internal SRAM array instances to cache design. """

        super().add_srams(m)

        # Use array
        word_size = self.way_size
        self.use_write_csb  = CacheSignal(reset_less=True, reset=1)
        self.use_write_addr = CacheSignal(self.set_size, reset_less=True)
        self.use_write_din  = CacheSignal(word_size, reset_less=True)
        self.use_read_csb   = CacheSignal(reset_less=True)
        self.use_read_addr  = CacheSignal(self.set_size, reset_less=True)
        self.use_read_dout  = CacheSignal(word_size)
        m.submodules += Instance(OPTS.use_array_name,
            ("i", "clk0",  self.clk),
            ("i", "csb0",  self.use_write_csb),
            ("i", "addr0", self.use_write_addr),
            ("i", "din0",  self.use_write_din),
            ("i", "clk1",  self.clk),
            ("i", "csb1",  self.use_read_csb),
            ("i", "addr1", self.use_read_addr),
            ("o", "dout1", self.use_read_dout),
        )