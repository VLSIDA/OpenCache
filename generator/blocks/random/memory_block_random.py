# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from memory_block_base import memory_block_base
from nmigen import Cat
from state import State


class memory_block_random(memory_block_base):
    """
    This class extends base memory controller module for random replacement
    policy.
    """

    def __init__(self):

        super().__init__()


    def add_compare(self, dsgn, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, cache compares tags.
        # Stall and dout are driven by the Output Block.
        with m.Case(State.COMPARE):
            dsgn.tag_array.read(dsgn.set)
            dsgn.data_array.read(dsgn.set)
            # Assuming that current request is miss, check if it is dirty miss
            with dsgn.check_dirty_miss(m, dsgn.random):
                # If DRAM is available, switch to WAIT_WRITE and wait for DRAM to
                # complete writing
                with m.If(~dsgn.dram.stall()):
                    dsgn.dram.write(Cat(dsgn.set, dsgn.tag_array.output().tag(dsgn.random)), dsgn.data_array.output().line(dsgn.random))
            # Else, assume that current request is clean miss
            with dsgn.check_clean_miss(m):
                with m.If(~dsgn.dram.stall()):
                    dsgn.dram.read(Cat(dsgn.set, dsgn.tag))
            # Check if there is an empty way. All empty ways need to be filled
            # before evicting a random way.
            for i in range(dsgn.num_ways):
                with m.If(~dsgn.tag_array.output().valid(i)):
                    with m.If(~dsgn.dram.stall()):
                        dsgn.dram.read(Cat(dsgn.set, dsgn.tag))
            # Check if current request is hit
            # Compare all ways' tags to find a hit. Since each way has a different
            # tag, only one of them can match at most.
            for i in range(dsgn.num_ways):
                with dsgn.check_hit(m, i):
                    # Set DRAM's csb to 1 again since it could be set 0 above
                    dsgn.dram.disable()
                    # Perform the write request
                    with m.If(~dsgn.web_reg):
                        dsgn.tag_array.write(dsgn.set, Cat(dsgn.tag_array.output().tag(i), 0b11), i)
                        dsgn.data_array.write(dsgn.set, dsgn.data_array.output())
                        dsgn.data_array.write_bytes(dsgn.wmask_reg, i, dsgn.offset, dsgn.din_reg)
                    # Read next lines from SRAMs even though CPU is not
                    # sending a new request since read is non-destructive.
                    dsgn.tag_array.read(dsgn.addr.parse_set())
                    dsgn.data_array.read(dsgn.addr.parse_set())