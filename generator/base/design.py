# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from nmigen import *
from nmigen.back import verilog
from cache_signal import CacheSignal
from state import State
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
        ports = self.add_io_signals()

        code = verilog.convert(self,
                               name=self.name,
                               strip_internal_attrs=OPTS.trim_verilog,
                               ports=ports)

        if OPTS.trim_verilog:
            code = self.trim_verilog(code)

        with open(verilog_path, "w") as vf:
            vf.write(code)


    def trim_verilog(self, code):
        """ Trim unnecessary lines in a Verilog code. """

        lines = code.splitlines(True)

        for i in range(len(lines)):
            # Delete \initial register
            if "\\initial" in lines[i]:
                lines[i] = ""
            # Delete auto-generated flops
            if "$next" in lines[i]:
                lines[i] = ""

        code = "".join(lines)
        return code


    def elaborate(self, platform):
        """ Elaborate the design. Called by nMigen library. """

        m = Module()

        # NOTE: IO signals must be added before elaborating. Otherwise,
        # nMigen fails to detect port signals and their directions.

        self.add_internal_signals()
        self.add_srams(m)
        self.add_flop_block(m)
        self.add_default_statements(m)
        self.add_logic_blocks(m)

        return m


    def add_io_signals(self):
        """ Add IO signals to cache design. """

        # CPU interface
        self.clk   = ClockSignal()
        self.rst   = ResetSignal()
        self.flush = CacheSignal()
        self.csb   = CacheSignal()
        self.web   = CacheSignal()
        self.wmask = CacheSignal(self.num_bytes)
        self.addr  = CacheSignal(self.address_size)
        self.din   = CacheSignal(self.word_size)
        self.dout  = CacheSignal(self.word_size)
        self.stall = CacheSignal(reset=1)

        # Main memory interface
        self.main_csb   = CacheSignal(reset_less=True, reset=1)
        self.main_web   = CacheSignal(reset_less=True, reset=1)
        self.main_addr  = CacheSignal(self.address_size - self.offset_size, reset_less=True)
        self.main_din   = CacheSignal(self.line_size, reset_less=True)
        self.main_dout  = CacheSignal(self.line_size)
        self.main_stall = CacheSignal()

        # Return all port signals
        ports = []
        for _, v in self.__dict__.items():
            if isinstance(v, Value):
                ports.append(v)
        return ports


    def add_internal_signals(self):
        """ Add internal registers and wires to cache design. """

        # Keep inputs in flops
        self.tag       = CacheSignal(self.tag_size, is_flop=True)
        self.set       = CacheSignal(self.set_size, is_flop=True)
        self.offset    = CacheSignal(self.offset_size, is_flop=True)
        self.web_reg   = CacheSignal(is_flop=True)
        self.wmask_reg = CacheSignal(self.num_bytes, is_flop=True)
        self.din_reg   = CacheSignal(self.word_size, is_flop=True)

        # State flop
        self.state = CacheSignal(State, is_flop=True)


    def add_srams(self, m):
        """ Add internal SRAM array instances to cache design. """

        # Tag array
        word_size = self.tag_word_size * self.num_ways
        self.tag_write_csb  = CacheSignal(reset_less=True, reset=1)
        self.tag_write_addr = CacheSignal(self.set_size, reset_less=True)
        self.tag_write_din  = CacheSignal(word_size, reset_less=True)
        self.tag_read_csb   = CacheSignal(reset_less=True)
        self.tag_read_addr  = CacheSignal(self.set_size, reset_less=True)
        self.tag_read_dout  = CacheSignal(word_size)
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
        self.data_write_csb  = CacheSignal(reset_less=True, reset=1)
        self.data_write_addr = CacheSignal(self.set_size, reset_less=True)
        self.data_write_din  = CacheSignal(word_size, reset_less=True)
        self.data_read_csb   = CacheSignal(reset_less=True)
        self.data_read_addr  = CacheSignal(self.set_size, reset_less=True)
        self.data_read_dout  = CacheSignal(word_size)
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
        for _, v in self.__dict__.items():
            if isinstance(v, CacheSignal) and v.is_flop:
                m.d.sync += v.eq(v.next, sync=True)


    def add_default_statements(self, m):
        """ Add default statements of all flip-flops. """

        # Add default statements for flip-flops only.
        # Default statements of other registers are automatically
        # added by nMigen library.
        for _, v in self.__dict__.items():
            if isinstance(v, CacheSignal) and v.is_flop:
                m.d.comb += v.eq(v)