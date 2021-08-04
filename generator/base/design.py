# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from nmigen import *
from nmigen.back import verilog
from rtl import *
from policy import ReplacementPolicy as RP
from globals import OPTS


class design(Elaboratable):
    """
    This is the base class for "elaboratable" design
    modules. Cache modules will inherit this.
    """

    def __init__(self):
        pass

    def verilog_write(self, verilog_path):
        """ Write the behavioral Verilog model. """

        # Add IO signals before elaborating
        self.add_io_signals()

        code = verilog.convert(self, name=self.name, strip_internal_attrs=OPTS.trim_verilog, ports=[
            # CPU interface signals
            self.clk, self.rst, self.flush, self.csb, self.web, self.wmask, self.addr, self.din, self.dout, self.stall,
            # Main memory interface signals
            self.main_csb, self.main_web, self.main_addr, self.main_din, self.main_dout, self.main_stall
        ])

        if OPTS.trim_verilog:
            code = trim_verilog(code)

        vf = open(verilog_path, "w")
        vf.write(code)
        vf.close()


    def elaborate(self, platform):
        """ Elaborate the design. Called by nMigen library. """

        m = Module()

        # NOTE: IO signals must be added before elaborating. Otherwise,
        # nMigen fails to detect port signals and their directions.

        self.add_internal_signals()
        self.add_srams(m)
        self.add_flop_block(m)
        self.add_memory_controller_block(m)
        self.add_state_block(m)
        self.add_request_block(m)
        self.add_output_block(m)
        if self.replacement_policy != RP.NONE:
            self.add_replacement_block(m)

        return m


    def add_io_signals(self):
        """ Add IO signals to cache design. """

        # CPU interface
        self.clk   = ClockSignal()
        self.rst   = ResetSignal()
        self.flush = Signal()
        self.csb   = Signal()
        self.web   = Signal()
        self.wmask = Signal(self.num_bytes)
        self.addr  = Signal(self.address_size)
        self.din   = Signal(self.word_size)
        self.dout  = Signal(self.word_size)
        self.stall = Signal()

        # Main memory interface
        self.main_csb   = Signal(reset_less=True, reset=1)
        self.main_web   = Signal(reset_less=True, reset=1)
        self.main_addr  = Signal(self.address_size - self.offset_size, reset_less=True)
        self.main_din   = Signal(self.line_size, reset_less=True)
        self.main_dout  = Signal(self.line_size)
        self.main_stall = Signal()


    def add_internal_signals(self):
        """ Add internal registers and wires to cache design. """

        # Keep inputs in flops
        self.tag, self.tag_next             = get_flop_signals("tag", self.tag_size)
        self.set, self.set_next             = get_flop_signals("set", self.set_size)
        self.offset, self.offset_next       = get_flop_signals("offset", self.offset_size)
        self.web_reg, self.web_reg_next     = get_flop_signals("web_reg")
        self.wmask_reg, self.wmask_reg_next = get_flop_signals("wmask_reg", self.num_bytes)
        self.din_reg, self.din_reg_next     = get_flop_signals("din_reg", self.word_size)

        # State flop
        self.state, self.state_next = get_flop_signals("state", State)


    def add_srams(self, m):
        """ Add internal SRAM array instances to cache design. """

        # Tag array
        word_size = (self.tag_size + 2) * self.num_ways
        self.tag_write_csb  = Signal(reset_less=True, reset=1)
        self.tag_write_addr = Signal(self.set_size, reset_less=True)
        self.tag_write_din  = Signal(word_size, reset_less=True)
        self.tag_read_csb   = Signal(reset_less=True)
        self.tag_read_addr  = Signal(self.set_size, reset_less=True)
        self.tag_read_dout  = Signal(word_size)
        m.submodules += Instance(OPTS.tag_array_name,
            ("i", "clk0",  self.clk),
            ("i", "csb0",  self.tag_write_csb),
            ("i", "addr0", self.tag_write_addr),
            ("i", "din0",  self.tag_write_din),
            ("i", "clk1",  self.clk),
            ("i", "csb1",  self.tag_read_csb),
            ("i", "addr1", self.tag_read_addr),
            ("o", "dout1", self.tag_read_dout),
        )

        # Data array
        word_size = self.line_size * self.num_ways
        self.data_write_csb  = Signal(reset_less=True, reset=1)
        self.data_write_addr = Signal(self.set_size, reset_less=True)
        self.data_write_din  = Signal(word_size, reset_less=True)
        self.data_read_csb   = Signal(reset_less=True)
        self.data_read_addr  = Signal(self.set_size, reset_less=True)
        self.data_read_dout  = Signal(word_size)
        m.submodules += Instance(OPTS.data_array_name,
            ("i", "clk0",  self.clk),
            ("i", "csb0",  self.data_write_csb),
            ("i", "addr0", self.data_write_addr),
            ("i", "din0",  self.data_write_din),
            ("i", "clk1",  self.clk),
            ("i", "csb1",  self.data_read_csb),
            ("i", "addr1", self.data_read_addr),
            ("o", "dout1", self.data_read_dout),
        )


    def add_flop_block(self, m):
        """ Add flip-flop block to cache design. """

        # In this block, flip-flop registers are updated at
        # every positive edge of the clock.

        # NOTE: LHS register of a flip-flop must end with "_next"
        for k, v in self.__dict__.items():
            lhs_name = k + "_next"
            if lhs_name in self.__dict__:
                m.d.sync += v.eq(self.__dict__[lhs_name])