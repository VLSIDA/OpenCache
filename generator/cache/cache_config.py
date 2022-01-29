# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from math import log2, ceil
import debug
from policy import associativity as asc
from globals import OPTS


class cache_config:
    """ This is a structure that is used to hold the cache configuration options. """

    def __init__(self, total_size, word_size, words_per_line, address_size, write_size, num_ways):

        self.total_size = total_size
        self.word_size = word_size
        self.words_per_line = words_per_line
        self.address_size = address_size
        self.write_size = write_size
        self.num_ways = num_ways

        self.compute_configs()


    def set_local_config(self, module):
        """ Copy all of the member variables to the given module for convenience. """

        members = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]

        # Copy all the variables to the local module
        for member in members:
            setattr(module, member, getattr(self, member))


    def compute_configs(self):
        """ Compute some of the configuration variables. """

        # A data line consists of multiple words
        self.line_size = self.word_size * self.words_per_line

        # A row may consist of multiple lines
        self.row_size = self.line_size * self.num_ways

        # Total size must match row size
        if self.total_size % self.row_size:
            debug.error("Row size overflows the size of the cache.", -1)

        self.num_rows = self.total_size // self.row_size

        # If cache returns line, we shouldn't use offset
        if OPTS.return_type == "word":
            self.offset_size = ceil(log2(self.words_per_line))
        else:
            self.offset_size = 0
        self.set_size = ceil(log2(self.num_rows))
        self.tag_size = self.address_size - self.set_size - self.offset_size

        debug.info(1, "Address tag size: {}".format(self.tag_size)
                   + " Address set size: {}".format(self.set_size)
                   + " Address offset size: {}".format(self.offset_size))

        if self.tag_size + self.set_size + self.offset_size != self.address_size:
            debug.error("Calculated address size does not match the given address size.", -1)

        # Address port size of DRAM
        self.dram_address_size = self.address_size - self.offset_size
        # Number of rows in DRAM
        self.dram_num_rows = 2 ** self.dram_address_size

        # Tag word bit-width of a way
        self.tag_word_size = self.tag_size + (2 if OPTS.is_data_cache else 1)

        # Way size is used in replacement policy
        self.way_size = ceil(log2(self.num_ways))

        # Don't add a write mask if it is the same size as data word or instruction cache
        if (OPTS.return_type == "word" and self.write_size == self.word_size) or self.write_size == self.line_size or not OPTS.is_data_cache:
            self.write_size = None
        # Number of write masks
        if self.write_size:
            # Write mask should be applied to input/output port size
            if OPTS.return_type == "word":
                self.num_masks = self.word_size // self.write_size
            else:
                self.num_masks = self.line_size // self.write_size
        else:
            self.num_masks = 0

        # Set the associativity of the cache
        if self.num_ways == 1:
            self.associativity = asc.DIRECT
        elif self.set_size > 0:
            self.associativity = asc.N_WAY
        else:
            self.associativity = asc.FULLY
        # Add associativity to OPTS
        OPTS.associativity = self.associativity

        debug.info(1, "Associativity: {}".format(self.associativity))