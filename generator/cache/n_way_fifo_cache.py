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
from rtl import get_ff_signals, State
from globals import OPTS


class n_way_fifo_cache(cache_base):
    """
    This is the design module of N-way set associative cache
    with FIFO replacement policy.
    """

    def __init__(self, cache_config, name):

        super().__init__(cache_config, name)


    def add_internal_signals(self):
        """ Add internal registers and wires to cache design. """

        super().add_internal_signals()

        # Keep way chosen to be evicted in an FF
        self.way, self.way_next = get_ff_signals("way", self.way_size)

        # Bypass FF for use array
        if self.data_hazard:
            self.new_use, self.new_use_next = get_ff_signals("new_use", self.way_size)


    def add_srams(self, m):
        """ Addhe internal SRAM array instances to cache design. """

        super().add_srams(m)

        # Use array
        word_size = self.way_size
        self.use_write_csb  = Signal(reset_less=True, reset=1)
        self.use_write_addr = Signal(self.set_size, reset_less=True)
        self.use_write_din  = Signal(word_size, reset_less=True)
        self.use_read_csb   = Signal(reset_less=True)
        self.use_read_addr  = Signal(self.set_size, reset_less=True)
        self.use_read_dout  = Signal(word_size)
        m.submodules += Instance(OPTS.use_array_name,
            ("i", "clk0",  self.clk),
            ("i", "csb0",  self.use_write_csb),
            ("i", "addr0", self.use_write_addr),
            ("i", "din0",  self.use_write_din),
            ("i", "clk1",  self.clk),
            ("i", "csb1",  self.use_read_csb),
            ("i", "addr1", self.use_read_addr),
            ("o", "dout1", self.use_read_dout),
        )


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

                with m.Case(State.RESET):
                    m.d.comb += self.tag_write_csb.eq(0)
                    m.d.comb += self.tag_write_addr.eq(self.set)
                    m.d.comb += self.tag_write_din.eq(0)

                with m.Case(State.FLUSH):
                    m.d.comb += self.tag_read_csb.eq(0)
                    m.d.comb += self.tag_read_addr.eq(self.set)
                    m.d.comb += self.data_read_csb.eq(0)
                    m.d.comb += self.data_read_addr.eq(self.set)
                    m.d.comb += self.main_csb.eq(0)
                    m.d.comb += self.main_web.eq(0)
                    m.d.comb += self.main_addr.eq(Cat(self.set, self.tag_read_dout.bit_select(self.way * (self.tag_size + 2), self.tag_size)))
                    m.d.comb += self.main_din.eq(self.data_read_dout.word_select(self.way, self.line_size))
                    with m.If(~self.main_stall & (self.way == self.num_ways - 1)):
                        m.d.comb += self.tag_read_addr.eq(self.set + 1)
                        m.d.comb += self.data_read_addr.eq(self.set + 1)

                with m.Case(State.IDLE):
                    with m.If(~self.csb):
                        m.d.comb += self.tag_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))
                        m.d.comb += self.data_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))
                        # FIXME: Don't write 0 in testbench (might result in missed errors).
                        m.d.comb += self.data_write_din.eq(0)

                with m.Case(State.COMPARE):
                    with m.If(
                        (self.bypass & (self.new_tag.bit_select(self.new_use * (self.tag_size + 2) + self.tag_size, 2) == Const(3, 2))) |
                        (~self.bypass & (self.tag_read_dout.bit_select(self.use_read_dout * (self.tag_size + 2) + self.tag_size, 2) == Const(3, 2)))
                    ):
                        with m.If(self.main_stall):
                            m.d.comb += self.tag_read_addr.eq(self.set)
                            m.d.comb += self.data_read_addr.eq(self.set)
                        with m.Else():
                            m.d.comb += self.main_csb.eq(0)
                            m.d.comb += self.main_web.eq(0)
                            with m.If(self.bypass):
                                m.d.comb += self.main_addr.eq(Cat(self.set, self.new_tag.bit_select(self.new_use * (self.tag_size + 2), self.tag_size)))
                                m.d.comb += self.main_din.eq(self.new_data.word_select(self.new_use, self.line_size))
                            with m.Else():
                                m.d.comb += self.main_addr.eq(Cat(self.set, self.tag_read_dout.bit_select(self.use_read_dout * (self.tag_size + 2), self.tag_size)))
                                m.d.comb += self.main_din.eq(self.data_read_dout.word_select(self.use_read_dout, self.line_size))
                    with m.Else():
                        with m.If(~self.main_stall):
                            m.d.comb += self.tag_read_addr.eq(self.set)
                            m.d.comb += self.data_read_addr.eq(self.set)
                            m.d.comb += self.main_csb.eq(0)
                            m.d.comb += self.main_addr.eq(Cat(self.set, self.tag))
                    for i in range(self.num_ways):
                        with m.If(
                            (self.bypass & self.new_tag[i * (self.tag_size + 2) + self.tag_size + 1] & (self.new_tag.bit_select(i * (self.tag_size + 2), self.tag_size) == self.tag)) |
                            (~self.bypass & self.tag_read_dout[i * (self.tag_size + 2) + self.tag_size + 1] & (self.tag_read_dout.bit_select(i * (self.tag_size + 2), self.tag_size) == self.tag))
                        ):
                            m.d.comb += self.main_csb.eq(1)
                            with m.If(~self.web_reg):
                                m.d.comb += self.tag_write_csb.eq(0)
                                m.d.comb += self.tag_write_addr.eq(self.set)
                                m.d.comb += self.data_write_csb.eq(0)
                                m.d.comb += self.data_write_addr.eq(self.set)
                                with m.If(self.bypass):
                                    m.d.comb += self.tag_write_din.eq(self.new_tag)
                                    m.d.comb += self.data_write_din.eq(self.new_data)
                                with m.Else():
                                    m.d.comb += self.tag_write_din.eq(self.tag_read_dout)
                                    m.d.comb += self.data_write_din.eq(self.data_read_dout)
                                m.d.comb += self.tag_write_din[i * (self.tag_size + 2) + self.tag_size].eq(1)
                                num_bytes_per_word = Const(self.num_bytes, log2_int(self.words_per_line, self.num_bytes))
                                num_bytes_per_line = Const(self.num_bytes * self.words_per_line, log2_int(self.num_ways * self.words_per_line))
                                for j in range(self.num_bytes):
                                    with m.If(self.wmask_reg[j]):
                                        m.d.comb += self.data_write_din.word_select(i * num_bytes_per_line + self.offset * num_bytes_per_word + j, 8).eq(self.din_reg.word_select(j, 8))
                            with m.If(~self.csb):
                                m.d.comb += self.tag_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))
                                m.d.comb += self.data_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))

                with m.Case(State.WRITE):
                    m.d.comb += self.tag_read_addr.eq(self.set)
                    m.d.comb += self.data_read_addr.eq(self.set)
                    with m.If(~self.main_stall):
                        m.d.comb += self.main_csb.eq(0)
                        m.d.comb += self.main_web.eq(0)
                        m.d.comb += self.main_addr.eq(Cat(self.set, self.tag_read_dout.bit_select(self.way * (self.tag_size + 2), self.tag_size)))
                        m.d.comb += self.main_din.eq(self.data_read_dout.word_select(self.way, self.line_size))

                with m.Case(State.WAIT_WRITE):
                    m.d.comb += self.tag_read_addr.eq(self.set)
                    m.d.comb += self.data_read_addr.eq(self.set)
                    with m.If(~self.main_stall):
                        m.d.comb += self.main_csb.eq(0)
                        m.d.comb += self.main_addr.eq(Cat(self.set, self.tag))

                # TODO: Is this state really necessary? WAIT_WRITE state may be used instead.
                with m.Case(State.READ):
                    m.d.comb += self.tag_read_addr.eq(self.set)
                    m.d.comb += self.data_read_addr.eq(self.set)
                    with m.If(~self.main_stall):
                        m.d.comb += self.main_csb.eq(0)
                        m.d.comb += self.main_addr.eq(Cat(self.set, self.tag))

                with m.Case(State.WAIT_READ):
                    m.d.comb += self.tag_read_addr.eq(self.set)
                    m.d.comb += self.data_read_addr.eq(self.set)
                    with m.If(~self.main_stall):
                        # TODO: Use wmask feature of OpenRAM.
                        m.d.comb += self.tag_write_csb.eq(0)
                        m.d.comb += self.tag_write_addr.eq(self.set)
                        m.d.comb += self.tag_write_din.eq(self.tag_read_dout)
                        # TODO: Optimize the below case statement.
                        with m.Switch(self.way):
                            for i in range(self.num_ways):
                                with m.Case(i):
                                    m.d.comb += self.tag_write_din.word_select(i, self.tag_size + 2).eq(Cat(self.tag, ~self.web_reg, Const(1, 1)))
                        m.d.comb += self.data_write_csb.eq(0)
                        m.d.comb += self.data_write_addr.eq(self.set)
                        m.d.comb += self.data_write_din.eq(self.data_read_dout)
                        # TODO: Optimize the below case statement.
                        with m.Switch(self.way):
                            for i in range(self.num_ways):
                                with m.Case(i):
                                    m.d.comb += self.data_write_din.word_select(i, self.line_size).eq(self.main_dout)
                        with m.If(~self.web_reg):
                            num_bytes_per_word = Const(self.num_bytes, log2_int(self.words_per_line, self.num_bytes))
                            num_bytes_per_line = Const(self.num_bytes * self.words_per_line, log2_int(self.num_ways * self.words_per_line))
                            for j in range(self.num_bytes):
                                with m.If(self.wmask_reg[j]):
                                    m.d.comb += self.data_write_din.word_select(self.way * num_bytes_per_line + self.offset * num_bytes_per_word + j, 8).eq(self.din_reg.word_select(j, 8))
                        with m.If(~self.csb):
                            m.d.comb += self.tag_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))
                            m.d.comb += self.data_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))


    def add_state_block(self, m):
        """ Add state controller always block to cache design. """

        m.d.comb += self.state_next.eq(self.state)

        with m.If(self.rst):
            m.d.comb += self.state_next.eq(State.RESET)

        with m.If(self.flush):
            m.d.comb += self.state_next.eq(State.FLUSH)

        with m.Else():
            with m.Switch(self.state):

                with m.Case(State.RESET):
                    with m.If(self.set == self.num_rows - 1):
                        m.d.comb += self.state_next.eq(State.IDLE)

                with m.Case(State.FLUSH):
                    with m.If(~self.main_stall & (self.way == self.num_ways - 1) & (self.set == self.num_rows - 1)):
                        m.d.comb += self.state_next.eq(State.IDLE)

                with m.Case(State.IDLE):
                    with m.If(~self.csb):
                        m.d.comb += self.state_next.eq(State.COMPARE)

                with m.Case(State.COMPARE):
                    with m.If(
                        (self.bypass & (self.new_tag.bit_select(self.new_use * (self.tag_size + 2) + self.tag_size, 2) == Const(3, 2))) |
                        (~self.bypass & (self.tag_read_dout.bit_select(self.use_read_dout * (self.tag_size + 2) + self.tag_size, 2) == Const(3, 2)))
                    ):
                        with m.If(self.main_stall):
                            m.d.comb += self.state_next.eq(State.WRITE)
                        with m.Else():
                            m.d.comb += self.state_next.eq(State.WAIT_WRITE)
                    with m.Else():
                        with m.If(self.main_stall):
                            m.d.comb += self.state_next.eq(State.READ)
                        with m.Else():
                            m.d.comb += self.state_next.eq(State.WAIT_READ)

                    for i in range(self.num_ways):
                        with m.If(
                            (self.bypass & self.new_tag[i * (self.tag_size + 2) + self.tag_size + 1] & (self.new_tag.bit_select(i * (self.tag_size + 2), self.tag_size) == self.tag)) |
                            (~self.bypass & self.tag_read_dout[i * (self.tag_size + 2) + self.tag_size + 1] & (self.tag_read_dout.bit_select(i * (self.tag_size + 2), self.tag_size) == self.tag))
                        ):
                            with m.If(self.csb):
                                m.d.comb += self.state_next.eq(State.IDLE)
                            with m.Else():
                                m.d.comb += self.state_next.eq(State.COMPARE)

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
                    with m.If(~self.main_stall & (self.way == self.num_ways - 1)):
                        m.d.comb += self.set_next.eq(self.set + 1)

                with m.Case(State.IDLE):
                    m.d.comb += self.tag_next.eq(self.addr[-self.tag_size:])
                    m.d.comb += self.set_next.eq(self.addr.bit_select(self.offset_size, self.set_size))
                    m.d.comb += self.offset_next.eq(self.addr[:self.offset_size+1])
                    m.d.comb += self.web_reg_next.eq(self.web)
                    m.d.comb += self.wmask_reg_next.eq(self.wmask)
                    m.d.comb += self.din_reg_next.eq(self.din)

                with m.Case(State.COMPARE):
                    for i in range(self.num_ways):
                        with m.If(
                            (self.bypass & self.new_tag[i * (self.tag_size + 2) + self.tag_size + 1] & (self.new_tag.bit_select(i * (self.tag_size + 2), self.tag_size) == self.tag)) |
                            (~self.bypass & self.tag_read_dout[i * (self.tag_size + 2) + self.tag_size + 1] & (self.tag_read_dout.bit_select(i * (self.tag_size + 2), self.tag_size) == self.tag))
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
        """ Add stall always block to cache design. """

        m.d.comb += self.stall.eq(1)
        # FIXME: Don't write 0 in testbench (might result in missed errors).
        m.d.comb += self.dout.eq(0)

        with m.Switch(self.state):

            with m.Case(State.IDLE):
                m.d.comb += self.stall.eq(0)

            with m.Case(State.COMPARE):
                for i in range(self.num_ways):
                    with m.If(
                        (self.bypass & self.new_tag[i * (self.tag_size + 2) + self.tag_size + 1] & (self.new_tag.bit_select(i * (self.tag_size + 2), self.tag_size) == self.tag)) |
                        (~self.bypass & self.tag_read_dout[i * (self.tag_size + 2) + self.tag_size + 1] & (self.tag_read_dout.bit_select(i * (self.tag_size + 2), self.tag_size) == self.tag))
                    ):
                        m.d.comb += self.stall.eq(0)
                        words_per_line = Const(self.words_per_line)
                        with m.If(self.bypass):
                            m.d.comb += self.dout.eq(self.new_data.word_select(i * words_per_line + self.offset, self.word_size))
                        with m.Else():
                            m.d.comb += self.dout.eq(self.data_read_dout.word_select(i * words_per_line + self.offset, self.word_size))

            with m.Case(State.WAIT_READ):
                with m.If(~self.main_stall):
                    m.d.comb += self.stall.eq(0)
                    m.d.comb += self.dout.eq(self.main_dout.word_select(self.offset, self.word_size))


    def add_replacement_block(self, m):
        """ Add replacement always block to cache design. """

        m.d.comb += self.way_next.eq(self.way)

        with m.If(self.rst):
            m.d.comb += self.way_next.eq(0)
            m.d.comb += self.use_write_csb.eq(0)
            m.d.comb += self.use_write_addr.eq(0)
            m.d.comb += self.use_write_din.eq(0)

        with m.Elif(self.flush):
            m.d.comb += self.way_next.eq(0)

        with m.Else():
            with m.Switch(self.state):

                with m.Case(State.RESET):
                    m.d.comb += self.use_write_csb.eq(0)
                    m.d.comb += self.use_write_addr.eq(self.set)
                    m.d.comb += self.use_write_din.eq(0)

                with m.Case(State.FLUSH):
                    with m.If(~self.main_stall):
                        m.d.comb += self.way_next.eq(self.way + 1)

                with m.Case(State.IDLE):
                    with m.If(~self.csb):
                        m.d.comb += self.way_next.eq(0)
                        m.d.comb += self.use_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))

                with m.Case(State.COMPARE):
                    with m.If(self.bypass):
                        m.d.comb += self.way_next.eq(self.new_use)
                    with m.Else():
                        m.d.comb += self.way_next.eq(self.use_read_dout)
                    with m.If(~self.csb):
                        for i in range(self.num_ways):
                            with m.If(
                                (self.bypass & self.new_tag[i * (self.tag_size + 2) + self.tag_size + 1] & (self.new_tag.bit_select(i * (self.tag_size + 2), self.tag_size) == self.tag)) |
                                (~self.bypass & self.tag_read_dout[i * (self.tag_size + 2) + self.tag_size + 1] & (self.tag_read_dout.bit_select(i * (self.tag_size + 2), self.tag_size) == self.tag))
                            ):
                                m.d.comb += self.use_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))

                with m.Case(State.WAIT_READ):
                    with m.If(~self.main_stall):
                        m.d.comb += self.use_write_csb.eq(0)
                        m.d.comb += self.use_write_addr.eq(self.set)
                        m.d.comb += self.use_write_din.eq(self.way + 1)
                        with m.If(~self.csb):
                            m.d.comb += self.use_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))


    def add_bypass_block(self, m):
        """ Add bypass register always block to cache design. """

        m.d.comb += self.bypass_next.eq(0)
        m.d.comb += self.new_tag_next.eq(0)
        m.d.comb += self.new_data_next.eq(0)
        m.d.comb += self.new_use_next.eq(0)

        with m.Switch(self.state):

            with m.Case(State.COMPARE):
                with m.If(~self.csb & ~self.web_reg & (self.set == self.addr.bit_select(self.offset_size, self.set_size))):
                    for i in range(self.num_ways):
                        with m.If(
                            (self.bypass & self.new_tag[i * (self.tag_size + 2) + self.tag_size + 1] & (self.new_tag.bit_select(i * (self.tag_size + 2), self.tag_size) == self.tag)) |
                            (~self.bypass & self.tag_read_dout[i * (self.tag_size + 2) + self.tag_size + 1] & (self.tag_read_dout.bit_select(i * (self.tag_size + 2), self.tag_size) == self.tag))
                        ):
                            m.d.comb += self.bypass_next.eq(1)
                            # FIXME: Do we need to update use array here?
                            with m.If(self.bypass):
                                m.d.comb += self.new_tag_next.eq(self.new_tag)
                                m.d.comb += self.new_data_next.eq(self.new_data)
                                m.d.comb += self.new_use_next.eq(self.new_use)
                            with m.Else():
                                m.d.comb += self.new_tag_next.eq(self.tag_read_dout)
                                m.d.comb += self.new_data_next.eq(self.data_read_dout)
                                m.d.comb += self.new_use_next.eq(self.use_read_dout)
                            m.d.comb += self.new_tag_next.word_select(i, self.tag_size + 2).eq(Cat(self.tag, Const(3, 2)))
                            # TODO: Optimize the below if statement
                            num_bytes_per_word = Const(self.num_bytes)
                            num_bytes_per_line = Const(self.num_bytes * self.words_per_line)
                            for j in range(self.num_bytes):
                                with m.If(self.wmask_reg[j]):
                                    m.d.comb += self.new_data_next.word_select(i * num_bytes_per_line + self.offset * num_bytes_per_word + j, 8).eq(self.din_reg.word_select(j, 8))

            with m.Case(State.WAIT_READ):
                with m.If(~self.main_stall & ~self.csb & (self.set == self.addr.bit_select(self.offset_size, self.set_size))):
                    m.d.comb += self.bypass_next.eq(1)
                    m.d.comb += self.new_tag_next.eq(self.tag_read_dout)
                    # TODO: Optimize the below case statement
                    with m.Switch(self.way):
                        for i in range(self.num_ways):
                            with m.Case(i):
                                m.d.comb += self.new_tag_next.word_select(i, self.tag_size + 2).eq(Cat(self.tag, ~self.web_reg, Const(1, 1)))
                    m.d.comb += self.new_data_next.eq(self.data_read_dout)
                    # TODO: Optimize the below case statement.
                    with m.Switch(self.way):
                        for i in range(self.num_ways):
                            with m.Case(i):
                                m.d.comb += self.new_data_next.word_select(i, self.line_size).eq(self.main_dout)
                    m.d.comb += self.new_use_next.eq(self.way + 1)
                    with m.If(~self.web_reg):
                        # TODO: Optimize the below if statement.
                        for i in range(self.num_bytes):
                            with m.If(self.wmask_reg[i]):
                                m.d.comb += self.new_data_next.word_select(self.way * num_bytes_per_line + self.offset * num_bytes_per_word + i, 8).eq(self.din_reg.word_select(i, 8))