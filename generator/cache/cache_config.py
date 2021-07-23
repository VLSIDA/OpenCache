# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import debug
from math import log2, ceil
from policy import Associativity as AS, ReplacementPolicy as RP


class cache_config:
    """ This is a structure that is used to hold the cache configuration options. """

    def __init__(self, OPTS):

        self.total_size         = OPTS.total_size
        self.word_size          = OPTS.word_size
        self.words_per_line     = OPTS.words_per_line
        self.address_size       = OPTS.address_size
        self.num_ways           = OPTS.num_ways
        self.replacement_policy = OPTS.replacement_policy
        self.write_policy       = OPTS.write_policy
        self.is_data_cache      = OPTS.is_data_cache
        self.return_type        = OPTS.return_type
        self.data_hazard        = OPTS.data_hazard

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

        self.num_rows = int(self.total_size / self.row_size)

        self.offset_size = ceil(log2(self.words_per_line))
        self.set_size = ceil(log2(self.num_rows))
        self.tag_size = self.address_size - self.set_size - self.offset_size

        if self.tag_size + self.set_size + self.offset_size != self.address_size:
            debug.error("Calculated address size does not match the given address size.", -1)

        # Way size is used in replacement policy
        self.way_size = ceil(log2(self.num_ways))

        # Number of bytes in a word
        self.num_bytes = ceil(self.word_size / 8)

        # Set the associativity of the cache
        if self.num_ways == 1:
            self.associativity = AS.DIRECT
        elif self.set_size > 0:
            self.associativity = AS.N_WAY
        else:
            self.associativity = AS.FULLY

        # Direct-mapped cache doesn't have a replacement policy
        if self.associativity == AS.DIRECT:
            self.replacement_policy = RP.NONE