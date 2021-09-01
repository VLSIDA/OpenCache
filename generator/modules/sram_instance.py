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


class SramInstance:
    """
    This class instantiates Instance class of nMigen library and holds OpenRAM
    SRAM modules instances.
    """

    def __init__(self, module_name, row_size, num_arrays, dsgn, m):

        # Find the declared name of this instance
        array_name = tracer.get_var_name()
        short_name = array_name.split("_array")[0]

        self.num_arrays = num_arrays
        real_row_size = row_size // num_arrays

        # Append signals to these lists
        self.write_csb  = []
        self.write_addr = []
        self.write_din  = []
        self.read_csb   = []
        self.read_addr  = []
        self.read_dout  = []

        for i in range(num_arrays):
            # Write enable
            self.write_csb.append(CacheSignal(reset_less=True, reset=1, name="{0}_write_csb{1}".format(short_name, i)))
            # Write address
            self.write_addr.append(CacheSignal(self.set_size, reset_less=True, name="{0}_write_addr{1}".format(short_name, i)))
            # Write data
            self.write_din.append(CacheSignal(real_row_size, reset_less=True, name="{0}_write_din{1}".format(short_name, i)))
            # Read enable
            self.read_csb.append(CacheSignal(reset_less=True, name="{0}_read_csb{1}".format(short_name, i)))
            # Read address
            self.read_addr.append(CacheSignal(self.set_size, reset_less=True, name="{0}_read_addr{1}".format(short_name, i)))
            # Read data
            self.read_dout.append(CacheSignal(real_row_size, name="{0}_read_dout{1}".format(short_name, i)))

            # Add this instance to the design module
            m.submodules += Instance(module_name,
                ("i", "clk0",  dsgn.clk),
                ("i", "csb0",  self.write_csb[i]),
                ("i", "addr0", self.write_addr[i]),
                ("i", "din0",  self.write_din[i]),
                ("i", "clk1",  dsgn.clk),
                ("i", "csb1",  self.read_csb[i]),
                ("i", "addr1", self.read_addr[i]),
                ("o", "dout1", self.read_dout[i]),
            )

        # Keep the design module for later use
        self.m = m


    def input(self, way=0):
        """ Return the input signal. """

        return self.write_din[way]


    def output(self, way=0):
        """ Return the output signal. """

        return self.read_dout[way]


    def read(self, address):
        """ Send a new read request to SRAM. """

        # Read the same address from all arrays
        for i in range(self.num_arrays):
            self.m.d.comb += self.read_csb[i].eq(0)
            self.m.d.comb += self.read_addr[i].eq(address)


    def write(self, address, data, way=None):
        """ Send a new write request to SRAM. """

        # TODO: Use wmask feature of OpenRAM

        # If no way is given, set all input data
        if way is None:
            for i in range(self.num_arrays):
                self.m.d.comb += self.write_csb[i].eq(0)
                self.m.d.comb += self.write_addr[i].eq(address)
                self.m.d.comb += self.write_din[i].eq(self.read_dout[i])
                self.m.d.comb += self.write_din[i].eq(data)
        # If way is a signal, wrap it with case statements
        elif isinstance(way, CacheSignal):
            with self.m.Switch(way):
                for i in range(1 << way.width):
                    with self.m.Case(i):
                        if self.num_arrays > 1:
                            self.m.d.comb += self.write_csb[i].eq(0)
                            self.m.d.comb += self.write_addr[i].eq(address)
                            self.m.d.comb += self.write_din[i].eq(self.read_dout[i])
                            self.m.d.comb += self.write_din[i].eq(data)
                        else:
                            self.m.d.comb += self.write_csb[0].eq(0)
                            self.m.d.comb += self.write_addr[0].eq(address)
                            self.m.d.comb += self.write_din[0].eq(self.read_dout[0])
                            self.m.d.comb += self.write_din[0].way(i).eq(data)
        # If way is a constant, calculate the way part of the signal
        else:
            if self.num_arrays > 1:
                self.m.d.comb += self.write_csb[way].eq(0)
                self.m.d.comb += self.write_addr[way].eq(address)
                self.m.d.comb += self.write_din[way].eq(self.read_dout[way])
                self.m.d.comb += self.write_din[way].eq(data)
            else:
                self.m.d.comb += self.write_csb[0].eq(0)
                self.m.d.comb += self.write_addr[0].eq(address)
                self.m.d.comb += self.write_din[0].eq(self.read_dout[0])
                self.m.d.comb += self.write_din[0].way(way).eq(data)


    def write_input(self, way, offset, data, wmask=None):
        """ Add input data to write request to SRAM. """

        # NOTE: These switch statements are written manually (not only with
        # word_select) because word_select fails to generate correct case
        # statements if offset calculation is a bit complex.

        # If way is a signal, use case statements
        if isinstance(way, CacheSignal):
            with self.m.Switch(way):
                for way_idx in range(SramInstance.num_ways):
                    with self.m.Case(way_idx):
                        # Offset is used to find the word
                        with self.m.Switch(offset):
                            for word_idx in range(SramInstance.words_per_line):
                                with self.m.Case(word_idx):
                                    # Write the word over the write mask
                                    for mask_idx in range(SramInstance.num_masks):
                                        with self.m.If(wmask[mask_idx]):
                                            self.m.d.comb += self.write_din[way_idx].mask(mask_idx, word_idx).eq(data.mask(mask_idx))
                                    if not SramInstance.num_masks:
                                        self.m.d.comb += self.write_din[way_idx].word(word_idx).eq(data)
        # If way is a constant, use it directly
        else:
            # Offset is used to find the word
            with self.m.Switch(offset):
                for word_idx in range(SramInstance.words_per_line):
                    with self.m.Case(word_idx):
                        # Write the word over the write mask
                        for mask_idx in range(SramInstance.num_masks):
                            with self.m.If(wmask[mask_idx]):
                                self.m.d.comb += self.write_din[way].mask(mask_idx, word_idx).eq(data.mask(mask_idx))
                        if not SramInstance.num_masks:
                            self.m.d.comb += self.write_din[way].word(word_idx).eq(data)