# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from amaranth import Instance
from amaranth import tracer
from cache_signal import cache_signal


class sram_instance:
    """
    This class instantiates Instance class of Amaranth library and holds OpenRAM
    SRAM modules instances.
    """

    def __init__(self, module_name, row_size, num_arrays, c, m):

        # Find the declared name of this instance
        array_name = tracer.get_var_name()
        # Get "{short_name}_array"
        short_name = array_name[:-6]

        self.num_arrays = num_arrays
        real_row_size = row_size // num_arrays

        # Append signals to these lists
        self.write_csb = []
        self.write_addr = []
        self.write_din = []
        self.read_csb = []
        self.read_addr = []
        self.read_dout = []

        for i in range(num_arrays):
            # Write enable
            self.write_csb.append(cache_signal(reset_less=True, reset=1, name="{0}_write_csb{1}".format(short_name, i)))
            # Write address
            self.write_addr.append(cache_signal(self.set_size, reset_less=True, name="{0}_write_addr{1}".format(short_name, i)))
            # Write data
            self.write_din.append(cache_signal(real_row_size, reset_less=True, name="{0}_write_din{1}".format(short_name, i)))
            # Read enable
            self.read_csb.append(cache_signal(reset_less=True, name="{0}_read_csb{1}".format(short_name, i)))
            # Read address
            self.read_addr.append(cache_signal(self.set_size, reset_less=True, name="{0}_read_addr{1}".format(short_name, i)))
            # Read data
            self.read_dout.append(cache_signal(real_row_size, name="{0}_read_dout{1}".format(short_name, i)))

            # Add this instance to the design module
            m.submodules += Instance(module_name,
                ("i", "clk0", c.clk),
                ("i", "csb0", self.write_csb[i]),
                ("i", "addr0", self.write_addr[i]),
                ("i", "din0", self.write_din[i]),
                ("i", "clk1", c.clk),
                ("i", "csb1", self.read_csb[i]),
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


    def write_local(self, address, data, way, is_reset=False):
        """ Send a new write request to SRAM. """

        if self.num_arrays > 1:
            idx = way
        else:
            idx = 0

        # TODO: Use wmask feature of OpenRAM
        self.m.d.comb += self.write_csb[idx].eq(0)
        self.m.d.comb += self.write_addr[idx].eq(address)
        self.m.d.comb += self.write_din[idx].eq(self.read_dout[idx])
        if self.num_arrays > 1 or is_reset:
            self.m.d.comb += self.write_din[idx].eq(data)
        else:
            self.m.d.comb += self.write_din[0].way(way).eq(data)


    def write(self, address, data, way=None):
        """ Send a new write request to SRAM. """

        # If no way is given, set all input data
        if way is None:
            for i in range(self.num_arrays):
                self.write_local(address, data, i, True)
        # If way is a signal, wrap it with case statements
        elif isinstance(way, cache_signal):
            with self.m.Switch(way):
                for i in range(2 ** way.width):
                    with self.m.Case(i):
                        self.write_local(address, data, i)
        # If way is a constant, calculate the way part of the signal
        else:
            self.write_local(address, data, way)


    def write_input_local(self, way, word, data, wmask):
        """ Add input data to write request to SRAM. """

        # Write the word over the write mask
        for mask_idx in range(sram_instance.num_masks):
            with self.m.If(wmask[mask_idx]):
                if word is None:
                    self.m.d.comb += self.write_din[way].mask(mask_idx).eq(data.mask(mask_idx))
                else:
                    self.m.d.comb += self.write_din[way].mask(mask_idx, word).eq(data.mask(mask_idx))

        # Write the whole word if write mask is not used
        if not sram_instance.num_masks:
            if word is None:
                self.m.d.comb += self.write_din[way].eq(data)
            else:
                self.m.d.comb += self.write_din[way].word(word).eq(data)


    def find_way(self, way):
        """ Return all way indices corresponding to the given way value. """

        if not isinstance(way, cache_signal):
            yield way
        else:
            with self.m.Switch(way):
                for way_idx in range(sram_instance.num_ways):
                    with self.m.Case(way_idx):
                        yield way_idx


    def find_word(self, offset):
        """ Return all word indices corresponding to the given offset value. """

        if offset is None:
            yield None
        else:
            with self.m.Switch(offset):
                for word_idx in range(sram_instance.words_per_line):
                    with self.m.Case(word_idx):
                        yield word_idx


    def write_input(self, way, offset, data, wmask=None):
        """ Add input data to write request to SRAM. """

        # NOTE: These switch statements are written manually (not only with
        # word_select) because word_select fails to generate correct case
        # statements if offset calculation is a bit complex.

        for way_idx in self.find_way(way):
            for word_idx in self.find_word(offset):
                self.write_input_local(way_idx, word_idx, data, wmask)