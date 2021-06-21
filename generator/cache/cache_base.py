# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#

class cache_base:
    """
    This is the abstract parent class of cache modules.
    Some common methods among different cache modules
    are implemented here.
    """
    def __init__(self, name, cache_config):

        cache_config.set_local_config(self)
        self.name = name


    def config_write(self, config_path):
        """ Write the configuration files for OpenRAM SRAM arrays. """

        self.dcf = open(config_path + "_data_array_config.py", "w")
        self.dcf.write("word_size = {}\n".format(self.row_size))
        self.dcf.write("num_words = {}\n".format(self.num_rows))
        # OpenRAM outputs of the data array are saved to a separate folder
        self.dcf.write("output_path = \"{}/tag_array\"\n".format(config_path))
        self.dcf.write("output_name = \"{}_tag_array\"\n".format(self.name))
        self.dcf.close()

        self.tcf = open(config_path + "_tag_array_config.py", "w")
        self.tcf.write("word_size = {}\n".format((2 + self.tag_size) * self.num_ways))
        self.tcf.write("num_words = {}\n".format(self.num_rows))
        # OpenRAM outputs of the tag array are saved to a separate folder
        self.tcf.write("output_path = \"{}/tag_array\"\n".format(config_path))
        self.tcf.write("output_name = \"{}_tag_array\"\n".format(self.name))
        self.tcf.close()


    def verilog_write(self, verilog_path):
        """ Write the behavioral Verilog model. """
        self.vf = open(verilog_path + ".v", "w")

        self.write_banner()

        # Cache module
        self.vf.write("module {} (\n".format(self.name))
        self.vf.write("  // CPU interface\n")
        self.vf.write("  clk, rst, csb, web, addr, din, dout, stall,\n")
        self.vf.write("  // Main memory interface\n")
        self.vf.write("  main_csb, main_web, main_addr, main_din, main_dout, main_stall\n")
        self.vf.write(");\n\n")

        self.write_parameters()

        self.write_io_ports()

        self.write_registers()        

        self.write_internal_arrays()

        self.write_flops()

        self.write_temp_variables()

        self.write_logic_block()

        self.vf.close()


    def write_banner(self):
        """ Write the banner of features of the cache. """

        self.vf.write("// ########## OpenCache Module ##########\n")

        if self.is_data_cache:
            self.vf.write("// Cache type         : Data\n")
        else:
            self.vf.write("// Cache type         : Instruction\n")

        self.vf.write("// Word size          : {}-bit\n".format(self.word_size))
        self.vf.write("// Words per line     : {}\n".format(self.words_per_line))
        self.vf.write("// Data array size    : {}-bit\n".format(self.total_size))

        if self.num_ways == 1:
            self.vf.write("// Placement policy   : Direct-mapped\n")
        elif self.set_size:
            self.vf.write("// Placement policy   : {}-way Set Associative\n".format(self.num_ways))
        else:
            self.vf.write("// Placement policy   : Fully Associative\n")

        if self.replacement_policy is None:
            self.vf.write("// Replacement policy : Direct\n")
        elif self.replacement_policy == "fifo":
            self.vf.write("// Replacement policy : First In First Out\n")
        elif self.replacement_policy == "lru":
            self.vf.write("// Replacement policy : Least Recently Used\n")
        elif self.replacement_policy == "random":
            self.vf.write("// Replacement policy : Random\n")

        if self.write_policy == "write-back":
            self.vf.write("// Write policy       : Write-back\n")
        elif self.write_policy == "write-through":
            self.vf.write("// Write policy       : Write-through\n")

        # TODO: How to adjust the data return size?
        if self.return_type == "word":
            self.vf.write("// Return type        : Word\n\n")
        elif self.return_type == "line":
            self.vf.write("// Return type        : Line\n\n")


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
        self.vf.write("  parameter  WORD_COUNT   = {};\n".format(self.words_per_line))
        self.vf.write("  localparam LINE_WIDTH   = WORD_WIDTH * WORD_COUNT;\n\n")
        self.vf.write("  localparam ADDR_WIDTH   = TAG_WIDTH + SET_WIDTH + OFFSET_WIDTH;\n")
        self.vf.write("  localparam CACHE_DEPTH  = 1 << SET_WIDTH;\n")
        if self.num_ways > 1:
            self.vf.write("  localparam WAY_DEPTH    = 1 << WAY_WIDTH;\n")
        self.vf.write("  // FIXME: This delay is arbitrary.\n")
        self.vf.write("  parameter  DELAY        = 3;\n\n")

        self.vf.write("  // States of the cache\n")
        self.vf.write("  localparam IDLE       = 0; // Fetch tag and data lines\n")
        self.vf.write("  localparam COMPARE    = 1; // Compare tags\n")
        self.vf.write("  localparam WRITE      = 2; // Send write request when main memory is available\n")
        self.vf.write("  localparam WAIT_WRITE = 3; // Wait for main memory to complete write request\n")
        self.vf.write("  localparam READ       = 4; // Send read request when main memory is available\n")
        self.vf.write("  localparam WAIT_READ  = 5; // Wait for main memory to return requested data\n\n")


    def write_io_ports(self):
        """ Write the IO ports of the cache. """

        self.vf.write("  input  clk;                   // clock\n")
        self.vf.write("  input  rst;                   // reset\n")
        self.vf.write("  input  csb;                   // active low chip select\n")
        self.vf.write("  input  web;                   // active low write control\n")
        self.vf.write("  input  [ADDR_WIDTH-1:0] addr; // address\n")
        self.vf.write("  input  [WORD_WIDTH-1:0] din;  // data input\n")
        self.vf.write("  output [WORD_WIDTH-1:0] dout; // data output\n")
        self.vf.write("  output stall;                 // pipeline stall\n\n")

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
        if self.replacement_policy not in [None, "random"]:
            self.vf.write("  {0}_{1}_array {1}_array (\n".format(self.name, self.replacement_policy))
            self.vf.write("    .clk0  (clk),\n")
            self.vf.write("    .csb0  ({}_write_csb),\n".format(self.replacement_policy))
            self.vf.write("    .addr0 ({}_write_addr),\n".format(self.replacement_policy))
            self.vf.write("    .din0  ({}_write_din),\n".format(self.replacement_policy))
            self.vf.write("    .clk1  (clk),\n")
            self.vf.write("    .csb1  ({}_read_csb),\n".format(self.replacement_policy))
            self.vf.write("    .addr1 ({}_read_addr),\n".format(self.replacement_policy))
            self.vf.write("    .dout1 ({}_read_dout)\n".format(self.replacement_policy))
            self.vf.write("  );\n\n")

        self.vf.write("  {}_tag_array tag_array (\n".format(self.name))
        self.vf.write("    .clk0  (clk),\n")
        self.vf.write("    .csb0  (tag_write_csb),\n")
        self.vf.write("    .addr0 (tag_write_addr),\n")
        self.vf.write("    .din0  (tag_write_din),\n")
        self.vf.write("    .clk1  (clk),\n")
        self.vf.write("    .csb1  (tag_read_csb),\n")
        self.vf.write("    .addr1 (tag_read_addr),\n")
        self.vf.write("    .dout1 (tag_read_dout)\n")
        self.vf.write("  );\n\n")

        self.vf.write("  {}_data_array data_array (\n".format(self.name))
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


    def write_logic_block(self):
        raise NotImplementedError("cache_base is an abstract class.")