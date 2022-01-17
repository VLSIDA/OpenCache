# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from state_block_base import state_block_base
from amaranth import C
from state import state
from globals import OPTS


class state_block_lru(state_block_base):
    """
    This class extends base state controller module for LRU replacement
    policy.
    """

    def __init__(self):

        super().__init__()


    def add_compare(self, c, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, state switches to:
        #   IDLE        if current request is hit and CPU isn't sending a new request
        #   COMPARE     if current request is hit and CPU is sending a new request
        #   WAIT_HAZARD if current request is hit and data hazard is possible
        #   WRITE       if current request is dirty miss and DRAM is busy
        #   WAIT_WRITE  if current request is dirty miss and DRAM is available
        #   READ        if current request is clean miss and DRAM is busy
        #   WAIT_READ   if current request is clean miss and DRAM is available
        with m.Case(state.COMPARE):
            for is_dirty, i in c.hit_detector.find_miss():
                # Assuming that current request is miss, check if it is dirty miss
                if is_dirty:
                    with m.If(c.dram.stall()):
                        m.d.comb += c.state.eq(state.WRITE)
                    with m.Else():
                        m.d.comb += c.state.eq(state.WAIT_WRITE)
                # Else, current request is clean miss
                else:
                    with m.If(c.dram.stall()):
                        m.d.comb += c.state.eq(state.READ)
                    with m.Else():
                        m.d.comb += c.state.eq(state.WAIT_READ)
            # Find the least recently used way (the way having 0 use number)
            # Compare all ways' tags to find a hit. Since each way has a different
            # tag, only one of them can match at most.
            # NOTE: This for loop should not be merged with the one above since hit
            # should be checked after all miss assumptions are done.
            # TODO: This should be optimized.
            for i in c.hit_detector.find_hit():
                with m.If(c.csb):
                    m.d.comb += c.state.eq(state.IDLE)
                with m.Else():
                    # Don't use WAIT_HAZARD if data_hazard is disabled
                    if OPTS.data_hazard:
                        with m.If(c.set == c.addr.parse_set()):
                            m.d.comb += c.state.eq(state.WAIT_HAZARD)
                        with m.Else():
                            m.d.comb += c.state.eq(state.COMPARE)
                    else:
                        m.d.comb += c.state.eq(state.COMPARE)