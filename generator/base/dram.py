# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from cache_signal import CacheSignal


class Dram:
    """
    This class represents DRAM which OpenCache modules connect to.
    """

    def __init__(self, m, address_size, row_size):

        self.main_csb   = CacheSignal(reset_less=True, reset=1)
        self.main_web   = CacheSignal(reset_less=True, reset=1)
        self.main_addr  = CacheSignal(address_size, reset_less=True)
        self.main_din   = CacheSignal(row_size, reset_less=True)
        self.main_dout  = CacheSignal(row_size)
        self.main_stall = CacheSignal()

        self.m = m


    def get_pins(self):
        """ Return a list of all IO signals. """

        ports = []
        for _, v in self.__dict__.items():
            if isinstance(v, CacheSignal):
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
        self.m.d.comb += self.main_web.eq(1)
        self.m.d.comb += self.main_addr.eq(address)


    def write(self, address, data):
        """ Send a new write request to DRAM. """

        self.m.d.comb += self.main_csb.eq(0)
        self.m.d.comb += self.main_web.eq(0)
        self.m.d.comb += self.main_addr.eq(address)
        self.m.d.comb += self.main_din.eq(data)