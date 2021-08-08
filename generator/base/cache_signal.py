# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from nmigen import Signal
from nmigen import tracer


class CacheSignal(Signal):
    """
    This class inherits from the Signal class of nMigen library.
    Common bit calculations are implemented here.
    """

    def __init__(self, shape=None, name=None, reset=0, reset_less=False, is_flop=False):

        super().__init__(shape=shape, name=name, reset=reset, reset_less=is_flop or reset_less)

        # Find the declared name of this instance
        self.name = tracer.get_var_name()

        self.is_flop = is_flop

        # If the signal is a flop, add a "_next" signal to deal
        # with flop operations internally
        if is_flop:
            self.next = CacheSignal(shape=shape, reset_less=True)
            # Update the name of "_next" signal
            self.next.name = self.name + "_next"


    def eq(self, value, sync=False):
        """ Assign a value to the signal. Deals with flops internally. """

        # If the domain is combinatorial, assign the value to left-hand side
        # signal of the flip-flop
        if not sync and self.is_flop:
            return self.next.eq(value)

        return super().eq(value)


    def parse_tag(self):
        """ Return tag bits of an address signal. """

        return self[-CacheSignal.tag_size:]


    def parse_set(self):
        """ Return set bits of an address signal. """

        return self.bit_select(self.offset_size, self.set_size)


    def parse_offset(self):
        """ Return offset bits of an address signal. """

        return self[:CacheSignal.offset_size]


    def valid(self, way=0):
        """ Return valid bit of a tag signal. """

        return self.bit_select(way * (CacheSignal.tag_word_size) + (CacheSignal.tag_word_size - 1), 1)


    def dirty(self, way=0):
        """ Return dirty bit of a tag signal. """

        return self.bit_select(way * (CacheSignal.tag_word_size) + (CacheSignal.tag_word_size - 2), 1)


    def tag(self, way=0):
        """ Return tag bits of a tag signal. """

        return self.bit_select(way * (CacheSignal.tag_word_size), CacheSignal.tag_size)


    def tag_word(self, way=0):
        """ Return whole tag word of a tag signal. """

        return self.word_select(way, CacheSignal.tag_word_size)


    def byte(self, byte_offset, word_offset=0, way=0):
        """ Return a data byte of a data signal. """

        return self.word_select((way * CacheSignal.words_per_line + word_offset) * CacheSignal.num_bytes + byte_offset, 8)


    def word(self, offset, way=0):
        """ Return a data word of a data signal. """

        return self.word_select(way * CacheSignal.words_per_line + offset, CacheSignal.word_size)


    def line(self, way):
        """ Return a data line of a data signal. """

        return self.word_select(way, CacheSignal.line_size)


    def use(self, way=0):
        """ Return use bits of a use signal. """

        return self.word_select(way, CacheSignal.way_size)