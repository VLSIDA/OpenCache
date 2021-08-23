# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from block_base import block_base
from state import State


class request_block_base(block_base):
    """
    This is the base class of request decoder always block modules.
    Methods of this class can be overridden for specific implementation of
    different cache designs.

    In this block, CPU's request is decoded. Address is parsed into tag, set
    and offset values, and write enable, write mask and data input are saved in
    flip-flops.
    """

    def __init__(self):

        super().__init__()


    def add_reset_sig(self, dsgn, m):
        """ Add reset signal control. """

        # If rst is high, input registers are reset.
        # set register becomes 1 since it is going to be used to reset all lines
        # in the tag array.
        # way register becomes 0 since it is going to be used to reset all ways
        # in a tag line.
        with m.If(dsgn.rst):
            m.d.comb += dsgn.tag.eq(0)
            m.d.comb += dsgn.set.eq(1)
            m.d.comb += dsgn.offset.eq(0)
            m.d.comb += dsgn.web_reg.eq(1)
            if dsgn.num_masks:
                m.d.comb += dsgn.wmask_reg.eq(0)
            m.d.comb += dsgn.din_reg.eq(0)


    def add_flush_sig(self, dsgn, m):
        """ Add flush signal control. """

        # If flush is high, input registers are not reset.
        # However, way and set registers becomes 0 since it is going to be used
        # to write dirty lines back to DRAM.
        with m.Elif(dsgn.flush):
            m.d.comb += dsgn.set.eq(0)


    def add_states(self, dsgn, m):
        """ Add statements for each cache state. """

        with m.Else():
            super().add_states(dsgn, m)


    def add_reset(self, dsgn, m):
        """ Add statements for the RESET state. """

        # In the RESET state, set register is used to reset all lines in
        # the tag array.
        with m.Case(State.RESET):
            m.d.comb += dsgn.set.eq(dsgn.set + 1)


    def add_flush(self, dsgn, m):
        """ Add statements for the FLUSH state. """

        # In the FLUSH state, set register is used to write all dirty lines
        # back to DRAM.
        with m.Case(State.FLUSH):
            # If current set is clean or DRAM is available, increment the set
            # register when all ways in the set are checked
            with m.If((~dsgn.tag_array.output().dirty(dsgn.way) | ~dsgn.dram.stall()) & (dsgn.way == dsgn.num_ways - 1)):
                m.d.comb += dsgn.set.eq(dsgn.set + 1)


    def add_idle(self, dsgn, m):
        """ Add statements for the IDLE state. """

        # In the IDLE state, the request is decoded.
        with m.Case(State.IDLE):
            self.store_request(dsgn, m)


    def add_compare(self, dsgn, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, the request is decoded if current request is hit.
        with m.Case(State.COMPARE):
            for i in range(dsgn.num_ways):
                with dsgn.check_hit(m, i):
                    self.store_request(dsgn, m)


    def add_wait_read(self, dsgn, m):
        """ Add statements for the WAIT_READ state. """

        # In the COMPARE state, the request is decoded if DRAM completed read request
        with m.Case(State.WAIT_READ):
            with m.If(~dsgn.dram.stall()):
                self.store_request(dsgn, m)


    def store_request(self, dsgn, m):
        """ Decode and store the request signals in flip-flops. """

        m.d.comb += dsgn.tag.eq(dsgn.addr.parse_tag())
        m.d.comb += dsgn.set.eq(dsgn.addr.parse_set())
        m.d.comb += dsgn.offset.eq(dsgn.addr.parse_offset())
        m.d.comb += dsgn.web_reg.eq(dsgn.web)
        if dsgn.num_masks:
            m.d.comb += dsgn.wmask_reg.eq(dsgn.wmask)
        m.d.comb += dsgn.din_reg.eq(dsgn.din)