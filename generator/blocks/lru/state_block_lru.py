# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from state_block_base import state_block_base
from nmigen import Const
from state import State


class state_block_lru(state_block_base):
    """
    This class extends base state controller module for LRU replacement
    policy.
    """

    def __init__(self):

        super().__init__()


    def add_compare(self, dsgn, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, state switches to:
        #   IDLE        if current request is hit and CPU isn't sending a new request
        #   COMPARE     if current request is hit and CPU is sending a new request
        #   WAIT_HAZARD if current request is hit and data hazard is possible
        #   WRITE       if current request is dirty miss and DRAM is busy
        #   WAIT_WRITE  if current request is dirty miss and DRAM is available
        #   READ        if current request is clean miss and DRAM is busy
        #   WAIT_READ   if current request is clean miss and DRAM is available
        with m.Case(State.COMPARE):
            for i in range(dsgn.num_ways):
                # Find the least recently used way (the way having 0 use number)
                with m.If(dsgn.use_array.output().use(i) == Const(0, dsgn.way_size)):
                    # Assuming that current request is miss, check if it is dirty miss
                    with dsgn.check_dirty_miss(m, i):
                        with m.If(dsgn.dram.stall()):
                            m.d.comb += dsgn.state.eq(State.WRITE)
                        with m.Else():
                            m.d.comb += dsgn.state.eq(State.WAIT_WRITE)
                    # Else, current request is clean miss
                    with dsgn.check_clean_miss(m):
                        with m.If(dsgn.dram.stall()):
                            m.d.comb += dsgn.state.eq(State.READ)
                        with m.Else():
                            m.d.comb += dsgn.state.eq(State.WAIT_READ)
            # Find the least recently used way (the way having 0 use number)
            # Compare all ways' tags to find a hit. Since each way has a different
            # tag, only one of them can match at most.
            # NOTE: This for loop should not be merged with the one above since hit
            # should be checked after all miss assumptions are done.
            # TODO: This should be optimized.
            for i in range(dsgn.num_ways):
                with dsgn.check_hit(m, i):
                    with m.If(dsgn.csb):
                        m.d.comb += dsgn.state.eq(State.IDLE)
                    with m.Else():
                        with m.If(dsgn.set == dsgn.addr.parse_set()):
                            m.d.comb += dsgn.state.eq(State.WAIT_HAZARD)
                        with m.Else():
                            m.d.comb += dsgn.state.eq(State.COMPARE)