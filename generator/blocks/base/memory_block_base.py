# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from block_base import block_base
from nmigen import Cat
from state import State


class memory_block_base(block_base):
    """
    This is the base class of memory controller always block modules.
    Methods of this class can be overridden for specific implementation of
    different cache designs.

    In this block, cache communicates with memory components such as tag array,
    data array, use array, and DRAM.
    """

    def __init__(self):

        super().__init__()


    def add_reset_sig(self, dsgn, m):
        """ Add reset signal control. """

        # If rst is high, state switches to RESET.
        # Registers, which are reset only once, are reset here.
        # In the RESET state, cache will set all tag and use array lines to 0.
        with m.If(dsgn.rst):
            dsgn.tag_array.write(0, 0)


    def add_flush_sig(self, dsgn, m):
        """ Add flush signal control. """

        # If flush is high, state switches to FLUSH.
        # In the FLUSH state, cache will write all data lines back to DRAM.
        with m.Elif(dsgn.flush):
            dsgn.tag_array.read(0)
            dsgn.data_array.read(0)


    def add_states(self, dsgn, m):
        """ Add statements for each cache state. """

        with m.Else():
            with m.Switch(dsgn.state):
                super().add_states(dsgn, m)


    def add_reset(self, dsgn, m):
        """ Add statements for the RESET state. """

        # In the RESET state, cache sends write request to the tag array to reset
        # the current set.
        # set register is incremented by the Request Block.
        # When set register reaches the end, state switches to IDLE.
        with m.Case(State.RESET):
            dsgn.tag_array.write(dsgn.set, 0)


    def add_flush(self, dsgn, m):
        """ Add statements for the FLUSH state. """

        # In the FLUSH state, cache sends write request to DRAM.
        # set register is incremented by the Request Block.
        # way register is incremented by the Replacement Block.
        # When set and way registers reach the end, state switches to IDLE.
        with m.Case(State.FLUSH):
            dsgn.tag_array.read(dsgn.set)
            dsgn.data_array.read(dsgn.set)
            with m.Switch(dsgn.way):
                for i in range(dsgn.num_ways):
                    with m.Case(i):
                        # Check if current set is clean or DRAM is available,
                        # and all ways of the set are checked
                        if i == dsgn.num_ways - 1:
                            with m.If(~dsgn.tag_array.output().dirty(i) | ~dsgn.main_stall):
                                # Request the next tag and data lines from SRAMs
                                dsgn.tag_array.read(dsgn.set + 1)
                                dsgn.data_array.read(dsgn.set + 1)
                        # Check if current set is dirty and DRAM is available
                        with m.If(dsgn.tag_array.output().dirty(i) & ~dsgn.main_stall):
                            # Update dirty bits in the tag line
                            dsgn.tag_array.write(dsgn.set, Cat(dsgn.tag_array.output().tag(i), 0b10), i)
                            # Send the write request to DRAM
                            m.d.comb += dsgn.main_csb.eq(0)
                            m.d.comb += dsgn.main_web.eq(0)
                            m.d.comb += dsgn.main_addr.eq(Cat(dsgn.set, dsgn.tag_array.output().tag(i)))
                            m.d.comb += dsgn.main_din.eq(dsgn.data_array.output().line(i))


    def add_idle(self, dsgn, m):
        """ Add statements for the IDLE state. """

        # In the IDLE state, cache waits for CPU to send a new request.
        # Until there is a new request from the cache, stall is low.
        # When there is a new request from the cache stall is asserted, request
        # is decoded and corresponding tag, data, and use array lines are read
        # from internal SRAMs.
        with m.Case(State.IDLE):
            # Read next lines from SRAMs even though CPU is not sending a new
            # request since read is non-destructive.
            dsgn.tag_array.read(dsgn.addr.parse_set())
            dsgn.data_array.read(dsgn.addr.parse_set())


    def add_wait_hazard(self, dsgn, m):
        """ Add statements for the WAIT_HAZARD state. """

        # In the WAIT_HAZARD state, cache waits in this state for 1 cycle.
        # Read requests are sent to tag and data arrays.
        with m.Case(State.WAIT_HAZARD):
            dsgn.tag_array.read(dsgn.set)
            dsgn.data_array.read(dsgn.set)


    def add_compare(self, dsgn, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, cache compares tags.
        with m.Case(State.COMPARE):
            dsgn.tag_array.read(dsgn.set)
            dsgn.data_array.read(dsgn.set)
            # Assuming that current request is miss, check if it is dirty miss
            with dsgn.check_dirty_miss(m):
                # If DRAM is available, switch to WAIT_WRITE and wait for DRAM to
                # complete writing
                with m.If(~dsgn.main_stall):
                    m.d.comb += dsgn.main_csb.eq(0)
                    m.d.comb += dsgn.main_web.eq(0)
                    m.d.comb += dsgn.main_addr.eq(Cat(dsgn.set, dsgn.tag_array.output().tag()))
                    m.d.comb += dsgn.main_din.eq(dsgn.data_array.output())
            # Else, assume that current request is clean miss
            with dsgn.check_clean_miss(m):
                # If DRAM is busy, switch to WRITE and wait for DRAM to be available
                # If DRAM is available, switch to WAIT_WRITE and wait for DRAM to
                # complete writing
                with m.If(~dsgn.main_stall):
                    m.d.comb += dsgn.main_csb.eq(0)
                    m.d.comb += dsgn.main_addr.eq(Cat(dsgn.set, dsgn.tag))
            # Check if current request is hit
            with dsgn.check_hit(m):
                # Set DRAM's csb to 1 again since it could be set 0 above
                m.d.comb += dsgn.main_csb.eq(1)
                # Perform the write request
                with m.If(~dsgn.web_reg):
                    # Update dirty bit in the tag line
                    dsgn.tag_array.write(dsgn.set, Cat(dsgn.tag, 0b11))
                    dsgn.data_array.write(dsgn.set, dsgn.data_array.output())
                    dsgn.data_array.write_bytes(dsgn.wmask_reg, 0, dsgn.offset, dsgn.din_reg)
                # Read next lines from SRAMs even though the CPU is not sending
                # a new request since read is non-destructive.
                dsgn.tag_array.read(dsgn.addr.parse_set())
                dsgn.data_array.read(dsgn.addr.parse_set())


    def add_write(self, dsgn, m):
        """ Add statements for the WRITE state. """

        # In the WRITE state, cache waits for DRAM to be available.
        # When DRAM is available, write request is sent.
        with m.Case(State.WRITE):
            dsgn.tag_array.read(dsgn.set)
            dsgn.data_array.read(dsgn.set)
            # If DRAM is busy, wait in this state.
            # If DRAM is available, switch to WAIT_WRITE and wait for DRAM to
            # complete writing.
            with m.If(~dsgn.main_stall):
                m.d.comb += dsgn.main_csb.eq(0)
                m.d.comb += dsgn.main_web.eq(0)
                m.d.comb += dsgn.main_addr.eq(Cat(dsgn.set, dsgn.tag_array.output().tag(dsgn.way)))
                m.d.comb += dsgn.main_din.eq(dsgn.data_array.output().line(dsgn.way))


    def add_wait_write(self, dsgn, m):
        """ Add statements for the WAIT_WRITE state. """

        # In the WAIT_WRITE state, cache waits for DRAM to complete writing.
        # When DRAM completes writing, read request is sent.
        with m.Case(State.WAIT_WRITE):
            dsgn.tag_array.read(dsgn.set)
            dsgn.data_array.read(dsgn.set)
            # If DRAM is busy, wait in this state.
            # If DRAM completes writing, switch to WAIT_READ and wait for DRAM to
            # complete reading.
            with m.If(~dsgn.main_stall):
                m.d.comb += dsgn.main_csb.eq(0)
                m.d.comb += dsgn.main_addr.eq(Cat(dsgn.set, dsgn.tag))


    def add_read(self, dsgn, m):
        """ Add statements for the READ state. """

        # In the READ state, cache waits for DRAM to be available.
        # When DRAM is available, read request is sent.
        # TODO: Is this state really necessary? WAIT_WRITE state may be used instead
        with m.Case(State.READ):
            dsgn.tag_array.read(dsgn.set)
            dsgn.data_array.read(dsgn.set)
            # If DRAM is busy, wait in this state.
            # If DRAM completes writing, switch to WAIT_READ and wait for DRAM to
            # complete reading.
            with m.If(~dsgn.main_stall):
                m.d.comb += dsgn.main_csb.eq(0)
                m.d.comb += dsgn.main_addr.eq(Cat(dsgn.set, dsgn.tag))


    def add_wait_read(self, dsgn, m):
        """ Add statements for the WAIT_READ state. """

        # In the WAIT_READ state, cache waits for DRAM to complete reading
        # When DRAM completes reading, request is completed.
        with m.Case(State.WAIT_READ):
            dsgn.tag_array.read(dsgn.set)
            dsgn.data_array.read(dsgn.set)
            # If DRAM is busy, cache waits in this state.
            # If DRAM completes reading, cache switches to:
            #   IDLE    if CPU isn't sending a new request
            #   COMPARE if CPU is sending a new request
            with m.If(~dsgn.main_stall):
                dsgn.tag_array.write(dsgn.set, Cat(dsgn.tag, ~dsgn.web_reg, 0b1), dsgn.way)
                dsgn.data_array.write(dsgn.set, dsgn.main_dout, dsgn.way)
                # Perform the write request
                with m.If(~dsgn.web_reg):
                    dsgn.data_array.write_bytes(dsgn.wmask_reg, dsgn.way, dsgn.offset, dsgn.din_reg)
                # Read next lines from SRAMs even though the CPU is not sending
                # a new request since read is non-destructive
                dsgn.tag_array.read(dsgn.addr.parse_set())
                dsgn.data_array.read(dsgn.addr.parse_set())