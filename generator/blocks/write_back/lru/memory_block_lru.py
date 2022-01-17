# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from memory_block_base import memory_block_base
from amaranth import Cat, C
from state import state


class memory_block_lru(memory_block_base):
    """
    This class extends base memory controller module for LRU replacement
    policy.
    """

    def __init__(self):

        super().__init__()


    def add_compare(self, c, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, cache compares tags.
        # Stall and dout are driven by the Output Block.
        with m.Case(state.COMPARE):
            c.tag_array.read(c.set)
            c.data_array.read(c.set)
            for is_dirty, i in c.hit_detector.find_miss():
                # Assuming that current request is miss, check if it is dirty miss
                if is_dirty:
                    # If DRAM is available, switch to WAIT_WRITE and wait for DRAM to
                    # complete writing.
                    with m.If(~c.dram.stall()):
                        c.dram.write(Cat(c.set, c.tag_array.output().tag(i)), c.data_array.output(i))
                # Else, assume that current request is clean miss
                else:
                    # If DRAM is busy, switch to READ and wait for DRAM to be available
                    # If DRAM is available, switch to WAIT_READ and wait for DRAM to
                    # complete reading
                    with m.If(~c.dram.stall()):
                        c.dram.read(Cat(c.set, c.tag))
            # Check if current request is hit
            # Compare all ways' tags to find a hit. Since each way has a different
            # tag, only one of them can match at most.
            # NOTE: This for loop should not be merged with the one above since hit
            # should be checked after all miss assumptions are done.
            for i in c.hit_detector.find_hit():
                # Disable DRAM since a request could be sent above
                c.dram.disable()
                # Perform the write request
                with m.If(~c.web_reg):
                    # Update dirty bit
                    c.tag_array.write(c.set, Cat(c.tag_array.output().tag(i), C(3, 2)), i)
                    # Perform write request
                    c.data_array.write(c.set, c.data_array.output(i), i)
                    c.data_array.write_input(i, c.offset, c.din_reg, c.wmask_reg if c.num_masks else None)
                # Read next lines from SRAMs even though CPU is not
                # sending a new request since read is non-destructive.
                c.tag_array.read(c.addr.parse_set())
                c.data_array.read(c.addr.parse_set())