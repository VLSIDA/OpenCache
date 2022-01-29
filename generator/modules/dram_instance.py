# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from cache_signal import cache_signal


class dram_instance:
    """
    This class represents DRAM which OpenCache modules connect to.
    """

    def __init__(self, m, address_size, row_size, read_only=False):

        self.read_only = read_only

        # Chip select
        self.main_csb = cache_signal(reset_less=True, reset=1)
        # Write enable
        if not read_only:
            self.main_web = cache_signal(reset_less=True, reset=1)
        # Address
        self.main_addr = cache_signal(address_size, reset_less=True)
        # Data input
        if not read_only:
            self.main_din = cache_signal(row_size, reset_less=True)
        # Data output
        self.main_dout = cache_signal(row_size)
        # Stall
        self.main_stall = cache_signal()

        # Keep the design module for later use
        self.m = m


    def get_signals(self):
        """ Return a list of all IO signals. """

        ports = []
        for _, v in self.__dict__.items():
            if isinstance(v, cache_signal):
                ports.append(v)
        return ports


    def output(self):
        """ Return the output signal. """

        return self.main_dout


    def stall(self):
        """ Return the stall signal. """

        return self.main_stall


    def disable(self):
        """ Don't send a new request to DRAM. """

        self.m.d.comb += self.main_csb.eq(1)


    def read(self, address):
        """ Send a new read request to DRAM. """

        self.m.d.comb += self.main_csb.eq(0)
        if not self.read_only:
            self.m.d.comb += self.main_web.eq(1)
        self.m.d.comb += self.main_addr.eq(address)


    def write(self, address, data):
        """ Send a new write request to DRAM. """

        if not self.read_only:
            self.m.d.comb += self.main_csb.eq(0)
            self.m.d.comb += self.main_web.eq(0)
            self.m.d.comb += self.main_addr.eq(address)
            self.m.d.comb += self.main_din.eq(data)