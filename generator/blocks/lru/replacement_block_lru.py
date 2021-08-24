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


    def add_reset(self, dsgn, m):
        """ Add statements for the RESET state. """

        # In the RESET state, way register is used to reset all ways in tag
        # and use lines.
        with m.Case(State.RESET):
            dsgn.use_array.write(dsgn.set, self.get_reset_value(dsgn))


    def add_flush(self, dsgn, m):
        """ Add statements for the FLUSH state. """

        # In the FLUSH state, way register is used to write all data lines
        # back to DRAM.
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
        # Also use numbers are updated if current request is hit.
        with m.Case(State.COMPARE):
            dsgn.use_array.read(dsgn.set)
            for i in range(dsgn.num_ways):
                # Find the least recently used way (the way having 0 use number)
                with m.If(dsgn.use_array.output().use(i) == Const(0, dsgn.way_size)):
                    # Check if current request is clean miss
                    m.d.comb += dsgn.way.eq(i)
            # Check if current request is a hit
            for i in range(dsgn.num_ways):
                with dsgn.check_hit(m, i):
                    dsgn.use_array.write(dsgn.set, dsgn.use_array.output())
                    # Each way in a set has its own use numbers. These numbers
                    # start from 0. Every time a way is needed to be evicted,
                    # the way having 0 use number is chosen.
                    # Every time a way is accessed (read or write), its corresponding
                    # use number is increased to the maximum value and other ways which
                    # have use numbers more than accessed way's use number are decremented
                    # by 1.
                    for j in range(dsgn.num_ways):
                        m.d.comb += dsgn.use_array.input().use(j).eq(dsgn.use_array.output().use(j) - (dsgn.use_array.output().use(j) > dsgn.use_array.output().use(i)))
                    m.d.comb += dsgn.use_array.input().use(i).eq(dsgn.num_ways - 1)
                    # Read next lines from SRAMs even though CPU is not
                    # sending a new request since read is non-destructive.
                    dsgn.use_array.read(dsgn.addr.parse_set())


    def add_wait_write(self, dsgn, m):
        """ Add statements for the WAIT_WRITE state. """

        # In the WAIT_WRITE and READ states, use line is read to update it
        # in the WAIT_READ state.
        with m.Case(State.WAIT_WRITE):
            dsgn.use_array.read(dsgn.set)


    def add_read(self, dsgn, m):
        """ Add statements for the READ state. """

        # In the WAIT_WRITE and READ states, use line is read to update it
        # in the WAIT_READ state.
        with m.Case(State.READ):
            dsgn.use_array.read(dsgn.set)


    def add_wait_read(self, dsgn, m):
        """ Add statements for the WAIT_READ state. """

        # In the WAIT_READ state, use numbers are updated.
        with m.Case(State.WAIT_READ):
            dsgn.use_array.read(dsgn.set)
            with m.If(~dsgn.dram.stall()):
                # Each way in a set has its own use numbers. These numbers
                # start from 0. Every time a way is needed to be evicted, the
                # way having 0 use number is chosen.
                # Every time a way is accessed (read or write), its corresponding
                # use number is increased to the maximum value and other ways which
                # have use numbers more than accessed way's use number are decremented
                # by 1.
                dsgn.use_array.write(dsgn.set, dsgn.use_array.output())
                for i in range(dsgn.num_ways):
                    m.d.comb += dsgn.use_array.input().use(i).eq(dsgn.use_array.output().use(i) - (dsgn.use_array.output().use(i) > dsgn.use_array.output().use(dsgn.way)))
                with m.Switch(dsgn.way):
                    for i in range(dsgn.num_ways):
                        with m.Case(i):
                            m.d.comb += dsgn.use_array.input().use(i).eq(dsgn.num_ways - 1)
                # Read next lines from SRAMs even though CPU is not
                # sending a new request since read is non-destructive.
                dsgn.use_array.read(dsgn.addr.parse_set())


    def add_flush_sig(self, dsgn, m):
        """ Add flush signal control. """

        # If flush is high, way is reset.
        # way register becomes 0 since it is going to be used to write all
        # data lines back to DRAM.
        with m.If(dsgn.flush):
            m.d.comb += dsgn.way.eq(0)


    def add_reset_sig(self, dsgn, m):
        """ Add reset signal control. """

        # If rst is high, way is reset and use numbers are reset.
        # way register becomes 0 since it is going to be used to reset all
        # ways in tag and use lines.
        with m.If(dsgn.rst):
            m.d.comb += dsgn.way.eq(0)


    def get_reset_value(self, dsgn):
        """ Return the reset value for use array lines. """

        reset_value = ["{0:0{1}b}".format(x, dsgn.way_size) for x in range(dsgn.num_ways)]
        reset_value.reverse()
        reset_value = "".join(reset_value)
        reset_value = int(reset_value, 2)

        return reset_value