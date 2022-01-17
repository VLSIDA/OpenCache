# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from block_base import block_base
from state import state


class output_block_base(block_base):
    """
    This is the base class of output controller always block modules.
    Methods of this class can be overridden for specific implementation of
    different cache designs.

    In this block, cache's output signals, which are stall and dout, are
    controlled.
    """

    def __init__(self):

        super().__init__()


    def add_idle(self, c, m):
        """ Add statements for the IDLE state. """

        # In the IDLE state, stall is low while there is no request from the CPU.
        # When there is a request, state switches to COMPARE and stall becomes
        # high in the next cycle.
        with m.Case(state.IDLE):
            m.d.comb += c.stall.eq(0)


    def add_compare(self, c, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, stall is low if the current request is hit.
        # Data output is valid if the request is hit and even if the current
        # request is write since read is non-destructive.
        with m.Case(state.COMPARE):
            for i in c.hit_detector.find_hit():
                m.d.comb += c.stall.eq(0)
                m.d.comb += c.dout.eq(c.data_array.output(i).word(c.offset))


    def add_wait_read(self, c, m):
        """ Add statements for the WAIT_READ state. """

        # In the WAIT_READ state, stall is low and data output is valid when DRAM
        # completes the read request.
        # Data output is valid even if the current request is write since read
        # is non-destructive.
        with m.Case(state.WAIT_READ):
            # Check if DRAM answers to the read request
            with m.If(~c.dram.stall()):
                m.d.comb += c.stall.eq(0)
                m.d.comb += c.dout.eq(c.dram.output().word(c.offset))