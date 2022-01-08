# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from block_base import block_base
from state import state
from globals import OPTS


class state_block_base(block_base):
    """
    This is the base class of state controller always block modules.
    Methods of this class can be overridden for specific implementation of
    different cache designs.

    In this block, cache's state is controlled. State flop is changed in order
    to switch between states.
    """

    def __init__(self):

        super().__init__()


    def add_reset(self, dsgn, m):
        """ Add statements for the RESET state. """

        # In the RESET state, state switches to IDLE if reset is completed.
        with m.Case(state.RESET):
            # When set reaches the limit, the last write request is sent to the
            # tag array.
            with m.If(dsgn.set == dsgn.num_rows - 1):
                m.d.comb += dsgn.state.eq(state.IDLE)


    def add_flush(self, dsgn, m):
        """ Add statements for the FLUSH state. """

        # In the FLUSH state, state switches to IDLE if flush is completed.
        with m.Case(state.FLUSH):
            # If the last set's last way is clean or DRAM will receive the last
            # write request, flush is completed.
            # FIXME: Cache switches to IDLE while DRAM is still writing
            # the last data line. This may cause a simulation mismatch.
            # This is the behavior that we probably want, so fix sim_cache
            # instead.
            with m.If((~dsgn.tag_array.output().dirty(dsgn.way) | ~dsgn.dram.stall()) & (dsgn.way == dsgn.num_ways - 1) & (dsgn.set == dsgn.num_rows - 1)):
                m.d.comb += dsgn.state.eq(state.IDLE)


    def add_idle(self, dsgn, m):
        """ Add statements for the IDLE state. """

        # In the IDLE state, state switches to COMPARE if CPU is sending a new
        # request.
        with m.Case(state.IDLE):
            with m.If(~dsgn.csb):
                m.d.comb += dsgn.state.eq(state.COMPARE)


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
            with dsgn.check_dirty_miss(m):
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
            # Check if current request is hit
            with dsgn.check_hit(m):
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


    def add_write(self, dsgn, m):
        """ Add statements for the WRITE state. """

        # In the WRITE state, state switches to:
        #   WRITE      if DRAM didn't respond yet
        #   WAIT_WRITE if DRAM responded
        with m.Case(state.WRITE):
            with m.If(~dsgn.dram.stall()):
                m.d.comb += dsgn.state.eq(state.WAIT_WRITE)


    def add_wait_write(self, dsgn, m):
        """ Add statements for the WAIT_WRITE state. """

        # In the WAIT_WRITE state, state switches to:
        #   WAIT_WRITE if DRAM didn't respond yet
        #   WAIT_READ  if DRAM responded
        with m.Case(state.WAIT_WRITE):
            with m.If(~dsgn.dram.stall()):
                m.d.comb += dsgn.state.eq(state.WAIT_READ)


    def add_read(self, dsgn, m):
        """ Add statements for the READ state. """

        # In the READ state, state switches to:
        #   READ      if DRAM didn't respond yet
        #   WAIT_READ if DRAM responded
        with m.Case(state.READ):
            with m.If(~dsgn.dram.stall()):
                m.d.comb += dsgn.state.eq(state.WAIT_READ)


    def add_wait_read(self, dsgn, m):
        """ Add statements for the WAIT_READ state. """

        # In the WAIT_READ state, state switches to:
        #   IDLE        if CPU isn't sending a new request
        #   WAIT_HAZARD if data hazard is possible
        #   COMPARE     if CPU is sending a new request
        with m.Case(state.WAIT_READ):
            with m.If(~dsgn.dram.stall()):
                with m.If(dsgn.csb):
                    m.d.comb += dsgn.state.eq(state.IDLE)
                with m.Else():
                    # Don't use WAIT_HAZARD if data_hazard is disabled
                    if OPTS.data_hazard:
                        with m.If(dsgn.set == dsgn.addr.parse_set()):
                            m.d.comb += dsgn.state.eq(state.WAIT_HAZARD)
                        with m.Else():
                            m.d.comb += dsgn.state.eq(state.COMPARE)
                    else:
                        m.d.comb += dsgn.state.eq(state.COMPARE)


    def add_flush_hazard(self, dsgn, m):
        """ Add statements for the FLUSH_HAZARD state. """

        # In the FLUSH_HAZARD state, state switches to FLUSH.
        # This state is used to prevent data hazard.
        # Data hazard might occur when there are read and write requests to the
        # same address of SRAMs.
        # This state delays the cache request 1 cycle so that read requests
        # will be performed after write is completed.
        with m.Case(state.FLUSH_HAZARD):
            m.d.comb += dsgn.state.eq(state.FLUSH)


    def add_wait_hazard(self, dsgn, m):
        """ Add statements for the WAIT_HAZARD state. """

        # In the WAIT_HAZARD state, state switches to COMPARE.
        # This state is used to prevent data hazard.
        # Data hazard might occur when there are read and write requests to the
        # same address of SRAMs.
        # This state delays the cache request 1 cycle so that read requests
        # will be performed after write is completed.
        with m.Case(state.WAIT_HAZARD):
            m.d.comb += dsgn.state.eq(state.COMPARE)


    def add_flush_sig(self, dsgn, m):
        """ Add flush signal control. """

        # If flush is high, state switches to FLUSH.
        with m.If(dsgn.flush):
            # Don't use FLUSH_HAZARD if data_hazard is disabled
            if OPTS.data_hazard:
                # If set register is 0, data hazard might occur. In order to
                # prevent this, cache will switch to FLUSH_HAZARD state.
                with m.If(dsgn.set):
                    m.d.comb += dsgn.state.eq(state.FLUSH)
                with m.Else():
                    m.d.comb += dsgn.state.eq(state.FLUSH_HAZARD)
            else:
                m.d.comb += dsgn.state.eq(state.FLUSH)


    def add_reset_sig(self, dsgn, m):
        """ Add reset signal control. """

        # If rst is high, state switches to RESET.
        with m.If(dsgn.rst):
            m.d.comb += dsgn.state.eq(state.RESET)