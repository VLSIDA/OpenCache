# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from nmigen import Elaboratable, Module
from nmigen import ClockSignal, ResetSignal
from nmigen import Value
from nmigen.back import verilog
from cache_signal import CacheSignal
from sram_instance import SramInstance
from dram import Dram
from state import State
from globals import OPTS


class design(Elaboratable):
    """
    This is the base class for "elaboratable" design modules.
    Cache modules will inherit this.
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

        # NOTE: IO signals must be added before elaborating. Otherwise, nMigen
        # fails to detect port signals and their directions.

        self.add_internal_signals()
        self.add_srams(self.m)
        self.add_flop_block(self.m)
        self.add_default_statements(self.m)
        self.add_logic_blocks(self.m)

        return self.m


    def add_io_signals(self):
        """ Add IO signals to cache design. """

        # Create the module here
        self.m = Module()

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

        # Create a DRAM module
        self.dram = Dram(self.m, self.address_size - self.offset_size, self.line_size)

        # Return all port signals
        ports = self.dram.get_pins()
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
        self.state     = CacheSignal(State, is_flop=True)


    def add_srams(self, m):
        """ Add internal SRAM array instances to cache design. """

        # Tag array
        word_size = self.tag_word_size * self.num_ways
        self.tag_array = SramInstance(OPTS.tag_array_name, word_size, 1, self, m)

        # Data array
        word_size = self.line_size * self.num_ways
        self.data_array = SramInstance(OPTS.data_array_name, word_size, OPTS.num_ways, self, m)


    def add_flop_block(self, m):
        """ Add flip-flop block to cache design. """

        # In this block, flip-flop registers are updated at every positive edge
        # of the clock.
        for _, v in self.__dict__.items():
            if isinstance(v, CacheSignal) and v.is_flop:
                m.d.sync += v.eq(v.next, sync=True)


    def add_default_statements(self, m):
        """ Add default statements of all flip-flops. """

        # Add default statements for flip-flops only.
        # Default statements of other registers are automatically added by
        # nMigen library.
        for _, v in self.__dict__.items():
            if isinstance(v, CacheSignal) and v.is_flop:
                m.d.comb += v.eq(v)