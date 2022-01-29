# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from logic_base import logic_base
from state import state
from globals import OPTS


class input_interface(logic_base):
    """
    This is the class of request decoder always block modules.

    In this block, CPU's request is decoded. Address is parsed into tag, set
    and offset values, and write enable, write mask and data input are saved in
    flip-flops.
    """

    def __init__(self):

        super().__init__()


    def add_reset(self, c, m):
        """ Add statements for the RESET state. """

        # In the RESET state, set register is used to reset all lines in
        # the tag array.
        with m.Case(state.RESET):
            m.d.comb += c.set.eq(c.set + 1)


    def add_flush(self, c, m):
        """ Add statements for the FLUSH state. """

        # In the FLUSH state, set register is used to write all dirty lines
        # back to DRAM.
        with m.Case(state.FLUSH):
            # If current set is clean or DRAM is available, increment the set
            # register when all ways in the set are checked
            with m.If((~c.tag_array.output().dirty(c.way) | ~c.dram.stall()) & (c.way == c.num_ways - 1)):
                m.d.comb += c.set.eq(c.set + 1)


    def add_idle(self, c, m):
        """ Add statements for the IDLE state. """

        # In the IDLE state, the request is decoded.
        with m.Case(state.IDLE):
            self.store_request(c, m)


    def add_compare(self, c, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, the request is decoded if current request is hit.
        with m.Case(state.COMPARE):
            for _ in c.hit_detector.find_hit():
                self.store_request(c, m)


    def add_wait_read(self, c, m):
        """ Add statements for the WAIT_READ state. """

        # In the COMPARE state, the request is decoded if DRAM completed read request
        with m.Case(state.WAIT_READ):
            with m.If(~c.dram.stall()):
                self.store_request(c, m)


    def add_flush_sig(self, c, m):
        """ Add flush signal control. """

        # If flush is high, input registers are not reset.
        # However, way and set registers becomes 0 since it is going to be used
        # to write dirty lines back to DRAM.
        with m.If(c.flush):
            m.d.comb += c.set.eq(0)


    def add_reset_sig(self, c, m):
        """ Add reset signal control. """

        # If rst is high, input registers are reset.
        # set register becomes 1 since it is going to be used to reset all lines
        # in the tag array.
        # way register becomes 0 since it is going to be used to reset all ways
        # in a tag line.
        with m.If(c.rst):
            m.d.comb += c.tag.eq(0)
            m.d.comb += c.set.eq(0)
            if c.offset_size:
                m.d.comb += c.offset.eq(0)
            if OPTS.is_data_cache:
                m.d.comb += c.web_reg.eq(1)
            if c.num_masks:
                m.d.comb += c.wmask_reg.eq(0)
            if OPTS.is_data_cache:
                m.d.comb += c.din_reg.eq(0)


    def store_request(self, c, m):
        """ Decode and store the request signals in flip-flops. """

        m.d.comb += c.tag.eq(c.addr.parse_tag())
        m.d.comb += c.set.eq(c.addr.parse_set())
        if c.offset_size:
            m.d.comb += c.offset.eq(c.addr.parse_offset())
        if OPTS.is_data_cache:
            m.d.comb += c.web_reg.eq(c.web)
        if c.num_masks:
            m.d.comb += c.wmask_reg.eq(c.wmask)
        if OPTS.is_data_cache:
            m.d.comb += c.din_reg.eq(c.din)