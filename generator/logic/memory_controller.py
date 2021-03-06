# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from amaranth import Cat, C
from logic_base import logic_base
from state import state
from policy import write_policy as wp
from globals import OPTS


class memory_controller(logic_base):
    """
    This is the class of memory controller always block modules.

    In this block, cache communicates with memory components such as tag array,
    data array, use array, and DRAM.
    """

    def __init__(self):

        super().__init__()


    def add_reset(self, c, m):
        """ Add statements for the RESET state. """

        # In the RESET state, cache sends write request to the tag array to reset
        # the current set.
        # set register is incremented by the Request Block.
        # When set register reaches the end, state switches to IDLE.
        with m.Case(state.RESET):
            c.tag_array.write(c.set, 0)
            c.data_array.write(c.set, 0)


    def add_flush(self, c, m):
        """ Add statements for the FLUSH state. """

        # In the FLUSH state, cache sends write request to DRAM.
        # set register is incremented by the Request Block.
        # way register is incremented by the Replacement Block.
        # When set and way registers reach the end, state switches to IDLE.
        with m.Case(state.FLUSH):
            c.tag_array.read(c.set)
            c.data_array.read(c.set)
            with m.Switch(c.way):
                for i in range(c.num_ways):
                    with m.Case(i):
                        # Check if current set is clean or DRAM is available,
                        # and all ways of the set are checked
                        if i == c.num_ways - 1:
                            with m.If(~c.tag_array.output().dirty(i) | ~c.dram.stall()):
                                # Request the next tag and data lines from SRAMs
                                c.tag_array.read(c.set + 1)
                                c.data_array.read(c.set + 1)
                        # Check if current set is dirty and DRAM is available
                        with m.If(c.tag_array.output().dirty(i) & ~c.dram.stall()):
                            # Update dirty bits in the tag line
                            c.tag_array.write(c.set, Cat(c.tag_array.output().tag(i), C(2, 2)), i)
                            # Send the write request to DRAM
                            c.dram.write(Cat(c.set, c.tag_array.output().tag(i)), c.data_array.output(i))


    def add_idle(self, c, m):
        """ Add statements for the IDLE state. """

        # In the IDLE state, cache waits for CPU to send a new request.
        # Until there is a new request from the cache, stall is low.
        # When there is a new request from the cache stall is asserted, request
        # is decoded and corresponding tag, data, and use array lines are read
        # from internal SRAMs.
        with m.Case(state.IDLE):
            # Read next lines from SRAMs even though CPU is not sending a new
            # request since read is non-destructive.
            c.tag_array.read(c.addr.parse_set())
            c.data_array.read(c.addr.parse_set())


    def add_compare(self, c, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, cache compares tags.
        with m.Case(state.COMPARE):
            c.tag_array.read(c.set)
            c.data_array.read(c.set)
            # Execute the lines below only if DRAM is available
            with m.If(~c.dram.stall()):
                for is_dirty, i in c.hit_detector.find_miss():
                    # Assuming that current request is miss, check if it is dirty miss
                    if is_dirty:
                        # If DRAM is available, switch to WAIT_WRITE and wait for DRAM to
                        # complete writing.
                        c.dram.write(Cat(c.set, c.tag_array.output().tag(i)), c.data_array.output(i))
                    # Else, assume that current request is clean miss
                    else:
                        # If DRAM is busy, switch to READ and wait for DRAM to be available
                        # If DRAM is available, switch to WAIT_READ and wait for DRAM to
                        # complete reading
                        c.dram.read(Cat(c.set, c.tag))
                # Check if there is an empty way. All empty ways need to be filled
                # before evicting a random way.
                # NOTE: The line below should only work for some replacement policies where
                # the lines above may miss an empty way (such as random replacement).
                for i in c.hit_detector.find_empty():
                    # If DRAM is busy, switch to READ and wait for DRAM to be available
                    # If DRAM is available, switch to WAIT_READ and wait for DRAM to
                    # complete reading
                    c.dram.read(Cat(c.set, c.tag))
            # Check if current request is hit
            # Compare all ways' tags to find a hit. Since each way has a different
            # tag, only one of them can match at most.
            # NOTE: This for loop should not be merged with the one above since hit
            # should be checked after all miss assumptions are done.
            for i in c.hit_detector.find_hit():
                # Disable DRAM since a request could have been sent above
                c.dram.disable()
                # Perform the write request if data cache
                if not OPTS.read_only:
                    with m.If(~c.web_reg):
                        # Update dirty bit
                        if c.has_dirty:
                            c.tag_array.write(c.set, Cat(c.tag, C(3, 2)), i)
                        # Perform write request
                        c.data_array.write(c.set, c.data_array.output(i), i)
                        c.data_array.write_input(i, c.offset if c.offset_size else None, c.din_reg, c.wmask_reg if c.num_masks else None)
                        # If write policy is write-through, write to the DRAM
                        if OPTS.write_policy == wp.WRITE_THROUGH:
                            c.dram.write(Cat(c.set, c.tag), c.data_array.output(i))
                            c.dram.write_input(c.offset if c.offset_size else None, c.din_reg, c.wmask_reg if c.num_masks else None)
                # If write policy is write-through, read next lines if current request
                # is read or DRAM is available.
                if OPTS.write_policy == wp.WRITE_THROUGH:
                    with m.If(c.web_reg | ~c.dram.stall()):
                        # Read next lines from SRAMs even though the CPU is not sending
                        # a new request since read is non-destructive.
                        c.tag_array.read(c.addr.parse_set())
                        c.data_array.read(c.addr.parse_set())
                else:
                    # Read next lines from SRAMs even though the CPU is not sending
                    # a new request since read is non-destructive.
                    c.tag_array.read(c.addr.parse_set())
                    c.data_array.read(c.addr.parse_set())


    def add_write(self, c, m):
        """ Add statements for the WRITE state. """

        # In the WRITE state, cache waits for DRAM to be available.
        # When DRAM is available, write request is sent.
        with m.Case(state.WRITE):
            c.tag_array.read(c.set)
            c.data_array.read(c.set)
            # If DRAM is busy, wait in this state.
            # If DRAM is available, switch to WAIT_WRITE and wait for DRAM to
            # complete writing.
            with m.If(~c.dram.stall()):
                with m.Switch(c.way):
                    for i in range(c.num_ways):
                        with m.Case(i):
                            c.dram.write(Cat(c.set, c.tag_array.output().tag(c.way)), c.data_array.output(i))
                # If write policy is write-through, write to the DRAM
                if OPTS.write_policy == wp.WRITE_THROUGH:
                    c.dram.write_input(c.offset if c.offset_size else None, c.din_reg, c.wmask_reg if c.num_masks else None)
                    # Read next lines from SRAMs even though the CPU is not sending
                    # a new request since read is non-destructive.
                    c.tag_array.read(c.addr.parse_set())
                    c.data_array.read(c.addr.parse_set())


    def add_wait_write(self, c, m):
        """ Add statements for the WAIT_WRITE state. """

        # In the WAIT_WRITE state, cache waits for DRAM to complete writing.
        # When DRAM completes writing, read request is sent.
        with m.Case(state.WAIT_WRITE):
            c.tag_array.read(c.set)
            c.data_array.read(c.set)
            # If DRAM is busy, wait in this state.
            # If DRAM completes writing, switch to WAIT_READ and wait for DRAM to
            # complete reading.
            with m.If(~c.dram.stall()):
                c.dram.read(Cat(c.set, c.tag))


    def add_read(self, c, m):
        """ Add statements for the READ state. """

        # In the READ state, cache waits for DRAM to be available.
        # When DRAM is available, read request is sent.
        # TODO: Is this state really necessary? WAIT_WRITE state may be used instead
        with m.Case(state.READ):
            c.tag_array.read(c.set)
            c.data_array.read(c.set)
            # If DRAM is busy, wait in this state.
            # If DRAM completes writing, switch to WAIT_READ and wait for DRAM to
            # complete reading.
            with m.If(~c.dram.stall()):
                c.dram.read(Cat(c.set, c.tag))


    def add_wait_read(self, c, m):
        """ Add statements for the WAIT_READ state. """

        # In the WAIT_READ state, cache waits for DRAM to complete reading
        # When DRAM completes reading, request is completed.
        with m.Case(state.WAIT_READ):
            c.tag_array.read(c.set)
            c.data_array.read(c.set)
            # If DRAM is busy, cache waits in this state.
            # If DRAM completes reading, cache switches to:
            #   IDLE    if CPU isn't sending a new request
            #   COMPARE if CPU is sending a new request
            with m.If(~c.dram.stall()):
                # Update tag line
                if c.has_dirty:
                    c.tag_array.write(c.set, Cat(c.tag, ~c.web_reg, C(1, 1)), c.way)
                else:
                    c.tag_array.write(c.set, Cat(c.tag, C(1, 1)), c.way)
                # Update data line
                c.data_array.write(c.set, c.dram.output(), c.way)
                # Perform the write request if data cache
                if not OPTS.read_only:
                    with m.If(~c.web_reg):
                        c.data_array.write_input(c.way, c.offset if c.offset_size else None, c.din_reg, c.wmask_reg if c.num_masks else None)
                        # If write policy is write-through, write to the DRAM
                        if OPTS.write_policy == wp.WRITE_THROUGH:
                            c.dram.write(Cat(c.set, c.tag), c.dram.output())
                            c.dram.write_input(c.offset if c.offset_size else None, c.din_reg, c.wmask_reg if c.num_masks else None)
                # Read next lines from SRAMs even though the CPU is not sending
                # a new request since read is non-destructive.
                c.tag_array.read(c.addr.parse_set())
                c.data_array.read(c.addr.parse_set())


    def add_flush_hazard(self, c, m):
        """ Add statements for the FLUSH_HAZARD state. """

        # In the FLUSH_HAZARD state, cache waits in this state for 1 cycle.
        # Read requests are sent to tag and data arrays.
        with m.Case(state.FLUSH_HAZARD):
            c.tag_array.read(0)
            c.data_array.read(0)


    def add_wait_hazard(self, c, m):
        """ Add statements for the WAIT_HAZARD state. """

        # In the WAIT_HAZARD state, cache waits in this state for 1 cycle.
        # Read requests are sent to tag and data arrays.
        with m.Case(state.WAIT_HAZARD):
            c.tag_array.read(c.set)
            c.data_array.read(c.set)


    def add_flush_sig(self, c, m):
        """ Add flush signal control. """

        # If flush is high, state switches to FLUSH.
        # In the FLUSH state, cache will write all data lines back to DRAM.
        with m.If(c.flush):
            c.tag_array.read(0)
            c.data_array.read(0)