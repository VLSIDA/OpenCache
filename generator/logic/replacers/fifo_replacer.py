# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from logic_base import logic_base
from state import state
from policy import write_policy as wp
from globals import OPTS


class fifo_replacer(logic_base):
    """
    This class extends base logic module for FIFO replacement policy.
    """

    def __init__(self):

        super().__init__()


    def add_reset(self, c, m):
        """ Add statements for the RESET state. """

        # In the RESET state, way register is used to reset all ways in tag and
        # use lines.
        with m.Case(state.RESET):
            c.use_array.write(c.set, 0)


    def add_flush(self, c, m):
        """ Add statements for the FLUSH state. """

        # In the FLUSH state, way register is used to write all data lines back
        # to DRAM.
        with m.Case(state.FLUSH):
            # If current set is clean or DRAM is available, increment the way register
            with m.If((~c.tag_array.output().dirty(c.way) | ~c.dram.stall())):
                m.d.comb += c.way.eq(c.way + 1)


    def add_idle(self, c, m):
        """ Add statements for the IDLE state. """

        # In the IDLE state, way is reset and the corresponding line from the
        # use array is requested.
        with m.Case(state.IDLE):
            # Read next lines from SRAMs even though CPU is not sending a new
            # request since read is non-destructive.
            c.use_array.read(c.addr.parse_set())


    def add_compare(self, c, m):
        """ Add statements for the COMPARE state. """


        # In the COMPARE state, way is selected according to the replacement
        # policy of the cache.
        with m.Case(state.COMPARE):
            m.d.comb += c.way.eq(c.use_array.output())
            # The corresponding use array line needs to be requested if current
            # request is hit.
            # Read next lines from SRAMs even though CPU is not sending a new
            # request since read is non-destructive.
            for i in c.hit_detector.find_hit():
                m.d.comb += c.way.eq(i)
                # If write policy is write-through, read next lines if current request
                # is read or DRAM is available.
                if OPTS.write_policy == wp.WRITE_THROUGH:
                    with m.If(c.web_reg | ~c.dram.stall()):
                        c.use_array.read(c.addr.parse_set())
                else:
                    c.use_array.read(c.addr.parse_set())


    def add_write(self, c, m):
        """ Add statements for the WRITE state. """

        # If write policy is not write-through, don't generate this state.
        if OPTS.write_policy != wp.WRITE_THROUGH:
            return

        # In the WAIT_READ state, corresponding line from the use array is
        # requested if DRAM is available.
        with m.Case(state.WRITE):
            with m.If(~c.dram.stall()):
                c.use_array.read(c.addr.parse_set())


    def add_wait_read(self, c, m):
        """ Add statements for the WAIT_READ state. """

        # In the WAIT_READ state, FIFO number are updated.
        with m.Case(state.WAIT_READ):
            with m.If(~c.dram.stall()):
                # Each set has its own FIFO number. These numbers start from 0 and
                # always show the next way to be placed. When new data is placed on
                # that way, FIFO number is incremented.
                c.use_array.write(c.set, c.way + 1)
                # Read next lines from SRAMs even if CPU is not sending a new request
                # since read is non-destructive.
                c.use_array.read(c.addr.parse_set())


    def add_wait_hazard(self, c, m):
        """ Add statements for the WAIT_HAZARD state. """

        # In the WAIT_READ state, corresponding line from the use array is
        # requested.
        with m.Case(state.WAIT_HAZARD):
            c.use_array.read(c.set)


    def add_flush_sig(self, c, m):
        """ Add flush signal control. """

        # If flush is high, way is reset.
        # way register becomes 0 since it is going to be used to write all data
        # lines back to DRAM.
        with m.If(c.flush):
            m.d.comb += c.way.eq(0)


    def add_reset_sig(self, c, m):
        """ Add reset signal control. """

        # If rst is high, way is reset and FIFO numbers are reset.
        # way register becomes 0 since it is going to be used to reset all ways
        # in FIFO and tag lines.
        with m.If(c.rst):
            m.d.comb += c.way.eq(0)