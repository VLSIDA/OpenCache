# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from random import randrange
from globals import OPTS


class sim_cache:
    """
    This is a high level cache design used for simulation.
    """

    def __init__(self, cache_config):

        cache_config.set_local_config(self)

        self.reset()
        self.reset_dram()


    def reset(self):
        """ Reset the cache. """

        # These arrays are multi-dimensional.
        # First dimension is for sets.
        # Second dimension is for ways.
        # Third dimension is for words (for data array).
        self.valid_array = [[0] * self.num_ways for _ in range(self.num_rows)]
        self.dirty_array = [[0] * self.num_ways for _ in range(self.num_rows)]
        self.tag_array   = [[0] * self.num_ways for _ in range(self.num_rows)]
        self.data_array  = [[[None] * self.words_per_line for _ in range(self.num_ways)] for _ in range(self.num_rows)]

        if self.replacement_policy == "fifo":
            self.fifo_array = [0] * self.num_rows

        if self.replacement_policy == "lru":
            self.lru_array = [[0] * self.num_ways for _ in range(self.num_rows)]

        if self.replacement_policy == "random":
            self.random = 0


    def reset_dram(self):
        """ Reset the DRAM. """

        # DRAM list has a line in each row.
        self.dram = [[None] * self.words_per_line for _ in range((2 ** (self.tag_size + self.set_size)))]


    def flush(self):
        """ Write dirty data lines back to DRAM. """

        for row_i in range(self.num_rows):
            for way_i in range(self.num_ways):
                if self.valid_array[row_i][way_i] and self.dirty_array[row_i][way_i]:
                    old_tag  = self.tag_array[row_i][way_i]
                    old_data = self.data_array[row_i][way_i].copy()
                    self.dram[(old_tag << self.set_size) + row_i] = old_data


    def merge_address(self, tag_decimal, set_decimal, offset_decimal):
        """
        Create the address consists of given
        tag, set, and offset values.
        """

        tag_binary    = "{0:0{1}b}".format(tag_decimal, self.tag_size)
        set_binary    = "{0:0{1}b}".format(set_decimal, self.set_size)
        offset_binary = "{0:0{1}b}".format(offset_decimal, self.offset_size)

        address_binary  = tag_binary + set_binary + offset_binary
        address_decimal = int(address_binary, 2)

        return address_decimal


    def parse_address(self, address):
        """ Parse the given address into tag, set, and offset. """

        address_binary = "{0:0{1}b}".format(address, self.address_size)
        tag_binary     = address_binary[:self.tag_size]
        set_binary     = address_binary[self.tag_size:self.tag_size + self.set_size]
        offset_binary  = address_binary[-self.offset_size:]

        tag_decimal    = int(tag_binary, 2)
        set_decimal    = int(set_binary, 2)
        offset_decimal = int(offset_binary, 2)

        return (tag_decimal, set_decimal, offset_decimal)


    def find_way(self, address):
        """ Find the way which has the given address' data. """

        tag_decimal, set_decimal, _ = self.parse_address(address)

        for way in range(self.num_ways):
            if self.valid_array[set_decimal][way] and self.tag_array[set_decimal][way] == tag_decimal:
                return way

        # Return None if not found
        return None


    def is_dirty(self, address):
        """ Return the dirty bit of the given address. """

        _, set_decimal, _ = self.parse_address(address)
        way = self.find_way(address)

        if way is not None:
            return self.dirty_array[set_decimal][way]

        # Return None if not found
        return None


    def way_to_evict(self, set_decimal):
        """ Return the way to evict. """

        if self.replacement_policy is None:
            return 0

        if self.replacement_policy == "fifo":
            return self.fifo_array[set_decimal]

        if self.replacement_policy == "lru":
            way = None
            for i in range(self.num_ways):
                if not self.lru_array[set_decimal][i]:
                    way = i
            return way

        # TODO: Random way should be the same as the hardware design.
        # In the hardware design, there is a counter serving as the
        # "random way selector". Therefore, this function must do
        # the same.
        if self.replacement_policy == "random":
            return randrange(2)


    def read(self, address):
        """ Read the data of an address. """

        tag_decimal, set_decimal, offset_decimal = self.parse_address(address)
        way = self.find_way(address)

        if way is not None: # Hit
            self.update_lru(set_decimal, way)

            return self.data_array[set_decimal][way][offset_decimal]
        else: # Miss
            evict_way = self.way_to_evict(set_decimal)

            # Write-back
            if self.is_dirty(address):
                self.update_fifo(set_decimal)

                old_tag  = self.tag_array[set_decimal][evict_way]
                old_data = self.data_array[set_decimal][evict_way].copy()
                self.dram[(old_tag << self.set_size) + set_decimal] = old_data

            self.valid_array[set_decimal][evict_way] = 1
            self.dirty_array[set_decimal][evict_way] = 0
            self.tag_array[set_decimal][evict_way]   = tag_decimal
            self.data_array[set_decimal][evict_way]  = self.dram[(tag_decimal << self.set_size) + set_decimal].copy()

            self.update_lru(set_decimal, evict_way)

            return self.data_array[set_decimal][evict_way][offset_decimal]


    def write(self, address, data_input):
        """ Write the data to an address. """

        tag_decimal, set_decimal, offset_decimal = self.parse_address(address)
        way = self.find_way(address)

        if way is not None: # Hit
            self.update_lru(set_decimal, way)

            self.dirty_array[set_decimal][way] = 1
            self.data_array[set_decimal][way][offset_decimal] = data_input
        else: # Miss
            evict_way = self.way_to_evict(set_decimal)

            # Write-back
            if self.dirty_array[set_decimal][evict_way]:
                self.update_fifo(set_decimal)

                old_tag  = self.tag_array[set_decimal][evict_way]
                old_data = self.data_array[set_decimal][evict_way].copy()
                self.dram[(old_tag << self.set_size) + set_decimal] = old_data

            self.valid_array[set_decimal][evict_way] = 1
            self.dirty_array[set_decimal][evict_way] = 1
            self.tag_array[set_decimal][evict_way]   = tag_decimal
            self.data_array[set_decimal][evict_way][offset_decimal] = data_input

            self.update_lru(set_decimal, evict_way)


    def update_fifo(self, set_decimal):
        """ Update the FIFO number of the latest replaced set. """

        # Check if replacement policy matches
        if self.replacement_policy == "fifo":
            # Starting from 0, increase the FIFO number every time a
            # new data is brought from DRAM.
            #
            # When it reaches the max value, go back to 0 and proceed.
            self.fifo_array[set_decimal] += 1
            self.fifo_array[set_decimal] %= self.num_ways


    def update_lru(self, set_decimal, way):
        """ Update the LRU numbers of the latest used way. """

        # Check if replacement policy matches
        if self.replacement_policy == "lru":
            # There is a number for each way in a set. They are ordered
            # by their access time relative to each other.
            #
            # When a way is accessed (read or write), it is brought to
            # the top of the order (highest possible number) and numbers
            # which are more than its previous value are decreased by one.
            for i in range(self.num_ways):
                if self.lru_array[set_decimal][i] > self.lru_array[set_decimal][way]:
                    self.lru_array[set_decimal][i] -= 1
            self.lru_array[set_decimal][way] = self.num_ways - 1


    def update_random(self, cycles):
        """ Update the random counter for a number of cycles. """

        # Check if replacement policy matches
        if self.replacement_policy == "random":
            # In the real hardware, random caches have a register acting 
            # like a counter. This register is incremented at every posedge
            # of the clock.
            # Since we cannot guarantee how many cycles a miss will take,
            # this register essentially has random values.
            self.random += cycles
            self.random %= self.num_ways