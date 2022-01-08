# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from state_block_base import state_block_base
from state import state
from globals import OPTS


class state_block_fifo(state_block_base):
    """
    This class extends base state controller module for FIFO replacement
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
        with m.Case(state.COMPARE):
            # Assuming that current request is miss, check if it is dirty miss
            with dsgn.check_dirty_miss(m, dsgn.use_array.output()):
                with m.If(dsgn.dram.stall()):
                    m.d.comb += dsgn.state.eq(state.WRITE)
                with m.Else():
                    m.d.comb += dsgn.state.eq(state.WAIT_WRITE)
            # Else, assume that current request is clean miss
            with dsgn.check_clean_miss(m):
                with m.If(dsgn.dram.stall()):
                    m.d.comb += dsgn.state.eq(state.READ)
                with m.Else():
                    m.d.comb += dsgn.state.eq(state.WAIT_READ)
            # Check if current request is hit.
            # Compare all ways' tags to find a hit. Since each way has a different
            # tag, only one of them can match at most.
            for i in range(dsgn.num_ways):
                with dsgn.check_hit(m, i):
                    with m.If(dsgn.csb):
                        m.d.comb += dsgn.state.eq(state.IDLE)
                    with m.Else():
                        # Don't use WAIT_HAZARD if data_hazard is disabled
                        if OPTS.data_hazard:
                            with m.If(~dsgn.web_reg & (dsgn.set == dsgn.addr.parse_set())):
                                m.d.comb += dsgn.state.eq(state.WAIT_HAZARD)
                            with m.Else():
                                m.d.comb += dsgn.state.eq(state.COMPARE)
                        else:
                            m.d.comb += dsgn.state.eq(state.COMPARE)