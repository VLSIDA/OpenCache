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


class memory_block_fifo(memory_block_base):
    """
    This class extends base memory controller module for FIFO replacement
    policy.
    """

    def __init__(self):

        super().__init__()


    def add_compare(self, dsgn, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, cache compares tags.
        # Stall and output are driven by the Output Block.
        with m.Case(State.COMPARE):
            m.d.comb += dsgn.tag_read_addr.eq(dsgn.set)
            m.d.comb += dsgn.data_read_addr.eq(dsgn.set)
            # Assuming that current request is miss, check if it is dirty miss
            with dsgn.check_dirty_miss(m, dsgn.use_read_dout):
                # If DRAM is available, switch to WAIT_WRITE and wait for DRAM to
                # complete writing
                with m.If(~dsgn.main_stall):
                    m.d.comb += dsgn.main_csb.eq(0)
                    m.d.comb += dsgn.main_web.eq(0)
                    m.d.comb += dsgn.main_addr.eq(Cat(dsgn.set, dsgn.tag_read_dout.tag(dsgn.use_read_dout)))
                    m.d.comb += dsgn.main_din.eq(dsgn.data_read_dout.line(dsgn.use_read_dout))
            # Else, assume that current request is clean miss
            with dsgn.check_clean_miss(m):
                with m.If(~dsgn.main_stall):
                    m.d.comb += dsgn.main_csb.eq(0)
                    m.d.comb += dsgn.main_addr.eq(Cat(dsgn.set, dsgn.tag))
            # Check if current request is hit
            # Compare all ways' tags to find a hit. Since each way has a different
            # tag, only one of them can match at most.
            for i in range(dsgn.num_ways):
                with dsgn.check_hit(m, i):
                    # Set DRAM's csb to 1 again since it could be set 0 above
                    m.d.comb += dsgn.main_csb.eq(1)
                    # Perform the write request
                    with m.If(~dsgn.web_reg):
                        # Update dirty bit in the tag line
                        m.d.comb += dsgn.tag_write_csb.eq(0)
                        m.d.comb += dsgn.tag_write_addr.eq(dsgn.set)
                        m.d.comb += dsgn.tag_write_din.eq(dsgn.tag_read_dout)
                        m.d.comb += dsgn.tag_write_din.dirty(i).eq(1)
                        # Write the word over the write mask
                        # NOTE: This switch statement is written manually (not only with
                        # word_select) because word_select fails to generate correct case
                        # statements if offset calculation is a bit complex.
                        m.d.comb += dsgn.data_write_csb.eq(0)
                        m.d.comb += dsgn.data_write_addr.eq(dsgn.set)
                        m.d.comb += dsgn.data_write_din.eq(dsgn.data_read_dout)
                        for j in range(dsgn.num_bytes):
                            with m.If(dsgn.wmask_reg[j]):
                                with m.Switch(dsgn.offset):
                                    for k in range(dsgn.words_per_line):
                                        with m.Case(k):
                                            m.d.comb += dsgn.data_write_din.byte(j, k, i).eq(dsgn.din_reg.byte(j))
                    # Read next lines from SRAMs even though CPU is not
                    # sending a new request since read is non-destructive.
                    m.d.comb += dsgn.tag_read_addr.eq(dsgn.addr.parse_set())
                    m.d.comb += dsgn.data_read_addr.eq(dsgn.addr.parse_set())