# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import re
from amaranth import Elaboratable, Module
from amaranth import ClockSignal, ResetSignal
from amaranth import Value
from amaranth.back import verilog
import debug
from cache_signal import cache_signal
from sram_instance import sram_instance
from dram_instance import dram_instance
from state import state
from hit_detector import hit_detector
from state_machine import state_machine
from input_interface import input_interface
from output_interface import output_interface
from memory_controller import memory_controller
from replacer import replacer
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
            # Don't delete the first line
            if i == 0:
                continue
            # Delete \initial register
            if "\\initial" in lines[i]:
                lines[i] = ""
            # Delete auto-generated flops
            if "$next" in lines[i]:
                lines[i] = ""
            # Delete attributes from lines
            lines[i] = re.sub(r"\(\*.*\*\)", "", lines[i])
            # Delete comments from lines
            lines[i] = re.sub(r"\/\*.*\*\/", "", lines[i])
            # Check if line is whitespace only
            if re.match(r".*[ \t]$", lines[i]):
                lines[i] = ""

        code = "".join(lines)
        return code


    def elaborate(self, platform):
        """ Elaborate the design. Called by Amaranth library. """

        # NOTE: IO signals must be added before elaborating. Otherwise, Amaranth
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
        self.clk = ClockSignal()
        self.rst = ResetSignal()
        if OPTS.has_flush:
            self.flush = cache_signal()
        self.csb = cache_signal()
        if not OPTS.read_only:
            self.web = cache_signal()
        if self.num_masks:
            self.wmask = cache_signal(self.num_masks)
        self.addr = cache_signal(self.address_size)
        if not OPTS.read_only:
            self.din = cache_signal(self.word_size if self.offset_size else self.line_size)
        self.dout = cache_signal(self.word_size if self.offset_size else self.line_size)
        self.stall = cache_signal(reset=1)

        # Create a DRAM module
        self.dram = dram_instance(self.m, self.dram_address_size, self.line_size, OPTS.read_only)

        # Return all port signals
        ports = self.dram.get_signals()
        for _, v in self.__dict__.items():
            if isinstance(v, Value):
                ports.append(v)
        return ports


    def add_internal_signals(self):
        """ Add internal registers and wires to cache design. """

        # Keep inputs in flops
        self.tag = cache_signal(self.tag_size, is_flop=True)
        self.set = cache_signal(self.set_size, is_flop=True)
        if self.offset_size:
            self.offset = cache_signal(self.offset_size, is_flop=True)
        if not OPTS.read_only:
            self.web_reg = cache_signal(is_flop=True)
        if self.num_masks:
            self.wmask_reg = cache_signal(self.num_masks, is_flop=True)
        if not OPTS.read_only:
            self.din_reg = cache_signal(self.word_size if self.offset_size else self.line_size, is_flop=True)
        # State flop
        self.state = cache_signal(state, is_flop=True)


    def add_srams(self, m):
        """ Add internal SRAM array instances to cache design. """

        # Tag array
        word_size = self.tag_word_size * self.num_ways
        self.tag_array = sram_instance(OPTS.tag_array_name, word_size, 1, self, m)

        # Data array
        word_size = self.line_size * self.num_ways
        self.data_array = sram_instance(OPTS.data_array_name, word_size, OPTS.num_ways, self, m)


    def add_flop_block(self, m):
        """ Add flip-flop block to cache design. """

        # In this block, flip-flop registers are updated at every positive edge
        # of the clock.
        for _, v in self.__dict__.items():
            if isinstance(v, cache_signal) and v.is_flop:
                m.d.sync += v.eq(v.next, sync=True)


    def add_default_statements(self, m):
        """ Add default statements of all flip-flops. """

        # Add default statements for flip-flops only.
        # Default statements of other registers are automatically added by
        # Amaranth library.
        for _, v in self.__dict__.items():
            if isinstance(v, cache_signal) and v.is_flop:
                m.d.comb += v.eq(v)


    def add_logic_blocks(self, m):
        """ Instantiate and add logic blocks. """
        debug.info(1, "Adding logic blocks...")

        # Add helper modules here
        self.hit_detector = hit_detector(self, m)

        # Add logic modules
        logics = []
        logics.append(state_machine())
        logics.append(input_interface())
        logics.append(output_interface())
        logics.append(memory_controller())
        logics.append(replacer())

        for logic in logics:
            logic.add(self, m)