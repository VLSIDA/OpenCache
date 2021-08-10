# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from block_base import block_base
from state import State


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


    def add_reset_sig(self, dsgn, m):
        """ Add reset signal control. """

        # If rst is high, state switches to RESET.
        with m.If(dsgn.rst):
            m.d.comb += dsgn.state.eq(State.RESET)


    def add_flush_sig(self, dsgn, m):
        """ Add flush signal control. """

        # If flush is high, state switches to FLUSH.
        with m.Elif(dsgn.flush):
            m.d.comb += dsgn.state.eq(State.FLUSH)


    def add_states(self, dsgn, m):
        """ Add statements for each cache state. """

        with m.Else():
            with m.Switch(dsgn.state):
                super().add_states(dsgn, m)


    def add_reset(self, dsgn, m):
        """ Add statements for the RESET state. """

        # In the RESET state, state switches to IDLE if reset is completed.
        with m.Case(State.RESET):
            # When set reaches the limit, the last write request is sent to the
            # tag array.
            with m.If(dsgn.set == dsgn.num_rows - 1):
                m.d.comb += dsgn.state.eq(State.IDLE)


    def add_flush(self, dsgn, m):
        """ Add statements for the FLUSH state. """

        # In the FLUSH state, state switches to IDLE if flush is completed.
        with m.Case(State.FLUSH):
            # If the last set's last way is clean or main memory will receive
            # the last write request, flush is completed.
            # FIXME: Cache switches to IDLE while main memory is still writing
            # the last data line. This may cause a simulation mismatch.
            # This is the behavior that we probably want, so fix sim_cache
            # instead.
            with m.If((~dsgn.tag_read_dout.dirty(dsgn.way) | ~dsgn.main_stall) & (dsgn.way == dsgn.num_ways - 1) & (dsgn.set == dsgn.num_rows - 1)):
                m.d.comb += dsgn.state.eq(State.IDLE)


    def add_idle(self, dsgn, m):
        """ Add statements for the IDLE state. """

        # In the IDLE state, state switches to COMPARE if CPU is sending a new
        # request.
        with m.Case(State.IDLE):
            with m.If(~dsgn.csb):
                m.d.comb += dsgn.state.eq(State.COMPARE)


    def add_wait_hazard(self, dsgn, m):
        """ Add statements for the WAIT_HAZARD state. """

        # In the WAIT_HAZARD state, state switches to COMPARE.
        # This state is used to prevent data hazard.
        # Data hazard might occur when there are read and write requests to the
        # same address of SRAMs.
        # This state delays the cache request 1 cycle so that read requests
        # will be performed after write is completed.
        with m.Case(State.WAIT_HAZARD):
            m.d.comb += dsgn.state.eq(State.COMPARE)


    def add_compare(self, dsgn, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, state switches to:
        #   IDLE        if current request is hit and CPU isn't sending a new request
        #   COMPARE     if current request is hit and CPU is sending a new request
        #   WAIT_HAZARD if current request is hit and data hazard is possible
        #   WRITE       if current request is dirty miss and main memory is busy
        #   WAIT_WRITE  if current request is dirty miss and main memory is available
        #   READ        if current request is clean miss and main memory is busy
        #   WAIT_READ   if current request is clean miss and main memory is available
        with m.Case(State.COMPARE):
            # Assuming that current request is miss, check if it is dirty miss
            with dsgn.check_dirty_miss(m):
                with m.If(dsgn.main_stall):
                    m.d.comb += dsgn.state.eq(State.WRITE)
                with m.Else():
                    m.d.comb += dsgn.state.eq(State.WAIT_WRITE)
            # Else, assume that current request is clean miss
            with dsgn.check_clean_miss(m):
                with m.If(dsgn.main_stall):
                    m.d.comb += dsgn.state.eq(State.READ)
                with m.Else():
                    m.d.comb += dsgn.state.eq(State.WAIT_READ)
            # Check if current request is hit
            with dsgn.check_hit(m):
                with m.If(dsgn.csb):
                    m.d.comb += dsgn.state.eq(State.IDLE)
                with m.Else():
                    with m.If(~dsgn.web_reg & (dsgn.set == dsgn.addr.parse_set())):
                        m.d.comb += dsgn.state.eq(State.WAIT_HAZARD)
                    with m.Else():
                        m.d.comb += dsgn.state.eq(State.COMPARE)


    def add_write(self, dsgn, m):
        """ Add statements for the WRITE state. """

        # In the WRITE state, state switches to:
        #   WRITE      if main memory didn't respond yet
        #   WAIT_WRITE if main memory responded
        with m.Case(State.WRITE):
            with m.If(~dsgn.main_stall):
                m.d.comb += dsgn.state.eq(State.WAIT_WRITE)


    def add_wait_write(self, dsgn, m):
        """ Add statements for the WAIT_WRITE state. """

        # In the WAIT_WRITE state, state switches to:
        #   WAIT_WRITE if main memory didn't respond yet
        #   WAIT_READ  if main memory responded
        with m.Case(State.WAIT_WRITE):
            with m.If(~dsgn.main_stall):
                m.d.comb += dsgn.state.eq(State.WAIT_READ)


    def add_read(self, dsgn, m):
        """ Add statements for the READ state. """

        # In the READ state, state switches to:
        #   READ      if main memory didn't respond yet
        #   WAIT_READ if main memory responded
        with m.Case(State.READ):
            with m.If(~dsgn.main_stall):
                m.d.comb += dsgn.state.eq(State.WAIT_READ)


    def add_wait_read(self, dsgn, m):
        """ Add statements for the WAIT_READ state. """

        # In the WAIT_READ state, state switches to:
        #   IDLE        if CPU isn't sending a new request
        #   WAIT_HAZARD if data hazard is possible
        #   COMPARE     if CPU is sending a new request
        with m.Case(State.WAIT_READ):
            with m.If(~dsgn.main_stall):
                with m.If(dsgn.csb):
                    m.d.comb += dsgn.state.eq(State.IDLE)
                with m.Else():
                    with m.If(dsgn.set == dsgn.addr.parse_set()):
                        m.d.comb += dsgn.state.eq(State.WAIT_HAZARD)
                    with m.Else():
                        m.d.comb += dsgn.state.eq(State.COMPARE)