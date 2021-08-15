# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from nmigen import Instance
from nmigen import tracer
from cache_signal import CacheSignal


class SramInstance(Instance):
    """
    This class inherits from the Instance class of nMigen library.
    OpenRAM SRAM modules are represented with this class.
    """

    def __init__(self, module_name, row_size, dsgn, m):

        array_name = tracer.get_var_name()
        short_name = array_name.split("_array")[0]

        self.write_csb  = CacheSignal(reset_less=True, reset=1, name=short_name + "_write_csb")
        self.write_addr = CacheSignal(self.set_size, reset_less=True, name=short_name + "_write_addr")
        self.write_din  = CacheSignal(row_size, reset_less=True, name=short_name + "_write_din")
        self.read_csb   = CacheSignal(reset_less=True, name=short_name + "_read_csb")
        self.read_addr  = CacheSignal(self.set_size, reset_less=True, name=short_name + "_read_addr")
        self.read_dout  = CacheSignal(row_size, name=short_name + "_read_dout")

        super().__init__(module_name,
            ("i", "clk0",  dsgn.clk),
            ("i", "csb0",  self.write_csb),
            ("i", "addr0", self.write_addr),
            ("i", "din0",  self.write_din),
            ("i", "clk1",  dsgn.clk),
            ("i", "csb1",  self.read_csb),
            ("i", "addr1", self.read_addr),
            ("o", "dout1", self.read_dout),
        )

        self.m = m

        m.submodules += self


    def input(self):
        """ Return the input signal. """

        return self.write_din


    def output(self):
        """ Return the output signal. """

        return self.read_dout


    def read(self, address):
        """ Send a new read request to SRAM. """

        self.m.d.comb += self.read_csb.eq(0)
        self.m.d.comb += self.read_addr.eq(address)


    def write(self, address, data, way=None):
        """ Send a new write request to SRAM. """

        self.m.d.comb += self.write_csb.eq(0)
        self.m.d.comb += self.write_addr.eq(address)
        # TODO: Use wmask feature of OpenRAM
        self.m.d.comb += self.write_din.eq(self.read_dout)

        if way is None:
            self.m.d.comb += self.write_din.eq(data)
        elif isinstance(way, CacheSignal):
            with self.m.Switch(way):
                for i in range(1 << way.width):
                    with self.m.Case(i):
                        self.m.d.comb += self.write_din.way(i).eq(data)
        else:
            self.m.d.comb += self.write_din.way(way).eq(data)


    def write_bytes(self, wmask, way, offset, data):
        """ Add bytes to write request to SRAM. """

        # Write the word over the write mask
        # NOTE: This switch statement is written manually (not only
        # with word_select) because word_select fails to generate
        # correct case statements if offset calculation is a bit
        # complex.
        for i in range(SramInstance.num_bytes):
            with self.m.If(wmask[i]):
                with self.m.Switch(way):
                    for j in range(SramInstance.num_ways):
                        with self.m.Case(j):
                            with self.m.Switch(offset):
                                for k in range(SramInstance.words_per_line):
                                    with self.m.Case(k):
                                        self.m.d.comb += self.write_din.byte(i, k, j).eq(data.byte(i))