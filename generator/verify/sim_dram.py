# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
DRAM_DELAY = 4


class sim_dram:
    """
    Class to generate the DRAM module for simulation.
    """

    def __init__(self, cache_config, data=None):

        cache_config.set_local_config(self)
        self.make_initial_data(data)


    def sim_dram_write(self, dram_path):
        """ Write the DRAM file. """

        self.df = open(dram_path, "w")
        self.df.write("module dram (clk, rst, csb, web, addr, din, dout, stall);\n\n")

        self.write_parameters()
        self.write_io_ports()
        self.write_registers()
        self.write_logic_block()
        self.write_initial_data()

        self.df.write("endmodule\n")
        self.df.close()


    def write_parameters(self):
        """ Write the parameters of the DRAM. """

        self.df.write("  parameter  WORD_WIDTH  = {};\n".format(self.line_size))
        self.df.write("  parameter  ADDR_WIDTH  = {};\n".format(self.tag_size + self.set_size))
        self.df.write("  localparam DRAM_DEPTH  = 1 << ADDR_WIDTH;\n\n")
        self.df.write("  // This delay is used to \"imitate\" DRAMs' low frequencies\n")
        self.df.write("  parameter  CYCLE_DELAY = {};\n".format(DRAM_DELAY))
        self.df.write("  parameter  DELAY       = 3;\n\n")


    def write_io_ports(self):
        """ Write the IO ports of the DRAM. """

        self.df.write("  input  clk;\n")
        self.df.write("  input  rst;\n")
        self.df.write("  input  csb;\n")
        self.df.write("  input  web;\n")
        self.df.write("  input  [ADDR_WIDTH-1:0] addr;\n")
        self.df.write("  input  [WORD_WIDTH-1:0] din;\n")
        self.df.write("  output [WORD_WIDTH-1:0] dout;\n")
        self.df.write("  output stall;\n\n")


    def write_registers(self):
        """ Write the registers of the DRAM. """

        self.df.write("  reg [WORD_WIDTH-1:0] dout;\n")
        self.df.write("  reg stall;\n\n")
        self.df.write("  reg [WORD_WIDTH-1:0] memory [0:DRAM_DEPTH-1];\n\n")


    def write_logic_block(self):
        """ Write the logic block of the DRAM. """

        self.df.write("  always @(posedge clk) begin\n")
        self.df.write("    if (rst) begin\n")
        self.df.write("      dout  <= {WORD_WIDTH{1'bx}};\n")
        self.df.write("      stall <= 0;\n")
        self.df.write("    end else if (!csb && !stall) begin\n")
        self.df.write("      stall <= 1; // When there is a request, DRAM immediately stalls\n")
        self.df.write("      stall <= #(CYCLE_DELAY * 5 * 2 + DELAY) 0; // Stall becomes low after a couple of cycles\n")
        self.df.write("      dout  <= #(DELAY) memory[addr];\n")
        self.df.write("      if (!web)\n")
        self.df.write("        memory[addr] <= #(DELAY) din;\n")
        self.df.write("    end\n")
        self.df.write("  end\n\n")


    def write_initial_data(self):
        """ Write the initial data in the memory. """

        if self.data:
            self.df.write("  initial begin\n")
            for i in range(len(self.data)):
                self.df.write("    memory[{0}] <= {1}'d{2};\n".format(i, self.line_size, self.data[i]))
            self.df.write("  end\n\n")


    def make_initial_data(self, data):
        """ Prepare the intial data in the memory. """

        self.data = []
        for line in data:
            self.data.append(0)
            for i in range(len(line)):
                self.data[-1] += line[i] << i * self.word_size