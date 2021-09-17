# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from policy import ReplacementPolicy as RP
from globals import OPTS


class sim_sram:
    """
    This is a simulation module for SRAMs.
    It is used in sim_cache to read and write data.
    """

    def __init__(self, num_words, num_ways, num_rows):

        self.num_words = num_words
        self.num_ways = num_ways
        self.num_rows = num_rows


    def reset(self):
        """ Reset all arrays of the SRAM. """

        self.valid_array = [[0] * self.num_ways for _ in range(self.num_rows)]
        self.dirty_array = [[0] * self.num_ways for _ in range(self.num_rows)]
        self.tag_array = [[0] * self.num_ways for _ in range(self.num_rows)]
        self.data_array = [[[0] * self.num_words for _ in range(self.num_ways)] for _ in range(self.num_rows)]
        if OPTS.replacement_policy == RP.FIFO:
            self.fifo_array = [0] * self.num_rows
        if OPTS.replacement_policy == RP.LRU:
            self.lru_array = [[0] * self.num_ways for _ in range(self.num_rows)]


    def read_valid(self, set, way):
        """ Return the valid bit of given set and way. """

        return self.valid_array[set][way]


    def read_dirty(self, set, way):
        """ Return the dirty bit of given set and way. """

        return self.dirty_array[set][way]


    def read_tag(self, set, way):
        """ Return the tag of given set and way. """

        return self.tag_array[set][way]


    def read_fifo(self, set):
        """ Return the FIFO bits of given set and way. """

        return self.fifo_array[set]


    def read_lru(self, set, way):
        """ Return the LRU bits of given set and way. """

        return self.lru_array[set][way]


    def read_word(self, set, way, offset):
        """ Return the data word of given set, way, and offset. """

        return self.data_array[set][way][offset]


    def read_line(self, set, way):
        """ Return the data line of given set and way. """

        return self.data_array[set][way].copy()


    def write_valid(self, set, way, data):
        """ Write the valid bit of given set and way. """

        self.valid_array[set][way] = data


    def write_dirty(self, set, way, data):
        """ Write the dirty bit of given set and way. """

        self.dirty_array[set][way] = data


    def write_tag(self, set, way, data):
        """ Write the tag of given set and way. """

        self.tag_array[set][way] = data


    def write_fifo(self, set, data):
        """ Write the FIFO bits of given set and way. """

        self.fifo_array[set] = data % self.num_ways


    def write_lru(self, set, way, data):
        """ Write the LRU bits of given set and way. """

        self.lru_array[set][way] = data


    def write_word(self, set, way, offset, data):
        """ Write the data word of given set, way, and offset. """

        self.data_array[set][way][offset] = data


    def write_line(self, set, way, data):
        """ Write the data line of given set and way. """

        self.data_array[set][way] = data