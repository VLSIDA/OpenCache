# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from memory_block_base import memory_block_base
from amaranth import Cat, Const, C
from state import state


class memory_block_lru(memory_block_base):
    """
    This class extends base memory controller module for LRU replacement
    policy.
    """

    def __init__(self):

        super().__init__()


    def add_compare(self, dsgn, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, cache compares tags.
        # Stall and dout are driven by the Output Block.
        with m.Case(state.COMPARE):
            dsgn.tag_array.read(dsgn.set)
            dsgn.data_array.read(dsgn.set)
            for i in range(dsgn.num_ways):
                # Find the least recently used way (the way having 0 use number)
                with m.If(dsgn.use_array.output().use(i) == Const(0, dsgn.way_size)):
                    # Assuming that current request is miss, check if it is dirty miss
                    with dsgn.check_dirty_miss(m, i):
                        # If DRAM is available, switch to WAIT_WRITE and wait for DRAM to
                        # complete writing.
                        with m.If(~dsgn.dram.stall()):
                            dsgn.dram.write(Cat(dsgn.set, dsgn.tag_array.output().tag(i)), dsgn.data_array.output(i))
                    # Else, assume that current request is clean miss
                    with dsgn.check_clean_miss(m):
                        # If DRAM is busy, switch to READ and wait for DRAM to be available
                        # If DRAM is available, switch to WAIT_READ and wait for DRAM to
                        # complete reading
                        with m.If(~dsgn.dram.stall()):
                            dsgn.dram.read(Cat(dsgn.set, dsgn.tag))
            # Check if current request is hit
            # Compare all ways' tags to find a hit. Since each way has a different
            # tag, only one of them can match at most.
            # NOTE: This for loop should not be merged with the one above since hit
            # should be checked after all miss assumptions are done.
            for i in range(dsgn.num_ways):
                with dsgn.check_hit(m, i):
                    # Disable DRAM since a request could be sent above
                    dsgn.dram.disable()
                    # Perform the write request
                    with m.If(~dsgn.web_reg):
                        # Update dirty bit
                        dsgn.tag_array.write(dsgn.set, Cat(dsgn.tag_array.output().tag(i), C(3, 2)), i)
                        # Perform write request
                        dsgn.data_array.write(dsgn.set, dsgn.data_array.output(i), i)
                        dsgn.data_array.write_input(i, dsgn.offset, dsgn.din_reg, dsgn.wmask_reg if dsgn.num_masks else None)
                    # Read next lines from SRAMs even though CPU is not
                    # sending a new request since read is non-destructive.
                    dsgn.tag_array.read(dsgn.addr.parse_set())
                    dsgn.data_array.read(dsgn.addr.parse_set())