# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from replacement_block_base import replacement_block_base
from nmigen import Const
from state import State


class replacement_block_lru(replacement_block_base):
    """
    This class extends base replacement module for LRU replacement policy.
    """

    def __init__(self):

        super().__init__()


    def add_reset_sig(self, dsgn, m):
        """ Add reset signal control. """

        # If rst is high, way is reset and use numbers are reset.
        # way register becomes 0 since it is going to be used to reset all
        # ways in tag and use lines.
        with m.If(dsgn.rst):
            m.d.comb += dsgn.way.eq(0)
            m.d.comb += dsgn.use_write_csb.eq(0)
            m.d.comb += dsgn.use_write_addr.eq(0)
            m.d.comb += dsgn.use_write_din.eq(0)


    def add_flush_sig(self, dsgn, m):
        """ Add flush signal control. """

        # If flush is high, way is reset.
        # way register becomes 0 since it is going to be used to write all
        # data lines back to DRAM.
        with m.Elif(dsgn.flush):
            m.d.comb += dsgn.way.eq(0)


    def add_states(self, dsgn, m):
        """ Add statements for each cache state. """

        with m.Else():
            with m.Switch(dsgn.state):
                super().add_states(dsgn, m)


    def add_reset(self, dsgn, m):
        """ Add statements for the RESET state. """

        # In the RESET state, way register is used to reset all ways in tag
        # and use lines.
        with m.Case(State.RESET):
            m.d.comb += dsgn.use_write_csb.eq(0)
            m.d.comb += dsgn.use_write_addr.eq(dsgn.set)
            m.d.comb += dsgn.use_write_din.eq(0)


    def add_flush(self, dsgn, m):
        """ Add statements for the FLUSH state. """

        # In the FLUSH state, way register is used to write all data lines
        # back to DRAM.
        with m.Case(State.FLUSH):
            # If current set is clean or DRAM is available, increment the way register
            with m.If((~dsgn.tag_read_dout.dirty(dsgn.way) | ~dsgn.main_stall)):
                m.d.comb += dsgn.way.eq(dsgn.way + 1)


    def add_idle(self, dsgn, m):
        """ Add statements for the IDLE state. """

        # In the IDLE state, way is reset and the corresponding line from the
        # use array is requested.
        with m.Case(State.IDLE):
            # Read next lines from SRAMs even though CPU is not sending a new
            # request since read is non-destructive.
            m.d.comb += dsgn.use_read_addr.eq(dsgn.addr.parse_set())


    def add_wait_hazard(self, dsgn, m):
        """ Add statements for the WAIT_HAZARD state. """

        # In the WAIT_READ state, corresponding line from the use array is
        # requested.
        with m.Case(State.WAIT_HAZARD):
            m.d.comb += dsgn.use_read_addr.eq(dsgn.set)


    def add_compare(self, dsgn, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, way is selected according to the replacement
        # policy of the cache.
        # Also use numbers are updated if current request is hit.
        with m.Case(State.COMPARE):
            for i in range(dsgn.num_ways):
                # Find the least recently used way (the way having 0 use number)
                with m.If(dsgn.use_read_dout.use(i) == Const(0, dsgn.way_size)):
                    # Check if current request is clean miss
                    m.d.comb += dsgn.way.eq(i)
                    with dsgn.check_dirty_miss(m, i):
                        m.d.comb += dsgn.use_read_addr.eq(dsgn.set)
            # Check if current request is a hit
            for i in range(dsgn.num_ways):
                with dsgn.check_hit(m, i):
                    m.d.comb += dsgn.use_write_csb.eq(0)
                    m.d.comb += dsgn.use_write_addr.eq(dsgn.set)
                    # Each way in a set has its own use numbers. These numbers
                    # start from 0. Every time a way is needed to be evicted,
                    # the way having 0 use number is chosen.
                    # Every time a way is accessed (read or write), its corresponding
                    # use number is increased to the maximum value and other ways which
                    # have use numbers more than accessed way's use number are decremented
                    # by 1.
                    for j in range(dsgn.num_ways):
                        m.d.comb += dsgn.use_write_din.use(j).eq(dsgn.use_read_dout.use(j) - (dsgn.use_read_dout.use(j) > dsgn.use_read_dout.use(i)))
                    m.d.comb += dsgn.use_write_din.use(i).eq(dsgn.num_ways - 1)
                    # Read next lines from SRAMs even though CPU is not
                    # sending a new request since read is non-destructive.
                    m.d.comb += dsgn.use_read_addr.eq(dsgn.addr.parse_set())


    def add_wait_write(self, dsgn, m):
        """ Add statements for the WAIT_WRITE state. """

        # In the WAIT_WRITE and READ states, use line is read to update it
        # in the WAIT_READ state.
        with m.Case(State.WAIT_WRITE):
            m.d.comb += dsgn.use_read_addr.eq(dsgn.set)


    def add_read(self, dsgn, m):
        """ Add statements for the READ state. """

        # In the WAIT_WRITE and READ states, use line is read to update it
        # in the WAIT_READ state.
        with m.Case(State.READ):
            m.d.comb += dsgn.use_read_addr.eq(dsgn.set)


    def add_wait_read(self, dsgn, m):
        """ Add statements for the WAIT_READ state. """

        # In the WAIT_READ state, use numbers are updated.
        with m.Case(State.WAIT_READ):
            m.d.comb += dsgn.use_read_addr.eq(dsgn.set)
            with m.If(~dsgn.main_stall):
                # Each way in a set has its own use numbers. These numbers
                # start from 0. Every time a way is needed to be evicted, the
                # way having 0 use number is chosen.
                # Every time a way is accessed (read or write), its corresponding
                # use number is increased to the maximum value and other ways which
                # have use numbers more than accessed way's use number are decremented
                # by 1.
                m.d.comb += dsgn.use_write_csb.eq(0)
                m.d.comb += dsgn.use_write_addr.eq(dsgn.set)
                for i in range(dsgn.num_ways):
                    m.d.comb += dsgn.use_write_din.use(i).eq(dsgn.use_read_dout.use(i) - (dsgn.use_read_dout.use(i) > dsgn.use_read_dout.use(dsgn.way)))
                with m.Switch(dsgn.way):
                    for i in range(dsgn.num_ways):
                        with m.Case(i):
                            m.d.comb += dsgn.use_write_din.use(i).eq(dsgn.num_ways - 1)
                # Read next lines from SRAMs even though CPU is not
                # sending a new request since read is non-destructive.
                m.d.comb += dsgn.use_read_addr.eq(dsgn.addr.parse_set())