# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from replacement_block_base import replacement_block_base
from state import State


class replacement_block_fifo(replacement_block_base):
    """
    This class extends base replacement module for FIFO replacement policy.
    """

    def __init__(self):

        super().__init__()


    def add_reset_sig(self, dsgn, m):
        """ Add reset signal control. """

        # If rst is high, way is reset and FIFO numbers are reset.
        # way register becomes 0 since it is going to be used to reset all ways
        # in FIFO and tag lines.
        with m.If(dsgn.rst):
            m.d.comb += dsgn.way.eq(0)
            dsgn.use_array.write(0, 0)


    def add_flush_sig(self, dsgn, m):
        """ Add flush signal control. """

        # If flush is high, way is reset.
        # way register becomes 0 since it is going to be used to write all data
        # lines back to DRAM.
        with m.Elif(dsgn.flush):
            m.d.comb += dsgn.way.eq(0)


    def add_states(self, dsgn, m):
        """ Add statements for each cache state. """

        with m.Else():
            with m.Switch(dsgn.state):
                super().add_states(dsgn, m)


    def add_reset(self, dsgn, m):
        """ Add statements for the RESET state. """

        # In the RESET state, way register is used to reset all ways in tag and
        # use lines.
        with m.Case(State.RESET):
            dsgn.use_array.write(dsgn.set, 0)


    def add_flush(self, dsgn, m):
        """ Add statements for the FLUSH state. """

        # In the FLUSH state, way register is used to write all data lines back
        # to DRAM.
        with m.Case(State.FLUSH):
            # If current set is clean or DRAM is available, increment the way register
            with m.If((~dsgn.tag_array.output().dirty(dsgn.way) | ~dsgn.dram.stall())):
                m.d.comb += dsgn.way.eq(dsgn.way + 1)


    def add_idle(self, dsgn, m):
        """ Add statements for the IDLE state. """

        # In the IDLE state, way is reset and the corresponding line from the
        # use array is requested.
        with m.Case(State.IDLE):
            # Read next lines from SRAMs even though CPU is not sending a new
            # request since read is non-destructive.
            dsgn.use_array.read(dsgn.addr.parse_set())


    def add_wait_hazard(self, dsgn, m):
        """ Add statements for the WAIT_HAZARD state. """

        # In the WAIT_READ state, corresponding line from the use array is
        # requested.
        with m.Case(State.WAIT_HAZARD):
            dsgn.use_array.read(dsgn.set)


    def add_compare(self, dsgn, m):
        """ Add statements for the COMPARE state. """


        # In the COMPARE state, way is selected according to the replacement
        # policy of the cache.
        with m.Case(State.COMPARE):
            m.d.comb += dsgn.way.eq(dsgn.use_array.output())
            # The corresponding use array line needs to be requested if current
            # request is hit.
            # Read next lines from SRAMs even though CPU is not sending a new
            # request since read is non-destructive.
            for i in range(dsgn.num_ways):
                with dsgn.check_hit(m, i):
                    dsgn.use_array.read(dsgn.addr.parse_set())


    def add_wait_read(self, dsgn, m):
        """ Add statements for the WAIT_READ state. """

        # In the WAIT_READ state, FIFO number are updated.
        with m.Case(State.WAIT_READ):
            with m.If(~dsgn.dram.stall()):
                # Each set has its own FIFO number. These numbers start from 0 and
                # always show the next way to be placed. When new data is placed on
                # that way, FIFO number is incremented.
                dsgn.use_array.write(dsgn.set, dsgn.way + 1)
                # Read next lines from SRAMs even though CPU is not
                # sending a new request since read is non-destructive.
                dsgn.use_array.read(dsgn.addr.parse_set())