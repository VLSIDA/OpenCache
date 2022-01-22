# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#

class test_bench:
    """
    Class to generate the test bench file for simulation.
    """

    def __init__(self, cache_config, name):

        cache_config.set_local_config(self)
        self.name = name

        self.success_message = "Simulation successful."
        self.failure_message = "Simulation failed."


    def test_bench_write(self, tb_path):
        """ Write the test bench file. """

        self.tbf = open(tb_path, "w")
        self.tbf.write("// Timescale is overwritten when running the EDA tool to prevent bugs\n")
        self.tbf.write("// `timescale 1ns / 1ps\n\n")
        self.tbf.write("module test_bench;\n\n")

        self.write_parameters()
        self.write_registers()
        self.write_dumps()
        self.write_clock_generator()
        self.write_reset_block()
        self.write_instances()
        self.write_tasks()

        self.tbf.write("  initial begin\n")
        self.tbf.write("    `include \"test_data.v\"\n")
        self.tbf.write("  end\n\n")
        self.tbf.write("endmodule\n")
        self.tbf.close()


    def write_parameters(self):
        """ Write the parameters of the test bench. """

        self.tbf.write("  parameter  TAG_WIDTH     = {};\n".format(self.tag_size))
        # TODO: Fully associative cache's set_size = 0.
        self.tbf.write("  parameter  SET_WIDTH     = {};\n".format(self.set_size))
        self.tbf.write("  parameter  OFFSET_WIDTH  = {};\n\n".format(self.offset_size))

        self.tbf.write("  parameter  WORD_WIDTH    = {};\n".format(self.word_size))
        if self.num_masks:
            self.tbf.write("  parameter  MASK_COUNT    = {};\n".format(self.num_masks))
        self.tbf.write("  parameter  WORD_COUNT    = {};\n".format(self.words_per_line))
        self.tbf.write("  localparam LINE_WIDTH    = WORD_WIDTH * WORD_COUNT;\n\n")

        self.tbf.write("  localparam ADDR_WIDTH    = TAG_WIDTH + SET_WIDTH + OFFSET_WIDTH;\n\n")

        self.tbf.write("  parameter  CLOCK_DELAY   = 5;\n")
        self.tbf.write("  // Reset is asserted for 1.5 cycles\n")
        self.tbf.write("  parameter  RESET_DELAY   = 15;\n")
        self.tbf.write("  parameter  DELAY         = 3;\n")
        self.tbf.write("  parameter  MAX_TEST_SIZE = 64;\n\n")


    def write_registers(self):
        """ Write the registers of the test bench. """

        self.tbf.write("  reg clk;\n")
        self.tbf.write("  reg rst;\n\n")

        self.tbf.write("  // Cache input pins\n")
        self.tbf.write("  reg cache_flush;\n")
        self.tbf.write("  reg cache_csb;\n")
        self.tbf.write("  reg cache_web;\n")
        if self.num_masks:
            self.tbf.write("  reg [MASK_COUNT-1:0] cache_wmask;\n")
        self.tbf.write("  reg [ADDR_WIDTH-1:0] cache_addr;\n")
        self.tbf.write("  reg [{}-1:0] cache_din;\n\n".format("WORD_WIDTH" if self.offset_size else "LINE_WIDTH"))

        self.tbf.write("  // Cache output pins\n")
        self.tbf.write("  wire [{}-1:0] cache_dout;\n\n".format("WORD_WIDTH" if self.offset_size else "LINE_WIDTH"))
        self.tbf.write("  wire cache_stall;\n")

        self.tbf.write("  // DRAM input pins\n")
        self.tbf.write("  wire dram_csb;\n")
        self.tbf.write("  wire dram_web;\n")
        self.tbf.write("  wire [ADDR_WIDTH-OFFSET_WIDTH-1:0] dram_addr;\n")
        self.tbf.write("  wire [LINE_WIDTH-1:0] dram_din;\n\n")

        self.tbf.write("  // DRAM output pins\n")
        self.tbf.write("  wire [LINE_WIDTH-1:0] dram_dout;\n\n")
        self.tbf.write("  wire dram_stall;\n")

        self.tbf.write("  // Test registers\n")
        self.tbf.write("  reg [MAX_TEST_SIZE-1:0] error_count;\n\n")


    def write_dumps(self):
        """ Write the $dumpfile and $dumpvars system functions for waveforms. """

        self.tbf.write("  initial begin\n")
        self.tbf.write("    $dumpfile(\"waves.vcd\");\n")
        self.tbf.write("    $dumpvars;\n")
        self.tbf.write("  end\n\n")


    def write_clock_generator(self):
        """ Write the clock generator of the test bench. """

        self.tbf.write("  // Clock generator\n")
        self.tbf.write("  initial begin\n")
        self.tbf.write("    clk = 1;\n")
        self.tbf.write("    forever #(CLOCK_DELAY) clk = !clk;\n")
        self.tbf.write("  end\n\n")


    def write_reset_block(self):
        """ Write the reset block of the test bench. """

        self.tbf.write("  // Reset registers\n")
        self.tbf.write("  initial begin\n")
        self.tbf.write("    rst         = 0;\n")
        self.tbf.write("    cache_flush = 0;\n")
        self.tbf.write("    cache_csb   = 1;\n")
        self.tbf.write("    cache_web   = 1;\n")
        if self.num_masks:
            self.tbf.write("    cache_wmask = 0;\n")
        self.tbf.write("    error_count = 0;\n")
        self.tbf.write("  end\n\n")


    def write_instances(self):
        """ Write the module instances of the cache and DRAM. """

        self.tbf.write("  {} cache_instance (\n".format(self.name))
        self.tbf.write("    .clk        (clk),\n")
        self.tbf.write("    .rst        (rst),\n")
        self.tbf.write("    .flush      (cache_flush),\n")
        self.tbf.write("    .csb        (cache_csb),\n")
        self.tbf.write("    .web        (cache_web),\n")
        if self.num_masks:
            self.tbf.write("    .wmask      (cache_wmask),\n")
        self.tbf.write("    .addr       (cache_addr),\n")
        self.tbf.write("    .din        (cache_din),\n")
        self.tbf.write("    .dout       (cache_dout),\n")
        self.tbf.write("    .stall      (cache_stall),\n")
        self.tbf.write("    .main_csb   (dram_csb),\n")
        self.tbf.write("    .main_web   (dram_web),\n")
        self.tbf.write("    .main_addr  (dram_addr),\n")
        self.tbf.write("    .main_din   (dram_din),\n")
        self.tbf.write("    .main_dout  (dram_dout),\n")
        self.tbf.write("    .main_stall (dram_stall)\n")
        self.tbf.write("  );\n\n")

        self.tbf.write("  dram dram_instance (\n")
        self.tbf.write("    .clk   (clk),\n")
        self.tbf.write("    .rst   (rst),\n")
        self.tbf.write("    .csb   (dram_csb),\n")
        self.tbf.write("    .web   (dram_web),\n")
        self.tbf.write("    .addr  (dram_addr),\n")
        self.tbf.write("    .din   (dram_din),\n")
        self.tbf.write("    .dout  (dram_dout),\n")
        self.tbf.write("    .stall (dram_stall)\n")
        self.tbf.write("  );\n\n")


    def write_tasks(self):
        """ Write the tasks of the test bench. """

        self.tbf.write("  // Assert the reset signal\n")
        self.tbf.write("  task assert_reset;\n")
        self.tbf.write("    begin\n")
        self.tbf.write("    // Reset is asserted just before a posedge of the clock.\n")
        self.tbf.write("    // Therefore, it is enough to assert it for DELAY.\n")
        self.tbf.write("    rst <= 1;\n")
        self.tbf.write("    rst <= #(DELAY) 0;\n")
        self.tbf.write("    end\n")
        self.tbf.write("  endtask\n\n")

        self.tbf.write("  // Assert the flush signal\n")
        self.tbf.write("  task assert_flush;\n")
        self.tbf.write("    begin\n")
        self.tbf.write("    // Flush is asserted just before a posedge of the clock.\n")
        self.tbf.write("    // Therefore, it is enough to assert it for DELAY.\n")
        self.tbf.write("    cache_flush <= 1;\n")
        self.tbf.write("    cache_flush <= #(DELAY) 0;\n")
        self.tbf.write("    end\n")
        self.tbf.write("  endtask\n\n")

        self.tbf.write("  // Check for a number of stall cycles starting from the current cycle\n")
        self.tbf.write("  task check_stall;\n")
        self.tbf.write("    input integer cycle_count;\n")
        self.tbf.write("    input [MAX_TEST_SIZE-1:0] test_count;\n")
        self.tbf.write("    integer i;\n")
        self.tbf.write("    begin\n")
        self.tbf.write("      for (i = 1; i <= cycle_count; i = i + 1) begin\n")
        self.tbf.write("        if (!cache_stall) begin\n")
        self.tbf.write("          $display(\"Error at test #%0d! Cache stall #%0d is expected to be high but it is low.\", test_count, i);\n")
        self.tbf.write("          error_count = error_count + 1;\n")
        self.tbf.write("        end\n")
        self.tbf.write("        #(CLOCK_DELAY * 2);\n")
        self.tbf.write("      end\n")
        self.tbf.write("    end\n")
        self.tbf.write("  endtask\n\n")

        self.tbf.write("  // Output of the cache must match the expected\n")
        self.tbf.write("  task check_dout;\n")
        self.tbf.write("    input [{}-1:0] dout_expected;\n".format("WORD_WIDTH" if self.offset_size else "LINE_WIDTH"))
        self.tbf.write("    input [MAX_TEST_SIZE-1:0] test_count;\n")
        self.tbf.write("    begin\n")
        self.tbf.write("      if (cache_dout !== dout_expected) begin\n")
        self.tbf.write("        $display(\"Error at test #%0d! Expected: %d, Received: %d\", test_count, dout_expected, cache_dout);\n")
        self.tbf.write("        error_count = error_count + 1;\n")
        self.tbf.write("      end\n")
        self.tbf.write("    end\n")
        self.tbf.write("  endtask\n\n")

        self.tbf.write("  // Print simulation result\n")
        self.tbf.write("  task end_simulation;\n")
        self.tbf.write("    begin\n")
        self.tbf.write("      if (!error_count) begin\n")
        self.tbf.write("        $display(\"{}\");\n".format(self.success_message))
        self.tbf.write("      end else begin\n")
        self.tbf.write("        $display(\"{} Error count: %0d\", error_count);\n".format(self.failure_message))
        self.tbf.write("      end\n")
        self.tbf.write("    end\n")
        self.tbf.write("  endtask\n\n")