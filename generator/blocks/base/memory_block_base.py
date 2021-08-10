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
    data array, use array, and main memory.
    """

    def __init__(self):

        super().__init__()


    def add_reset_sig(self, dsgn, m):
        """ Add reset signal control. """

        # If rst is high, state switches to RESET.
        # Registers, which are reset only once, are reset here.
        # In the RESET state, cache will set all tag and use array lines to 0.
        with m.If(dsgn.rst):
            m.d.comb += dsgn.tag_write_csb.eq(0)
            m.d.comb += dsgn.tag_write_addr.eq(0)
            m.d.comb += dsgn.tag_write_din.eq(0)


    def add_flush_sig(self, dsgn, m):
        """ Add flush signal control. """

        # If flush is high, state switches to FLUSH.
        # In the FLUSH state, cache will write all data lines back to main memory.
        with m.Elif(dsgn.flush):
            m.d.comb += dsgn.tag_read_addr.eq(0)
            m.d.comb += dsgn.data_read_addr.eq(0)


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
            m.d.comb += dsgn.tag_write_csb.eq(0)
            m.d.comb += dsgn.tag_write_addr.eq(dsgn.set)
            m.d.comb += dsgn.tag_write_din.eq(0)


    def add_flush(self, dsgn, m):
        """ Add statements for the FLUSH state. """

        # In the FLUSH state, cache sends write request to main memory.
        # set register is incremented by the Request Block.
        # way register is incremented by the Replacement Block.
        # When set and way registers reach the end, state switches to IDLE.
        with m.Case(State.FLUSH):
            m.d.comb += dsgn.tag_read_addr.eq(dsgn.set)
            m.d.comb += dsgn.data_read_addr.eq(dsgn.set)
            with m.Switch(dsgn.way):
                for i in range(dsgn.num_ways):
                    with m.Case(i):
                        # Check if current set is clean or main memory is available,
                        # and all ways of the set are checked
                        if i == dsgn.num_ways - 1:
                            with m.If(~dsgn.tag_read_dout.dirty(i) | ~dsgn.main_stall):
                                # Request the next tag and data lines from SRAMs
                                m.d.comb += dsgn.tag_read_addr.eq(dsgn.set + 1)
                                m.d.comb += dsgn.data_read_addr.eq(dsgn.set + 1)
                        # Check if current set is dirty and main memory is available
                        with m.If(dsgn.tag_read_dout.dirty(i) & ~dsgn.main_stall):
                            # Update dirty bits in the tag line
                            m.d.comb += dsgn.tag_write_csb.eq(0)
                            m.d.comb += dsgn.tag_write_addr.eq(dsgn.set)
                            m.d.comb += dsgn.tag_write_din.eq(dsgn.tag_read_dout)
                            m.d.comb += dsgn.tag_write_din.tag_word(i).eq(Cat(dsgn.tag_read_dout.tag(i), 0b10))
                            # Send the write request to main memory
                            m.d.comb += dsgn.main_csb.eq(0)
                            m.d.comb += dsgn.main_web.eq(0)
                            m.d.comb += dsgn.main_addr.eq(Cat(dsgn.set, dsgn.tag_read_dout.tag(i)))
                            m.d.comb += dsgn.main_din.eq(dsgn.data_read_dout.line(i))


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
            m.d.comb += dsgn.tag_read_addr.eq(dsgn.addr.parse_set())
            m.d.comb += dsgn.data_read_addr.eq(dsgn.addr.parse_set())


    def add_wait_hazard(self, dsgn, m):
        """ Add statements for the WAIT_HAZARD state. """

        # In the WAIT_HAZARD state, cache waits in this state for 1 cycle.
        # Read requests are sent to tag and data arrays.
        with m.Case(State.WAIT_HAZARD):
            m.d.comb += dsgn.tag_read_addr.eq(dsgn.set)
            m.d.comb += dsgn.data_read_addr.eq(dsgn.set)


    def add_compare(self, dsgn, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, cache compares tags.
        with m.Case(State.COMPARE):
            # Assuming that current request is miss, check if it is dirty miss
            with dsgn.check_dirty_miss(m):
                # If main memory is busy, switch to WRITE and wait for main
                # memory to be available.
                with m.If(dsgn.main_stall):
                    m.d.comb += dsgn.tag_read_addr.eq(dsgn.set)
                    m.d.comb += dsgn.data_read_addr.eq(dsgn.set)
                # If main memory is available, switch to WAIT_WRITE and wait for
                # main memory to complete writing.
                with m.Else():
                    m.d.comb += dsgn.main_csb.eq(0)
                    m.d.comb += dsgn.main_web.eq(0)
                    m.d.comb += dsgn.main_addr.eq(Cat(dsgn.set, dsgn.tag_read_dout.tag()))
                    m.d.comb += dsgn.main_din.eq(dsgn.data_read_dout)
            # Else, assume that current request is clean miss
            with dsgn.check_clean_miss(m):
                # If main memory is busy, switch to WRITE and wait for main memory
                # to be available.
                # If main memory is available, switch to WAIT_WRITE and wait for
                # main memory to complete writing.
                with m.If(~dsgn.main_stall):
                    m.d.comb += dsgn.main_csb.eq(0)
                    m.d.comb += dsgn.main_addr.eq(Cat(dsgn.set, dsgn.tag))
            # Check if current request is hit
            with dsgn.check_hit(m):
                # Set main memory's csb to 1 again since it could be set 0 above
                m.d.comb += dsgn.main_csb.eq(1)
                # Perform the write request
                with m.If(~dsgn.web_reg):
                    m.d.comb += dsgn.tag_write_csb.eq(0)
                    m.d.comb += dsgn.tag_write_addr.eq(dsgn.set)
                    m.d.comb += dsgn.tag_write_din.eq(Cat(dsgn.tag, 0b11))
                    m.d.comb += dsgn.data_write_csb.eq(0)
                    m.d.comb += dsgn.data_write_addr.eq(dsgn.set)
                    m.d.comb += dsgn.data_write_din.eq(dsgn.data_read_dout)
                    # Write the word over the write mask
                    # NOTE: This switch statement is written manually (not only with
                    # word_select) because word_select fails to generate correct case
                    # statements if offset calculation is a bit complex.
                    for i in range(dsgn.num_bytes):
                        with m.If(dsgn.wmask_reg[i]):
                            with m.Switch(dsgn.offset):
                                for j in range(dsgn.words_per_line):
                                    with m.Case(j):
                                        m.d.comb += dsgn.data_write_din.byte(i, j).eq(dsgn.din_reg.byte(i))
                # Read next lines from SRAMs even though the CPU is not sending
                # a new request since read is non-destructive.
                m.d.comb += dsgn.tag_read_addr.eq(dsgn.addr.parse_set())
                m.d.comb += dsgn.data_read_addr.eq(dsgn.addr.parse_set())


    def add_write(self, dsgn, m):
        """ Add statements for the WRITE state. """

        # In the WRITE state, cache waits for main memory to be available.
        # When main memory is available, write request is sent.
        with m.Case(State.WRITE):
            m.d.comb += dsgn.tag_read_addr.eq(dsgn.set)
            m.d.comb += dsgn.data_read_addr.eq(dsgn.set)
            # If main memory is busy, wait in this state.
            # If main memory is available, switch to WAIT_WRITE and wait for
            # main memory to complete writing.
            with m.If(~dsgn.main_stall):
                m.d.comb += dsgn.main_csb.eq(0)
                m.d.comb += dsgn.main_web.eq(0)
                m.d.comb += dsgn.main_addr.eq(Cat(dsgn.set, dsgn.tag_read_dout.tag(dsgn.way)))
                m.d.comb += dsgn.main_din.eq(dsgn.data_read_dout.line(dsgn.way))


    def add_wait_write(self, dsgn, m):
        """ Add statements for the WAIT_WRITE state. """

        # In the WAIT_WRITE state, cache waits for main memory to complete
        # writing.
        # When main memory completes writing, read request is sent.
        with m.Case(State.WAIT_WRITE):
            m.d.comb += dsgn.tag_read_addr.eq(dsgn.set)
            m.d.comb += dsgn.data_read_addr.eq(dsgn.set)
            # If main memory is busy, wait in this state.
            # If main memory completes writing, switch to WAIT_READ and wait
            # for main memory to complete reading.
            with m.If(~dsgn.main_stall):
                m.d.comb += dsgn.main_csb.eq(0)
                m.d.comb += dsgn.main_addr.eq(Cat(dsgn.set, dsgn.tag))


    def add_read(self, dsgn, m):
        """ Add statements for the READ state. """

        # In the READ state, cache waits for main memory to be available.
        # When main memory is available, read request is sent.
        # TODO: Is this state really necessary? WAIT_WRITE state may be used instead
        with m.Case(State.READ):
            m.d.comb += dsgn.tag_read_addr.eq(dsgn.set)
            m.d.comb += dsgn.data_read_addr.eq(dsgn.set)
            # If main memory is busy, wait in this state.
            # If main memory completes writing, switch to WAIT_READ and wait
            # for main memory to complete reading.
            with m.If(~dsgn.main_stall):
                m.d.comb += dsgn.main_csb.eq(0)
                m.d.comb += dsgn.main_addr.eq(Cat(dsgn.set, dsgn.tag))


    def add_wait_read(self, dsgn, m):
        """ Add statements for the WAIT_READ state. """

        # In the WAIT_READ state, cache waits for main memory to complete
        # reading.
        # When main memory completes reading, request is completed.
        with m.Case(State.WAIT_READ):
            m.d.comb += dsgn.tag_read_addr.eq(dsgn.set)
            m.d.comb += dsgn.data_read_addr.eq(dsgn.set)
            # If main memory is busy, cache waits in this state.
            # If main memory completes reading, cache switches to:
            #   IDLE    if CPU isn't sending a new request
            #   COMPARE if CPU is sending a new request
            with m.If(~dsgn.main_stall):
                # TODO: Use wmask feature of OpenRAM
                m.d.comb += dsgn.tag_write_csb.eq(0)
                m.d.comb += dsgn.tag_write_addr.eq(dsgn.set)
                m.d.comb += dsgn.tag_write_din.eq(dsgn.tag_read_dout)
                # TODO: Optimize the below case statement
                with m.Switch(dsgn.way):
                    for i in range(dsgn.num_ways):
                        with m.Case(i):
                            m.d.comb += dsgn.tag_write_din.tag_word(i).eq(Cat(dsgn.tag, ~dsgn.web_reg, 0b1))
                m.d.comb += dsgn.data_write_csb.eq(0)
                m.d.comb += dsgn.data_write_addr.eq(dsgn.set)
                m.d.comb += dsgn.data_write_din.eq(dsgn.data_read_dout)
                # TODO: Optimize the below case statement.
                with m.Switch(dsgn.way):
                    for i in range(dsgn.num_ways):
                        with m.Case(i):
                            m.d.comb += dsgn.data_write_din.line(i).eq(dsgn.main_dout)
                # Perform the write request
                with m.If(~dsgn.web_reg):
                    # Write the word over the write mask
                    # NOTE: This switch statement is written manually (not only
                    # with word_select) because word_select fails to generate
                    # correct case statements if offset calculation is a bit
                    # complex.
                    for i in range(dsgn.num_bytes):
                        with m.If(dsgn.wmask_reg[i]):
                            with m.Switch(dsgn.way):
                                for j in range(dsgn.num_ways):
                                    with m.Case(j):
                                        with m.Switch(dsgn.offset):
                                            for k in range(dsgn.words_per_line):
                                                with m.Case(k):
                                                    m.d.comb += dsgn.data_write_din.byte(i, k, j).eq(dsgn.din_reg.byte(i))
                # Read next lines from SRAMs even though the CPU is not sending
                # a new request since read is non-destructive
                m.d.comb += dsgn.tag_read_addr.eq(dsgn.addr.parse_set())
                m.d.comb += dsgn.data_read_addr.eq(dsgn.addr.parse_set())