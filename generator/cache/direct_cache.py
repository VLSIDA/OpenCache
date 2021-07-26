# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from cache_base import cache_base
from nmigen import *
from nmigen.utils import log2_int
from rtl import State


class direct_cache(cache_base):
    """
    This is the design module of direct-mapped cache.
    """

    def __init__(self, cache_config, name):

        super().__init__(cache_config, name)


    def add_memory_controller_block(self, m):
        """ Add memory controller always block to cache design. """

        with m.If(self.rst):
            m.d.comb += self.tag_write_csb.eq(0)
            m.d.comb += self.tag_write_addr.eq(0)
            m.d.comb += self.tag_write_din.eq(0)

        with m.Elif(self.flush):
            m.d.comb += self.tag_read_csb.eq(0)
            m.d.comb += self.tag_read_addr.eq(0)
            m.d.comb += self.data_read_csb.eq(0)
            m.d.comb += self.data_read_addr.eq(0)

        with m.Else():
            with m.Switch(self.state):
                ########## RESET ##########
                with m.Case(State.RESET):
                    m.d.comb += self.tag_write_csb.eq(0)
                    m.d.comb += self.tag_write_addr.eq(self.set)
                    m.d.comb += self.tag_write_din.eq(0)

                ########## FLUSH ##########
                with m.Case(State.FLUSH):
                    m.d.comb += self.tag_read_csb.eq(0)
                    m.d.comb += self.tag_read_addr.eq(self.set)
                    m.d.comb += self.data_read_csb.eq(0)
                    m.d.comb += self.data_read_addr.eq(self.set)
                    m.d.comb += self.main_csb.eq(0)
                    m.d.comb += self.main_web.eq(0)
                    m.d.comb += self.main_addr.eq(Cat(self.set, self.tag_read_dout[:self.tag_size+1]))
                    m.d.comb += self.main_din.eq(self.data_read_dout)
                    with m.If(~self.main_stall):
                        m.d.comb += self.tag_read_addr.eq(self.set + 1)
                        m.d.comb += self.data_read_addr.eq(self.set + 1)

                ########## IDLE ##########
                with m.Case(State.IDLE):
                    with m.If(~self.csb):
                        m.d.comb += self.tag_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))
                        m.d.comb += self.data_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))
                        # FIXME: Don't write 0 in testbench (might result in missed errors).
                        m.d.comb += self.data_write_din.eq(0)

                ########## COMPARE ##########
                with m.Case(State.COMPARE):
                    with m.If(
                        (self.bypass & self.new_tag[-1] & (self.new_tag[:self.tag_size] == self.tag)) | 
                        (~self.bypass & self.tag_read_dout[-1] & (self.tag_read_dout[:self.tag_size] == self.tag))
                    ):
                        with m.If(~self.web_reg):
                            m.d.comb += self.tag_write_csb.eq(0)
                            m.d.comb += self.tag_write_addr.eq(self.set)
                            m.d.comb += self.tag_write_din.eq(Cat(self.tag, Const(3, 2)))
                            m.d.comb += self.data_write_csb.eq(0)
                            m.d.comb += self.data_write_addr.eq(self.set)
                            m.d.comb += self.data_write_din.eq(Mux(self.bypass, self.new_data, self.data_read_dout))
                            num_bytes = Const(self.num_bytes, log2_int(self.words_per_line, self.num_bytes))
                            for i in range(self.num_bytes):
                                with m.If(self.wmask_reg[i]):
                                    m.d.comb += self.data_write_din.word_select(self.offset * num_bytes + i, 8).eq(self.din_reg.word_select(i, 8))
                        with m.If(~self.csb):
                            m.d.comb += self.tag_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))
                            m.d.comb += self.data_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))
                    with m.Elif(self.tag_read_dout[-2:] == Const(3, 2)):
                        with m.If(self.main_stall):
                            m.d.comb += self.tag_read_addr.eq(self.set)
                            m.d.comb += self.data_read_addr.eq(self.set)
                        with m.Else():
                            m.d.comb += self.main_csb.eq(0)
                            m.d.comb += self.main_web.eq(0)
                            with m.If(self.bypass):
                                m.d.comb += self.main_addr.eq(Cat(self.set, self.new_tag[:self.tag_size+1]))
                                m.d.comb += self.main_din.eq(self.new_data)
                            with m.Else():
                                m.d.comb += self.main_addr.eq(Cat(self.set, self.tag_read_dout[:self.tag_size+1]))
                                m.d.comb += self.main_din.eq(self.data_read_dout)
                    with m.Else():
                        with m.If(~self.main_stall):
                            m.d.comb += self.main_csb.eq(0)
                            m.d.comb += self.main_addr.eq(Cat(self.set, self.tag))

                ########## WRITE ##########
                with m.Case(State.WRITE):
                    m.d.comb += self.tag_read_addr.eq(self.set)
                    m.d.comb += self.data_read_addr.eq(self.set)
                    with m.If(~self.main_stall):
                        m.d.comb += self.main_csb.eq(0)
                        m.d.comb += self.main_web.eq(0)
                        m.d.comb += self.main_addr.eq(Cat(self.set, self.tag_read_dout[:self.tag_size+1]))
                        m.d.comb += self.main_din.eq(self.data_read_dout)

                ########## WAIT_WRITE ##########
                with m.Case(State.WAIT_WRITE):
                    with m.If(~self.main_stall):
                        m.d.comb += self.main_csb.eq(0)
                        m.d.comb += self.main_addr.eq(Cat(self.set, self.tag))

                ########## READ ##########
                with m.Case(State.READ):
                    with m.If(~self.main_stall):
                        m.d.comb += self.main_csb.eq(0)
                        m.d.comb += self.main_addr.eq(Cat(self.set, self.tag))

                ########## WAIT_READ ##########
                with m.Case(State.WAIT_READ):
                    with m.If(~self.main_stall):
                        m.d.comb += self.tag_write_csb.eq(0)
                        m.d.comb += self.tag_write_addr.eq(self.set)
                        m.d.comb += self.tag_write_din.eq(Cat(self.tag, ~self.web_reg, Const(1, 1)))
                        m.d.comb += self.data_write_csb.eq(0)
                        m.d.comb += self.data_write_addr.eq(self.set)
                        m.d.comb += self.data_write_din.eq(self.main_dout)
                        with m.If(~self.web_reg):
                            num_bytes = Const(self.num_bytes, log2_int(self.words_per_line, self.num_bytes))
                            for i in range(self.num_bytes):
                                with m.If(self.wmask_reg[i]):
                                    m.d.comb += self.data_write_din.word_select(self.offset * num_bytes + i, 8).eq(self.din_reg.word_select(i, 8))
                        with m.If(~self.csb):
                            m.d.comb += self.tag_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))
                            m.d.comb += self.data_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))


    def add_state_block(self, m):
        """ Add state controller always block to cache design. """

        m.d.comb += self.state_next.eq(self.state)

        with m.If(self.rst):
            m.d.comb += self.state_next.eq(State.RESET)

        with m.Elif(self.flush):
            m.d.comb += self.state_next.eq(State.FLUSH)

        with m.Else():
            with m.Switch(self.state):
                with m.Case(State.RESET):
                    with m.If(self.set == self.num_rows - 1):
                        m.d.comb += self.state_next.eq(State.IDLE)

                with m.Case(State.FLUSH):
                    with m.If(~self.main_stall & (self.set == self.num_rows - 1)):
                        m.d.comb += self.state_next.eq(State.IDLE)

                with m.Case(State.IDLE):
                    with m.If(~self.csb):
                        m.d.comb += self.state_next.eq(State.COMPARE)

                with m.Case(State.COMPARE):
                    with m.If(
                        (self.bypass & self.new_tag[-1] & (self.new_tag[:self.tag_size] == self.tag)) | 
                        (~self.bypass & self.tag_read_dout[-1] & (self.tag_read_dout[:self.tag_size] == self.tag))
                    ):
                        with m.If(self.csb):
                            m.d.comb += self.state_next.eq(State.IDLE)
                        with m.Else():
                            m.d.comb += self.state_next.eq(State.COMPARE)
                    with m.Elif(self.tag_read_dout[-2:] == Const(3, 2)):
                        with m.If(self.csb):
                            m.d.comb += self.state_next.eq(State.WRITE)
                        with m.Else():
                            m.d.comb += self.state_next.eq(State.WAIT_WRITE)
                    with m.Else():
                        with m.If(self.csb):
                            m.d.comb += self.state_next.eq(State.READ)
                        with m.Else():
                            m.d.comb += self.state_next.eq(State.WAIT_READ)

                with m.Case(State.WRITE):
                    with m.If(~self.main_stall):
                        m.d.comb += self.state_next.eq(State.WAIT_WRITE)

                with m.Case(State.WAIT_WRITE):
                    with m.If(~self.main_stall):
                        m.d.comb += self.state_next.eq(State.WAIT_READ)

                with m.Case(State.READ):
                    with m.If(~self.main_stall):
                        m.d.comb += self.state_next.eq(State.WAIT_READ)

                with m.Case(State.WAIT_READ):
                    with m.If(~self.main_stall):
                        with m.If(self.csb):
                            m.d.comb += self.state_next.eq(State.IDLE)
                        with m.Else():
                            m.d.comb += self.state_next.eq(State.COMPARE)


    def add_request_block(self, m):
        """ Add request decode always block to cache design. """

        m.d.comb += self.tag_next.eq(self.tag)
        m.d.comb += self.set_next.eq(self.set)
        m.d.comb += self.offset_next.eq(self.offset)
        m.d.comb += self.web_reg_next.eq(self.web_reg)
        m.d.comb += self.wmask_reg_next.eq(self.wmask_reg)
        m.d.comb += self.din_reg_next.eq(self.din_reg)

        with m.If(self.rst):
            m.d.comb += self.tag_next.eq(0)
            m.d.comb += self.set_next.eq(1)
            m.d.comb += self.offset_next.eq(0)
            m.d.comb += self.web_reg_next.eq(1)
            m.d.comb += self.wmask_reg_next.eq(0)
            m.d.comb += self.din_reg_next.eq(0)

        with m.Elif(self.flush):
            m.d.comb += self.set_next.eq(0)

        with m.Else():
            with m.Switch(self.state):
                with m.Case(State.RESET):
                    m.d.comb += self.set_next.eq(self.set + 1)

                with m.Case(State.FLUSH):
                    with m.If(~self.main_stall):
                        m.d.comb += self.set_next.eq(self.set + 1)

                with m.Case(State.IDLE):
                    m.d.comb += self.tag_next.eq(self.addr[-self.tag_size:])
                    m.d.comb += self.set_next.eq(self.addr.bit_select(self.offset_size, self.set_size))
                    m.d.comb += self.offset_next.eq(self.addr[:self.offset_size+1])
                    m.d.comb += self.web_reg_next.eq(self.web)
                    m.d.comb += self.wmask_reg_next.eq(self.wmask)
                    m.d.comb += self.din_reg_next.eq(self.din)

                with m.Case(State.COMPARE):
                    with m.If(
                        (self.bypass & self.new_tag[-1] & (self.new_tag[:self.tag_size] == self.tag)) | 
                        (~self.bypass & self.tag_read_dout[-1] & (self.tag_read_dout[:self.tag_size] == self.tag))
                    ):
                        m.d.comb += self.tag_next.eq(self.addr[-self.tag_size:])
                        m.d.comb += self.set_next.eq(self.addr.bit_select(self.offset_size, self.set_size))
                        m.d.comb += self.offset_next.eq(self.addr[:self.offset_size+1])
                        m.d.comb += self.web_reg_next.eq(self.web)
                        m.d.comb += self.wmask_reg_next.eq(self.wmask)
                        m.d.comb += self.din_reg_next.eq(self.din)

                with m.Case(State.WAIT_READ):
                    with m.If(~self.main_stall):
                        m.d.comb += self.tag_next.eq(self.addr[-self.tag_size:])
                        m.d.comb += self.set_next.eq(self.addr.bit_select(self.offset_size, self.set_size))
                        m.d.comb += self.offset_next.eq(self.addr[:self.offset_size+1])
                        m.d.comb += self.web_reg_next.eq(self.web)
                        m.d.comb += self.wmask_reg_next.eq(self.wmask)
                        m.d.comb += self.din_reg_next.eq(self.din)


    def add_output_block(self, m):
        """ Add the output always block to cache design. """

        m.d.comb += self.stall.eq(1)
        # FIXME: Don't write 0 in testbench (might result in missed errors).
        m.d.comb += self.dout.eq(0)

        with m.Switch(self.state):
            with m.Case(State.IDLE):
                m.d.comb += self.stall.eq(0)

            with m.Case(State.COMPARE):
                with m.If(
                    (self.bypass & self.new_tag[-1] & (self.new_tag[:self.tag_size] == self.tag)) | 
                    (~self.bypass & self.tag_read_dout[-1] & (self.tag_read_dout[:self.tag_size] == self.tag))
                ):
                    m.d.comb += self.stall.eq(0)
                    with m.If(self.bypass):
                        m.d.comb += self.dout.eq(self.new_data.word_select(self.offset, self.word_size))
                    with m.Else():
                        m.d.comb += self.dout.eq(self.data_read_dout.word_select(self.offset, self.word_size))

            with m.Case(State.WAIT_READ):
                with m.If(~self.main_stall):
                    m.d.comb += self.stall.eq(0)
                    m.d.comb += self.dout.eq(self.main_dout.word_select(self.offset, self.word_size))


    def add_bypass_block(self, m):
        """ Add the bypass register always block to cache design. """

        m.d.comb += self.bypass_next.eq(0)
        m.d.comb += self.new_tag_next.eq(0)
        m.d.comb += self.new_data_next.eq(0)

        with m.Switch(self.state):
            with m.Case(State.COMPARE):
                with m.If(
                    ~self.csb &
                    ~self.web_reg &
                    (self.set == self.addr.bit_select(self.offset_size, self.set_size)) &
                    ((self.bypass & self.new_tag[-1] & (self.new_tag[:self.tag_size] == self.tag)) | (~self.bypass & self.tag_read_dout[-1] & (self.tag_read_dout[:self.tag_size] == self.tag)))
                ):
                    m.d.comb += self.bypass_next.eq(1)
                    m.d.comb += self.new_tag_next.eq(Cat(self.tag, Const(3, 2)))
                    with m.If(self.bypass):
                        m.d.comb += self.new_data_next.eq(self.new_data)
                    with m.Else():
                        m.d.comb += self.new_data_next.eq(self.data_read_dout)
                    num_bytes = Const(self.num_bytes, log2_int(self.words_per_line, self.num_bytes))
                    for i in range(self.num_bytes):
                        with m.If(self.wmask_reg[i]):
                            m.d.comb += self.new_data_next.word_select(self.offset * num_bytes + i, 8).eq(self.din_reg.word_select(i, 8))

            with m.Case(State.WAIT_READ):
                with m.If(~self.main_stall & ~self.csb & (self.set == self.addr.bit_select(self.offset_size, self.set_size))):
                    m.d.comb += self.bypass_next.eq(1)
                    m.d.comb += self.new_tag_next.eq(Cat(self.tag, ~self.web_reg, Const(1, 1)))
                    m.d.comb += self.new_data_next.eq(self.main_dout)
                    with m.If(~self.web_reg):
                        num_bytes = Const(self.num_bytes, log2_int(self.words_per_line, self.num_bytes))
                        for i in range(self.num_bytes):
                            with m.If(self.wmask_reg[i]):
                                m.d.comb += self.new_data_next.word_select(self.offset * num_bytes + i, 8).eq(self.din_reg.word_select(i, 8))