# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from globals import OPTS, NAME
from textwrap import wrap
from nmigen import *


class design(Elaboratable):
    """
    This is the base class for "elaboratable" design
    modules. Cache modules will inherit this.
    """

    def __init__(self):
        pass


    def verilog_write(self, verilog_path):
        """ Write the behavioral Verilog model. """

        self.vf = open(verilog_path, "w")
        self.write_cache_banner()

        # Cache module
        self.vf.write("module {} (\n".format(self.name))
        self.vf.write("  // CPU interface\n")
        self.vf.write("  clk, rst, flush, csb, web, wmask, addr, din, dout, stall,\n")
        self.vf.write("  // Main memory interface\n")
        self.vf.write("  main_csb, main_web, main_addr, main_din, main_dout, main_stall\n")
        self.vf.write(");\n\n")

        self.write_parameters()
        self.write_io_ports()
        self.write_registers()        
        self.write_internal_arrays()
        self.write_temp_variables()
        self.write_logic_blocks()

        self.vf.write("endmodule\n")
        self.vf.close()


    def write_title_banner(self, title, descr=None, indent=0):
        """ Write a title banner. """

        self.vf.write(("  " * indent) + "///" + ("/" * 50) + "///\n")
        self.vf.write(("  " * indent) + "// " + " ".center(50) + " //\n")
        self.vf.write(("  " * indent) + "// " + title.center(50) + " //\n")
        self.vf.write(("  " * indent) + "// " + " ".center(50) + " //\n")
        self.vf.write(("  " * indent) + "///" + ("/" * 50) + "///\n")

        if descr is not None:
            self.vf.write(("  " * indent) + "// " + " ".center(50) + " //\n")
            for wline in wrap(descr, 50):
                self.vf.write(("  " * indent) + "// " + wline.ljust(50) + " //\n")
            self.vf.write(("  " * indent) + "// " + " ".center(50) + " //\n")
            self.vf.write(("  " * indent) + "///" + ("/" * 50) + "///\n")


    def write_cache_banner(self):
        """ Write the banner of cache features. """

        cache_type = "Data" if self.is_data_cache else "Instruction"
        word_size  = "{}-bit".format(self.word_size)
        words_per_line = str(self.words_per_line)
        array_size = "{}-bit".format(self.total_size)
        associativity = str(self.associativity)
        replacement_policy = self.replacement_policy.long_name()
        num_ways = str(self.num_ways)
        write_policy = self.write_policy.long_name()
        # TODO: How to adjust the data return size?
        return_type = self.return_type.capitalize()
        data_hazard = str(self.data_hazard)

        self.write_title_banner(NAME)
        self.vf.write("// Cache type         :" + cache_type.rjust(30) + " //\n")
        self.vf.write("// Word size          :" + word_size.rjust(30) + " //\n")
        self.vf.write("// Words per line     :" + words_per_line.rjust(30) + " //\n")
        self.vf.write("// Data array size    :" + array_size.rjust(30) + " //\n")
        self.vf.write("// Associativity      :" + associativity.rjust(30) + " //\n")
        self.vf.write("// Replacement policy :" + replacement_policy.rjust(30) + " //\n")
        self.vf.write("// Number of ways     :" + num_ways.rjust(30) + " //\n")
        self.vf.write("// Write policy       :" + write_policy.rjust(30) + " //\n")
        self.vf.write("// Return type        :" + return_type.rjust(30) + " //\n")
        self.vf.write("// Data hazard        :" + data_hazard.rjust(30) + " //\n")
        self.vf.write("///" + ("/" * 50) + "///\n\n")


    def write_parameters(self):
        """ Write the parameters of the cache. """

        self.vf.write("  parameter  TAG_WIDTH    = {};\n".format(self.tag_size))
        # TODO: Fully associative cache's set_size = 0.
        self.vf.write("  parameter  SET_WIDTH    = {};\n".format(self.set_size))
        self.vf.write("  parameter  OFFSET_WIDTH = {};\n".format(self.offset_size))
        if self.num_ways > 1:
            self.vf.write("  parameter  WAY_WIDTH    = {};\n".format(self.way_size))
        self.vf.write("\n")

        self.vf.write("  parameter  WORD_WIDTH   = {};\n".format(self.word_size))
        self.vf.write("  parameter  BYTE_COUNT   = {};\n".format(self.num_bytes))
        self.vf.write("  parameter  WORD_COUNT   = {};\n".format(self.words_per_line))
        self.vf.write("  localparam LINE_WIDTH   = WORD_WIDTH * WORD_COUNT;\n\n")
        self.vf.write("  localparam ADDR_WIDTH   = TAG_WIDTH + SET_WIDTH + OFFSET_WIDTH;\n")
        self.vf.write("  localparam CACHE_DEPTH  = 1 << SET_WIDTH;\n")
        if self.num_ways > 1:
            self.vf.write("  localparam WAY_DEPTH    = 1 << WAY_WIDTH;\n")

        self.vf.write("  // FIXME: This delay is arbitrary.\n")
        self.vf.write("  parameter  DELAY        = 3;\n\n")

        self.vf.write("  // States of the cache\n")
        self.vf.write("  localparam RESET      = 0; // Reset tags and registers\n")
        # Instruction caches don't have flush state
        if self.is_data_cache:
            self.vf.write("  localparam FLUSH      = 1; // Write all data lines back to main memory\n")
        self.vf.write("  localparam IDLE       = 2; // Fetch tag and data lines\n")
        self.vf.write("  localparam COMPARE    = 3; // Compare tags\n")
        # Instruction caches don't have write states
        if self.is_data_cache:
            self.vf.write("  localparam WRITE      = 4; // Send write request when main memory is available\n")
            self.vf.write("  localparam WAIT_WRITE = 5; // Wait for main memory to complete write request\n")
        self.vf.write("  localparam READ       = 6; // Send read request when main memory is available\n")
        self.vf.write("  localparam WAIT_READ  = 7; // Wait for main memory to return requested data\n\n")


    def write_io_ports(self):
        """ Write the IO ports of the cache. """

        self.vf.write("  input  clk;                    // clock\n")
        self.vf.write("  input  rst;                    // reset\n")
        self.vf.write("  input  flush;                  // flush\n")
        self.vf.write("  input  csb;                    // active low chip select\n")
        self.vf.write("  input  web;                    // active low write control\n")
        self.vf.write("  input  [BYTE_COUNT-1:0] wmask; // write mask\n")
        self.vf.write("  input  [ADDR_WIDTH-1:0] addr;  // address\n")
        self.vf.write("  input  [WORD_WIDTH-1:0] din;   // data input\n")
        self.vf.write("  output [WORD_WIDTH-1:0] dout;  // data output\n")
        self.vf.write("  output stall;                  // pipeline stall\n\n")

        self.vf.write("  output main_csb;                                // main memory active low chip select\n")
        self.vf.write("  output main_web;                                // main memory active low write control\n")
        self.vf.write("  output [ADDR_WIDTH-OFFSET_WIDTH-1:0] main_addr; // main memory address\n")
        self.vf.write("  output [LINE_WIDTH-1:0] main_din;               // main memory data input\n")
        self.vf.write("  input  [LINE_WIDTH-1:0] main_dout;              // main memory data output\n")
        self.vf.write("  input  main_stall;                              // high when waiting for main memory\n\n")


    def write_internal_arrays(self):
        """ Write the internal OpenRAM SRAM array instances of the cache. """

        self.vf.write("  // For synthesis, modify OpenRAM modules or make these modules black box.\n")

        # Random replacement policy doesn't require a separate SRAM array
        if self.replacement_policy.has_sram_array():
            rp_name = str(self.replacement_policy)
            self.vf.write("  {0} {1}_array (\n".format(OPTS.use_array_name, rp_name))
            self.vf.write("    .clk0  (clk),\n")
            self.vf.write("    .csb0  ({}_write_csb),\n".format(rp_name))
            self.vf.write("    .addr0 ({}_write_addr),\n".format(rp_name))
            self.vf.write("    .din0  ({}_write_din),\n".format(rp_name))
            self.vf.write("    .clk1  (clk),\n")
            self.vf.write("    .csb1  ({}_read_csb),\n".format(rp_name))
            self.vf.write("    .addr1 ({}_read_addr),\n".format(rp_name))
            self.vf.write("    .dout1 ({}_read_dout)\n".format(rp_name))
            self.vf.write("  );\n\n")

        self.vf.write("  {} tag_array (\n".format(OPTS.tag_array_name))
        self.vf.write("    .clk0  (clk),\n")
        self.vf.write("    .csb0  (tag_write_csb),\n")
        self.vf.write("    .addr0 (tag_write_addr),\n")
        self.vf.write("    .din0  (tag_write_din),\n")
        self.vf.write("    .clk1  (clk),\n")
        self.vf.write("    .csb1  (tag_read_csb),\n")
        self.vf.write("    .addr1 (tag_read_addr),\n")
        self.vf.write("    .dout1 (tag_read_dout)\n")
        self.vf.write("  );\n\n")

        self.vf.write("  {} data_array (\n".format(OPTS.data_array_name))
        self.vf.write("    .clk0  (clk),\n")
        self.vf.write("    .csb0  (data_write_csb),\n")
        self.vf.write("    .addr0 (data_write_addr),\n")
        self.vf.write("    .din0  (data_write_din),\n")
        self.vf.write("    .clk1  (clk),\n")
        self.vf.write("    .csb1  (data_read_csb),\n")
        self.vf.write("    .addr1 (data_read_addr),\n")
        self.vf.write("    .dout1 (data_read_dout)\n")
        self.vf.write("  );\n\n")


    def write_registers(self):
        raise NotImplementedError("cache_base is an abstract class.")


    def write_flops(self):
        raise NotImplementedError("cache_base is an abstract class.")


    def write_temp_variables(self):
        raise NotImplementedError("cache_base is an abstract class.")


    def write_logic_blocks(self):
        raise NotImplementedError("cache_base is an abstract class.")


    def wrap_data_hazard(self, lines, indent=0):
        """ Wrap given Verilog lines with data hazard control. """

        # If data_hazard is false, return the original lines
        if not self.data_hazard:
            if type(lines) is str:
                for line in lines:
                    line = (indent * "  ") + line
            return lines

        # Given lines are if statements
        # Assuming that statement is given in a single line
        if type(lines) is str:
            dh_line = lines
            for or_reg, bp_reg in self.bypass_regs.items():
                dh_line = dh_line.replace(or_reg, bp_reg)
            new_line = "(bypass && {0}) || (!bypass && {1})".format(dh_line, lines)
            return new_line

        # Multiple lines are given in a list
        else:
            new_lines = [
                (indent * "  ") + "// Use bypass registers if needed\n",
                (indent * "  ") + "if (bypass) begin\n"
            ]
            for line in lines:
                dh_line = line
                for or_reg, bp_reg in self.bypass_regs.items():
                    dh_line = dh_line.replace(or_reg, bp_reg)
                new_lines.append(((indent + 1) * "  ") + dh_line + "\n")

            new_lines.append((indent * "  ") + "end else begin\n")

            for line in lines:
                new_lines.append(((indent + 1) * "  ") + line + "\n")

            new_lines.append((indent * "  ") + "end\n")

            return new_lines