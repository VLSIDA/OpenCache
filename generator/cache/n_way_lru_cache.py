# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from cache_base import cache_base
from globals import OPTS


class n_way_lru_cache(cache_base):
    """
    This is the design module of N-way set associative cache
    with LRU replacement policy.
    """

    def __init__(self, cache_config, name):

        super().__init__(cache_config, name)

        self.bypass_regs = {
            "lru_read_dout":  "new_lru",
            "tag_read_dout":  "new_tag",
            "data_read_dout": "new_data"
        }


    def config_write(self, config_paths):
        """ Write the configuration files for OpenRAM SRAM arrays. """

        super().config_write(config_paths[:-1])

        self.lcf = open(config_paths[-1], "w")

        self.lcf.write("word_size = {}\n".format(self.way_size * self.num_ways))
        self.lcf.write("num_words = {}\n".format(self.num_rows))

        self.lcf.write("num_rw_ports = 0\n")
        self.lcf.write("num_r_ports  = 1\n")
        self.lcf.write("num_w_ports  = 1\n")

        # OpenRAM outputs of the LRU array are saved to a separate folder
        self.lcf.write("output_path = \"{}/lru_array\"\n".format(OPTS.output_path))
        self.lcf.write("output_name = \"{}_lru_array\"\n".format(self.name))

        self.lcf.close()


    def write_parameters(self):
        """ Write the parameters of the cache. """

        super().write_parameters()

        # This parameter is used to update LRU bits
        self.vf.write("  // Maximum value of a way.\n")
        self.vf.write("  localparam WAY_LIMIT = {};\n".format(self.num_ways - 1))
        self.vf.write("\n")


    def write_registers(self):
        """ Write the registers of the cache. """

        self.vf.write("  reg web_reg, web_reg_next;\n")
        self.vf.write("  reg stall;\n")
        self.vf.write("  reg [TAG_WIDTH-1:0]    tag, tag_next;\n")
        self.vf.write("  reg [SET_WIDTH-1:0]    set, set_next;\n")
        self.vf.write("  reg [OFFSET_WIDTH-1:0] offset, offset_next;\n")
        self.vf.write("  reg [WORD_WIDTH-1:0]   din_reg, din_reg_next;\n")
        self.vf.write("  reg [WORD_WIDTH-1:0]   dout;\n")
        self.vf.write("  reg [2:0]              state, state_next;\n")
        self.vf.write("  reg [WAY_WIDTH-1:0]    way, way_next;                          // way that is chosen to evict\n")

        # No need for bypass registers if SRAMs are
        # guaranteed to be data hazard proof
        if self.data_hazard:
            self.vf.write("  // When the next fetch is in the same set, tag_array and data_array might be old (data hazard).\n")
            self.vf.write("  reg bypass, bypass_next;                                       // high if write and read from arrays must be done at the same cycle\n")
            self.vf.write("  reg [WAY_WIDTH * WAY_DEPTH-1:0]       new_lru, new_lru_next;   // new replacement bits from the previous cycle\n")
            self.vf.write("  reg [(2 + TAG_WIDTH) * WAY_DEPTH-1:0] new_tag, new_tag_next;   // new tag line from the previous cycle\n")
            self.vf.write("  reg [LINE_WIDTH * WAY_DEPTH-1:0]      new_data, new_data_next; // new data line from the previous cycle\n\n")

        self.vf.write("  // Main memory ports\n")
        self.vf.write("  reg main_csb;\n")
        self.vf.write("  reg main_web;\n")
        self.vf.write("  reg [ADDR_WIDTH - OFFSET_WIDTH-1:0] main_addr;\n")
        self.vf.write("  reg [LINE_WIDTH-1:0] main_din;\n\n")

        self.vf.write("  // LRU array read port\n")
        self.vf.write("  reg  lru_read_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] lru_read_addr;\n")
        self.vf.write("  wire [WAY_WIDTH * WAY_DEPTH-1:0] lru_read_dout;\n")
        self.vf.write("  // LRU array write port\n")
        self.vf.write("  reg  lru_write_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] lru_write_addr;\n")
        self.vf.write("  reg  [WAY_WIDTH * WAY_DEPTH-1:0] lru_write_din;\n\n")

        self.vf.write("  // Tag array read port\n")
        self.vf.write("  reg  tag_read_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] tag_read_addr;\n")
        self.vf.write("  wire [(2 + TAG_WIDTH) * WAY_DEPTH-1:0] tag_read_dout;\n")
        self.vf.write("  // Tag array write port\n")
        self.vf.write("  reg  tag_write_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] tag_write_addr;\n")
        self.vf.write("  reg  [(2 + TAG_WIDTH) * WAY_DEPTH-1:0] tag_write_din;\n\n")

        self.vf.write("  // Data array read port\n")
        self.vf.write("  reg  data_read_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] data_read_addr;\n")
        self.vf.write("  wire [LINE_WIDTH * WAY_DEPTH-1:0] data_read_dout;\n")
        self.vf.write("  // Data array write port\n")
        self.vf.write("  reg  data_write_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] data_write_addr;\n")
        self.vf.write("  reg  [LINE_WIDTH * WAY_DEPTH-1:0] data_write_din;\n\n")


    def write_temp_variables(self):
        """ Write the temporary variables of the cache. """

        # For loop variables
        self.vf.write("  // These should be unrolled during synthesis.\n")
        self.vf.write("  // Each always block has its own variable to prevent combinational\n")
        self.vf.write("  // loop in simulation.\n")
        self.vf.write("  integer var_0;\n")
        self.vf.write("  integer var_1;\n")
        self.vf.write("  integer var_3;\n")
        self.vf.write("  integer var_4;\n")
        self.vf.write("  integer var_5;\n")
        self.vf.write("  integer var_6;\n")
        self.vf.write("  integer var_7;\n")
        self.vf.write("  integer var_8;\n")
        self.vf.write("  integer var_9;\n")
        self.vf.write("  integer var_10;\n\n")


    def write_logic_blocks(self):
        """ Write the always blocks. """

        self.write_flop_block()
        self.write_memory_controller_block()
        self.write_state_block()
        self.write_request_block()
        self.write_output_block()
        self.write_replacement_block()
        if self.data_hazard:
            self.write_bypass_block()


    def write_flop_block(self):
        """ Write the flip-flops of the cache. """

        title = "Flip-Flop Block"
        descr = "In this block, flip-flop registers are updated at " + \
                "every positive edge of the clock."

        self.write_title_banner(title, descr, indent=1)
        self.vf.write("  always @(posedge clk) begin\n")
        self.vf.write("    state    <= #(DELAY) state_next;\n")
        self.vf.write("    way      <= #(DELAY) way_next;\n")
        self.vf.write("    tag      <= #(DELAY) tag_next;\n")
        self.vf.write("    set      <= #(DELAY) set_next;\n")
        self.vf.write("    offset   <= #(DELAY) offset_next;\n")
        self.vf.write("    web_reg  <= #(DELAY) web_reg_next;\n")
        self.vf.write("    din_reg  <= #(DELAY) din_reg_next;\n")

        if self.data_hazard:
            self.vf.write("    bypass   <= #(DELAY) bypass_next;\n")
            self.vf.write("    new_lru  <= #(DELAY) new_lru_next;\n")
            self.vf.write("    new_tag  <= #(DELAY) new_tag_next;\n")
            self.vf.write("    new_data <= #(DELAY) new_data_next;\n")

        self.vf.write("  end\n\n\n")


    def write_memory_controller_block(self):
        """ Write the logic always block of the cache. """

        title = "Memory Controller Block"
        descr = "In this block, cache communicates with memory components " + \
                "which are LRU array, tag array, data array, and main memory."

        self.write_title_banner(title, descr, indent=1)
        self.vf.write("  always @* begin\n")
        self.vf.write("    main_csb        = 1;\n")
        self.vf.write("    main_web        = 1;\n")
        self.vf.write("    main_addr       = 0;\n")
        self.vf.write("    main_din        = 0;\n")
        self.vf.write("    tag_read_csb    = 0;\n")
        self.vf.write("    tag_read_addr   = 0;\n")
        self.vf.write("    tag_write_csb   = 1;\n")
        self.vf.write("    tag_write_addr  = 0;\n")
        self.vf.write("    tag_write_din   = 0;\n")
        self.vf.write("    data_read_csb   = 0;\n")
        self.vf.write("    data_read_addr  = 0;\n")
        self.vf.write("    data_write_csb  = 1;\n")
        self.vf.write("    data_write_addr = 0;\n")
        self.vf.write("    data_write_din  = 0;\n\n")

        self.vf.write("    // If rst is high, state switches to RESET.\n")
        self.vf.write("    // Registers, which are reset only once, are reset here.\n")
        self.vf.write("    // In the RESET state, cache will set all LRU and tag\n")
        self.vf.write("    // array lines to 0.\n")
        self.vf.write("    if (rst) begin\n")
        self.vf.write("      tag_write_csb  = 0;\n")
        self.vf.write("      tag_write_addr = 0;\n")
        self.vf.write("      tag_write_din  = 0;\n")
        self.vf.write("    end\n\n")

        self.vf.write("    // If flush is high, state switches to FLUSH.\n")
        self.vf.write("    // In the FLUSH state, cache will write all data lines back\n")
        self.vf.write("    // to main memory.\n")
        self.vf.write("    // TODO: Cache should write only dirty lines back.\n")
        self.vf.write("    else if (flush) begin\n")
        self.vf.write("      tag_read_csb   = 0;\n")
        self.vf.write("      tag_read_addr  = 0;\n")
        self.vf.write("      data_read_csb  = 0;\n")
        self.vf.write("      data_read_addr = 0;\n")
        self.vf.write("    end\n\n")

        self.vf.write("    else begin\n")
        self.vf.write("      case (state)\n\n")

        # RESET state
        self.vf.write("        // In the RESET state, cache sends write request to LRU\n")
        self.vf.write("        // and tag arrays to reset the current set.\n")
        self.vf.write("        //\n")
        self.vf.write("        // set register is incremented by the Request Decode Block.\n")
        self.vf.write("        //\n")
        self.vf.write("        // When set register reaches the end, state switches to IDLE.\n")
        self.vf.write("        RESET: begin\n")
        self.vf.write("          tag_write_csb  = 0;\n")
        self.vf.write("          tag_write_addr = set;\n")
        self.vf.write("          tag_write_din  = 0;\n")
        self.vf.write("        end\n\n")

        # FLUSH state
        self.vf.write("        // In the FLUSH state, cache sends write request to main\n")
        self.vf.write("        // memory.\n")
        self.vf.write("        //\n")
        self.vf.write("        // set register is incremented by the Request Decode Block.\n")
        self.vf.write("        // way register is incremented by the Replacement Block.\n")
        self.vf.write("        //\n")
        self.vf.write("        // When set and way registers reach the end, state switches\n")
        self.vf.write("        // to IDLE.\n")
        self.vf.write("        // TODO: Cache should write only dirty lines back.\n")
        self.vf.write("        FLUSH: begin\n")
        self.vf.write("          tag_read_csb   = 0;\n")
        self.vf.write("          tag_read_addr  = set;\n")
        self.vf.write("          data_read_csb  = 0;\n")
        self.vf.write("          data_read_addr = set;\n")
        self.vf.write("          main_csb       = 0;\n")
        self.vf.write("          main_web       = 0;\n")
        self.vf.write("          main_addr      = {tag_read_dout[way * (TAG_WIDTH + 2) +: TAG_WIDTH], set};\n")
        self.vf.write("          main_din       = data_read_dout[way * LINE_WIDTH +: LINE_WIDTH];\n")
        self.vf.write("          if (!main_stall && way == WAY_DEPTH - 1) begin\n")
        self.vf.write("            tag_read_addr  = set + 1;\n")
        self.vf.write("            data_read_addr = set + 1;\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n\n")

        # IDLE state
        self.vf.write("        // In the IDLE state, cache waits for CPU to send a new request.\n")
        self.vf.write("        // Until there is a new request from the cache, stall is low.\n")
        self.vf.write("        //\n")
        self.vf.write("        // When there is a new request from the cache stall is asserted,\n")
        self.vf.write("        // request is decoded and corresponding LRU, tag, and data\n")
        self.vf.write("        // lines are read from internal SRAM arrays.\n")
        self.vf.write("        IDLE: begin\n")
        self.vf.write("          if (!csb) begin\n")
        self.vf.write("            tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("            data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("            // FIXME: This might cause a problem, need to recheck.\n")
        self.vf.write("            // Data input to data_array is made unknown in order to\n")
        self.vf.write("            // prevent writing other lines' data to the data array.\n")
        self.vf.write("            data_write_din = 'bx;\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n\n")

        # COMPARE state
        self.vf.write("        // In the COMPARE state, cache compares tags.\n")
        self.vf.write("        // Stall and output are driven by the Output Block.\n")
        self.vf.write("        COMPARE: begin\n")
        self.vf.write("          for (var_0 = 0; var_0 < WAY_DEPTH; var_0 = var_0 + 1) begin\n")
        self.vf.write("            // Find the least recently used way (the way having 0 LRU number)\n")

        lines = "!lru_read_dout[var_0 * WAY_WIDTH +: WAY_WIDTH]"
        lines = self.wrap_data_hazard(lines)

        self.vf.write("            if ({}) begin\n".format(lines))
        self.vf.write("              // Assuming that current request is miss, check if it is a dirty miss\n")

        lines = "tag_read_dout[var_0 * (TAG_WIDTH + 2) + TAG_WIDTH +: 2] == 2'b11"
        lines = self.wrap_data_hazard(lines)

        self.vf.write("              if ({}) begin\n".format(lines))
        self.vf.write("                // If main memory is busy, switch to WRITE and wait for\n")
        self.vf.write("                // main memory to be available.\n")
        self.vf.write("                if (main_stall) begin\n")
        self.vf.write("                  tag_read_addr  = set;\n")
        self.vf.write("                  data_read_addr = set;\n")
        self.vf.write("                end\n")
        self.vf.write("                // If main memory is available, switch to WAIT_WRITE and\n")
        self.vf.write("                // wait for main memory to complete writing.\n")
        self.vf.write("                else begin\n")
        self.vf.write("                  main_csb = 0;\n")
        self.vf.write("                  main_web = 0;\n")

        lines = [
            "main_addr = {tag_read_dout[var_0 * (TAG_WIDTH + 2) +: TAG_WIDTH], set};",
            "main_din  = data_read_dout[var_0 * LINE_WIDTH +: LINE_WIDTH];"
        ]
        lines = self.wrap_data_hazard(lines, indent=9)

        self.vf.writelines(lines)
        self.vf.write("                end\n")
        self.vf.write("              end\n")
        self.vf.write("              // Else, assume that current request is a clean miss\n")
        self.vf.write("              else begin\n")
        self.vf.write("                if (!main_stall) begin\n")
        self.vf.write("                  tag_read_addr  = set;\n")
        self.vf.write("                  data_read_addr = set;\n")
        self.vf.write("                  main_csb       = 0;\n")
        self.vf.write("                  main_addr      = {tag, set};\n")
        self.vf.write("                end\n")
        self.vf.write("              end\n")
        self.vf.write("            end\n")
        self.vf.write("          end\n")
        self.vf.write("          // Check if current request is hit\n")
        self.vf.write("          // Compare all ways' tags to find a hit. Since each way has a different\n")
        self.vf.write("          // tag, only one of them can match at most.\n")
        self.vf.write("          for (var_0 = 0; var_0 < WAY_DEPTH; var_0 = var_0 + 1)\n")

        lines = "tag_read_dout[var_0 * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && tag_read_dout[var_0 * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag"
        lines = self.wrap_data_hazard(lines)

        self.vf.write("            if ({}) begin\n".format(lines))
        self.vf.write("              // Set main memory's csb to 1 again since it could be set 0 above\n")
        self.vf.write("              main_csb = 1;\n")
        self.vf.write("              // Perform the write request\n")
        self.vf.write("              if (!web_reg) begin\n")
        self.vf.write("                tag_write_csb   = 0;\n")
        self.vf.write("                tag_write_addr  = set;\n")
        self.vf.write("                data_write_csb  = 0;\n")
        self.vf.write("                data_write_addr = set;\n")

        lines = [
            "tag_write_din  = tag_read_dout;",
            "data_write_din = data_read_dout;"
        ]
        lines = self.wrap_data_hazard(lines, indent=8)

        self.vf.writelines(lines)
        self.vf.write("                // Update dirty bit in the tag line\n")
        self.vf.write("                tag_write_din[var_0 * (2 + TAG_WIDTH) + TAG_WIDTH] = 1;\n")
        self.vf.write("                // Overwrite the word\n")
        self.vf.write("                for (var_1 = 0; var_1 < WORD_WIDTH; var_1 = var_1 + 1)\n")
        self.vf.write("                  data_write_din[var_0 * LINE_WIDTH + offset * WORD_WIDTH + var_1] = din_reg[var_1];\n")
        self.vf.write("              end\n")
        self.vf.write("              // If CPU is sending a new request, read next lines from SRAMs.\n")
        self.vf.write("              // Even if bypass registers are going to be used, read requests\n")
        self.vf.write("              // are sent to SRAMs since read is non-destructive (hopefully?).\n")
        self.vf.write("              if (!csb) begin\n")
        self.vf.write("                tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("                data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("              end\n")
        self.vf.write("            end\n")
        self.vf.write("        end\n")

        # WRITE state
        self.vf.write("        // In the WRITE state, cache waits for main memory to be\n")
        self.vf.write("        // available.\n")
        self.vf.write("        // When main memory is available, write request is sent.\n")
        self.vf.write("        WRITE: begin\n")
        self.vf.write("          // If main memory is busy, wait in this state.\n")
        self.vf.write("          //\n")
        self.vf.write("          // If main memory is available, switch to WAIT_WRITE and\n")
        self.vf.write("          // wait for main memory to complete writing.\n")
        self.vf.write("          tag_read_addr  = set;\n")
        self.vf.write("          data_read_addr = set;\n")
        self.vf.write("          if (!main_stall) begin\n")
        self.vf.write("            main_csb  = 0;\n")
        self.vf.write("            main_web  = 0;\n")
        self.vf.write("            main_addr = {tag_read_dout[way * (TAG_WIDTH + 2) +: TAG_WIDTH], set};\n")
        self.vf.write("            main_din  = data_read_dout[way * LINE_WIDTH +: LINE_WIDTH];\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n\n")

        # WAIT_WRITE state
        self.vf.write("        // In the WAIT_WRITE state, cache waits for main memory to\n")
        self.vf.write("        // complete writing.\n")
        self.vf.write("        // When main memory completes writing, read request is sent.\n")
        self.vf.write("        WAIT_WRITE: begin\n")
        self.vf.write("          // If main memory is busy, wait in this state.\n")
        self.vf.write("          //\n")
        self.vf.write("          // If main memory completes writing, switch to WAIT_READ\n")
        self.vf.write("          // and wait for main memory to complete reading.\n")
        self.vf.write("          tag_read_addr  = set;\n")
        self.vf.write("          data_read_addr = set;\n")
        self.vf.write("          if (!main_stall) begin\n")
        self.vf.write("            main_csb  = 0;\n")
        self.vf.write("            main_addr = {tag, set};\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n\n")

        # READ state
        # TODO: Is this state really necessary? WAIT_WRITE state may be used instead.
        self.vf.write("        // In the READ state, cache waits for main memory to be\n")
        self.vf.write("        // available.\n")
        self.vf.write("        // When main memory is available, read request is sent.\n")
        self.vf.write("        READ: begin\n")
        self.vf.write("          // If main memory is busy, wait in this state.\n")
        self.vf.write("          //\n")
        self.vf.write("          // If main memory completes writing, switch to WAIT_READ\n")
        self.vf.write("          // and wait for main memory to complete reading.\n")
        self.vf.write("          tag_read_addr  = set;\n")
        self.vf.write("          data_read_addr = set;\n")
        self.vf.write("          if (!main_stall) begin\n")
        self.vf.write("            main_csb  = 0;\n")
        self.vf.write("            main_addr = {tag, set};\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n\n")

        # WAIT_READ state
        self.vf.write("        // In the WAIT_READ state, cache waits for main memory to\n")
        self.vf.write("        // complete reading.\n")
        self.vf.write("        // When main memory completes reading, request is completed.\n")
        self.vf.write("        WAIT_READ: begin\n")
        self.vf.write("          tag_read_addr  = set;\n")
        self.vf.write("          data_read_addr = set;\n")
        self.vf.write("          // If main memory is busy, wait in this state.\n")
        self.vf.write("          //\n")
        self.vf.write("          // If main memory completes reading, cache switches to:\n")
        self.vf.write("          //   IDLE    if CPU isn't sending a new request\n")
        self.vf.write("          //   COMPARE if CPU is sending a new request\n")
        self.vf.write("          if (!main_stall) begin\n")
        self.vf.write("            // TODO: Use wmask feature of OpenRAM\n")
        self.vf.write("            tag_write_csb  = 0;\n")
        self.vf.write("            tag_write_addr = set;\n")
        self.vf.write("            tag_write_din  = tag_read_dout;\n")
        self.vf.write("            tag_write_din[way * (2 + TAG_WIDTH) + TAG_WIDTH + 1] = 1;\n")
        self.vf.write("            tag_write_din[way * (2 + TAG_WIDTH) + TAG_WIDTH]     = ~web_reg;\n")
        self.vf.write("            for (var_0 = 0; var_0 < TAG_WIDTH; var_0 = var_0 + 1)\n")
        self.vf.write("              tag_write_din[way * (2 + TAG_WIDTH) + var_0] = tag[var_0];\n")
        self.vf.write("            data_write_csb  = 0;\n")
        self.vf.write("            data_write_addr = set;\n")
        self.vf.write("            data_write_din  = data_read_dout;\n")
        self.vf.write("            for (var_0 = 0; var_0 < LINE_WIDTH; var_0 = var_0 + 1)\n")
        self.vf.write("              data_write_din[way * LINE_WIDTH + var_0] = main_dout[var_0];\n")
        self.vf.write("            // Perform the write request\n")
        self.vf.write("            if (!web_reg)\n")
        self.vf.write("              for (var_0 = 0; var_0 < WORD_WIDTH; var_0 = var_0 + 1)\n")
        self.vf.write("                data_write_din[way * LINE_WIDTH + offset * WORD_WIDTH + var_0] = din_reg[var_0];\n")
        self.vf.write("            // If CPU is sending a new request, read next lines from SRAMs\n")
        self.vf.write("            // Even if bypass registers are going to be used, read requests\n")
        self.vf.write("            // are sent to SRAMs since read is non-destructive (hopefully?).\n")
        self.vf.write("            if (!csb) begin\n")
        self.vf.write("              tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("              data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("            end\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n\n")

        self.vf.write("        default: begin\n")
        self.vf.write("          main_csb        = 1;\n")
        self.vf.write("          main_web        = 1;\n")
        self.vf.write("          main_addr       = 0;\n")
        self.vf.write("          main_din        = 0;\n")
        self.vf.write("          tag_read_csb    = 0;\n")
        self.vf.write("          tag_read_addr   = 0;\n")
        self.vf.write("          tag_write_csb   = 1;\n")
        self.vf.write("          tag_write_addr  = 0;\n")
        self.vf.write("          tag_write_din   = 0;\n")
        self.vf.write("          data_read_csb   = 0;\n")
        self.vf.write("          data_read_addr  = 0;\n")
        self.vf.write("          data_write_csb  = 1;\n")
        self.vf.write("          data_write_addr = 0;\n")
        self.vf.write("          data_write_din  = 0;\n")
        self.vf.write("        end\n\n")

        self.vf.write("      endcase\n")
        self.vf.write("    end\n\n")
        self.vf.write("  end\n\n\n")


    def write_state_block(self):
        """ Write the state controller always block. """

        title = "State Controller Block"
        descr = "In this block, cache's state is controlled. state flip-flop " + \
                "register is changed in order to switch between states."

        self.write_title_banner(title, descr, indent=1)
        self.vf.write("  always @* begin\n")
        self.vf.write("    state_next = state;\n\n")

        self.vf.write("    // If rst is high, state switches to RESET.\n")
        self.vf.write("    if (rst) begin\n")
        self.vf.write("      state_next = RESET;\n")
        self.vf.write("    end\n\n")

        self.vf.write("    // If flush is high, state switches to FLUSH.\n")
        self.vf.write("    else if (flush) begin\n")
        self.vf.write("      state_next = FLUSH;\n")
        self.vf.write("    end\n\n")

        self.vf.write("    else begin\n")
        self.vf.write("      case (state)\n\n")

        # RESET state
        self.vf.write("        // In the RESET state, state switches to IDLE if reset is completed.\n")
        self.vf.write("        RESET: begin\n")
        self.vf.write("          // When set reaches the limit, the last write request to the\n")
        self.vf.write("          // tag array is sent.\n")
        self.vf.write("          if (set == CACHE_DEPTH - 1)\n")
        self.vf.write("            state_next = IDLE;\n")
        self.vf.write("        end\n\n")

        # FLUSH state
        self.vf.write("        // In the FLUSH state, state switches to IDLE if flush is completed.\n")
        self.vf.write("        FLUSH: begin\n")
        self.vf.write("          // If main memory completes the last write request, flush is\n")
        self.vf.write("          // completed.\n")
        self.vf.write("          if (!main_stall && way == WAY_DEPTH - 1 && set == CACHE_DEPTH - 1)\n")
        self.vf.write("            state_next = IDLE;\n")
        self.vf.write("        end\n\n")

        # IDLE state
        self.vf.write("        // In the IDLE state, state switches to COMPARE if CPU is sending\n")
        self.vf.write("        // a new request.\n")
        self.vf.write("        IDLE: begin\n")
        self.vf.write("          if (!csb)\n")
        self.vf.write("            state_next = COMPARE;\n")
        self.vf.write("        end\n\n")

        # COMPARE state
        self.vf.write("        // In the COMPARE state, state switches to:\n")
        self.vf.write("        //   IDLE       if current request is hit and CPU isn't sending a new request\n")
        self.vf.write("        //   COMPARE    if current request is hit and CPU is sending a new request\n")
        self.vf.write("        //   WRITE      if current request is dirty miss and main memory is busy\n")
        self.vf.write("        //   WAIT_WRITE if current request is dirty miss and main memory is available\n")
        self.vf.write("        //   READ       if current request is clean miss and main memory is busy\n")
        self.vf.write("        //   WAIT_READ  if current request is clean miss and main memory is available\n")
        self.vf.write("        COMPARE: begin\n")
        self.vf.write("          // Find the least recently used way (the way having 0 LRU number)\n")
        self.vf.write("          for (var_3 = 0; var_3 < WAY_DEPTH; var_3 = var_3 + 1) begin\n")

        lines = "!lru_read_dout[var_3 * WAY_WIDTH +: WAY_WIDTH]"
        lines = self.wrap_data_hazard(lines)

        self.vf.write("            if ({}) begin\n".format(lines))
        self.vf.write("            // Assuming that current request is miss, check if it is a dirty miss\n")

        lines = "tag_read_dout[var_3 * (TAG_WIDTH + 2) + TAG_WIDTH +: 2] == 2'b11"
        lines = self.wrap_data_hazard(lines)

        self.vf.write("              if ({})\n".format(lines))
        self.vf.write("                state_next = main_stall ? WRITE : WAIT_WRITE;\n")
        self.vf.write("              // Else (Assuming that current request is miss, it is a clean miss)\n")
        self.vf.write("              else\n")
        self.vf.write("                state_next = main_stall ? READ : WAIT_READ;\n")
        self.vf.write("            end\n")
        self.vf.write("          end\n")
        self.vf.write("          // Find the least recently used way (the way having 0 LRU number)\n")
        self.vf.write("          // Hit is checked here in order to prevent bugs where hit way's var_3\n")
        self.vf.write("          // value is smaller than least recently used way's var_3 value.\n")
        self.vf.write("          // TODO: This should be optimized.\n")
        self.vf.write("          for (var_3 = 0; var_3 < WAY_DEPTH; var_3 = var_3 + 1) begin\n")

        lines = "tag_read_dout[var_3 * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && tag_read_dout[var_3 * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag"
        lines = self.wrap_data_hazard(lines)

        self.vf.write("            if ({})\n".format(lines))
        self.vf.write("              state_next = csb ? IDLE : COMPARE;\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n\n")

        # WRITE state
        self.vf.write("        // In the WRITE state, state switches to:\n")
        self.vf.write("        //   WRITE      if main memory didn't respond yet\n")
        self.vf.write("        //   WAIT_WRITE if main memory responded\n")
        self.vf.write("        WRITE: begin\n")
        self.vf.write("          if (!main_stall)\n")
        self.vf.write("            state_next = WAIT_WRITE;\n")
        self.vf.write("        end\n\n")

        # WAIT_WRITE state
        self.vf.write("        // In the WAIT_WRITE state, state switches to:\n")
        self.vf.write("        //   WAIT_WRITE if main memory didn't respond yet\n")
        self.vf.write("        //   WAIT_READ  if main memory responded\n")
        self.vf.write("        WAIT_WRITE: begin\n")
        self.vf.write("          if (!main_stall)\n")
        self.vf.write("            state_next = WAIT_READ;\n")
        self.vf.write("        end\n\n")

        # READ state
        self.vf.write("        // In the READ state, state switches to:\n")
        self.vf.write("        //   READ      if main memory didn't respond yet\n")
        self.vf.write("        //   WAIT_READ if main memory responded\n")
        self.vf.write("        READ: begin\n")
        self.vf.write("          if (!main_stall)\n")
        self.vf.write("            state_next = WAIT_READ;\n")
        self.vf.write("        end\n\n")

        # WAIT_READ state
        self.vf.write("        // In the WAIT_READ state, state switches to:\n")
        self.vf.write("        //   IDLE    if CPU isn't sending a request\n")
        self.vf.write("        //   COMPARE if CPU is sending a request\n")
        self.vf.write("        WAIT_READ: begin\n")
        self.vf.write("          if (!main_stall)\n")
        self.vf.write("            state_next = csb ? IDLE : COMPARE;\n")
        self.vf.write("        end\n\n")

        self.vf.write("        default: state_next = state;\n\n")

        self.vf.write("      endcase\n")
        self.vf.write("    end\n\n")
        self.vf.write("  end\n\n\n")


    def write_request_block(self):
        """ Write the request decode always block. """

        title = "Request Decode Block"
        descr = "In this block, CPU's request is decoded. Address is parsed into " + \
                "tag, set and offset values, and write enable and data input are " + \
                "saved in registers."

        self.write_title_banner(title, descr, indent=1)
        self.vf.write("  always @* begin\n")
        self.vf.write("    tag_next     = tag;\n")
        self.vf.write("    set_next     = set;\n")
        self.vf.write("    offset_next  = offset;\n")
        self.vf.write("    web_reg_next = web_reg;\n")
        self.vf.write("    din_reg_next = din_reg;\n\n")

        self.vf.write("    // If rst is high, input registers are reset.\n")
        self.vf.write("    // set register becomes 1 since it is going to be used to reset all\n")
        self.vf.write("    // lines in the tag_array.\n")
        self.vf.write("    // way register becomes 0 since it is going to be used to reset all\n")
        self.vf.write("    // ways in a tag line.\n")
        self.vf.write("    if (rst) begin \n")
        self.vf.write("      tag_next     = 0;\n")
        self.vf.write("      set_next     = 1;\n")
        self.vf.write("      offset_next  = 0;\n")
        self.vf.write("      web_reg_next = 1;\n")
        self.vf.write("      din_reg_next = 0;\n")
        self.vf.write("    end\n\n")

        self.vf.write("    // If flush is high, input registers are not reset.\n")
        self.vf.write("    // However, way and set registers becomes 0 since it is going\n")
        self.vf.write("    // to be used to write dirty lines back to main memory.\n")
        self.vf.write("    else if (flush) begin\n")
        self.vf.write("      set_next = 0;\n")
        self.vf.write("    end\n\n")

        self.vf.write("    else begin\n")
        self.vf.write("      case (state)\n\n")

        # RESET state
        self.vf.write("        // In the RESET state, set register is used to reset all lines in\n")
        self.vf.write("        // the tag_array.\n")
        self.vf.write("        RESET: begin\n")
        self.vf.write("          set_next = set + 1;\n")
        self.vf.write("        end\n\n")

        # FLUSH state
        self.vf.write("        // In the FLUSH state, set register is used to write all dirty lines\n")
        self.vf.write("        // back to main memory.\n")
        self.vf.write("        FLUSH: begin\n")
        self.vf.write("          if (!main_stall && way == WAY_DEPTH - 1)\n")
        self.vf.write("            set_next = set + 1;\n")
        self.vf.write("        end\n\n")

        # IDLE, COMPARE, and WAIT_READ states
        self.vf.write("        // The request is decoded when needed. Check if:\n")
        self.vf.write("        //   CPU is sending a request and either:\n")
        self.vf.write("        //     state is IDLE\n")
        self.vf.write("        //     state is COMPARE and current request is hit\n")
        self.vf.write("        //     state is WAIT_READ and main memory answered the read request\n")
        self.vf.write("        default: begin\n")
        self.vf.write("          if (!csb) begin\n")
        self.vf.write("            for (var_4 = 0; var_4 < WAY_DEPTH; var_4 = var_4 + 1) begin\n")
        self.vf.write("              if ((state == IDLE)\n")

        lines = "tag_read_dout[var_4 * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && tag_read_dout[var_4 * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag"
        lines = self.wrap_data_hazard(lines)

        self.vf.write("              || (state == COMPARE && ({}))\n".format(lines))
        self.vf.write("              || (state == WAIT_READ && !main_stall))\n")
        self.vf.write("              begin\n")
        self.vf.write("                tag_next     = addr[ADDR_WIDTH-1 -: TAG_WIDTH];\n")
        self.vf.write("                set_next     = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("                offset_next  = addr[OFFSET_WIDTH-1:0];\n")
        self.vf.write("                web_reg_next = web;\n")
        self.vf.write("                din_reg_next = din;\n")
        self.vf.write("              end\n")
        self.vf.write("            end\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n\n")

        self.vf.write("      endcase\n")
        self.vf.write("    end\n\n")
        self.vf.write("  end\n\n\n")


    def write_output_block(self):
        """ Write the stall always block. """

        title = "Output Block"
        descr = "In this block, cache's output signals, which are stall and dout, " + \
                "are controlled."

        self.write_title_banner(title, descr, indent=1)
        self.vf.write("  always @* begin\n")
        self.vf.write("    stall = 1;\n")
        self.vf.write("    dout  = 'bx;\n\n")

        self.vf.write("    case (state)\n\n")

        # RESET state
        self.vf.write("      // In the RESET state, stall is low if reset is completed.\n")
        self.vf.write("      RESET: begin\n")
        self.vf.write("        // When set reaches the limit, the last write request to the\n")
        self.vf.write("        // tag_array is sent.\n")
        self.vf.write("        stall = set != CACHE_DEPTH - 1;\n")
        self.vf.write("      end\n\n")

        # FLUSH state
        self.vf.write("      // In the FLUSH state, stall is low if flush is completed.\n")
        self.vf.write("      FLUSH: begin\n")
        self.vf.write("        // If main memory completes the last write request, stall is low.\n")
        self.vf.write("        // The line below is the inverse of:\n")
        self.vf.write("        //   !main_stall && way == WAY_DEPTH - 1 && set == CACHE_DEPTH - 1\n")
        self.vf.write("        stall = main_stall || way != WAY_DEPTH - 1 || set != CACHE_DEPTH - 1;\n")
        self.vf.write("      end\n\n")

        # IDLE state
        self.vf.write("      // In the IDLE state, stall is low while there is no request from\n")
        self.vf.write("      // the CPU.\n")
        self.vf.write("      IDLE: begin\n")
        self.vf.write("        stall = !csb;\n")
        self.vf.write("      end\n\n")

        # COMPARE state
        self.vf.write("      // In the COMPARE state, stall is low if the current request is hit.\n")
        self.vf.write("      //\n")
        self.vf.write("      // Data output is valid if the request is hit and even if the current\n")
        self.vf.write("      // request is write since read is non-destructive.\n")
        self.vf.write("      COMPARE: begin\n")
        self.vf.write("        // Check if current request is hit\n")
        self.vf.write("        for (var_5 = 0; var_5 < WAY_DEPTH; var_5 = var_5 + 1) begin\n")

        lines = "tag_read_dout[var_5 * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && tag_read_dout[var_5 * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag"
        lines = self.wrap_data_hazard(lines)

        self.vf.write("          if ({}) begin\n".format(lines))
        self.vf.write("            stall = 0;\n")

        lines = ["dout = data_read_dout[var_5 * LINE_WIDTH + offset * WORD_WIDTH +: WORD_WIDTH];"]
        lines = self.wrap_data_hazard(lines, indent=6)

        self.vf.writelines(lines)
        self.vf.write("          end\n")
        self.vf.write("        end\n")
        self.vf.write("      end\n\n")

        # WAIT_READ state
        self.vf.write("      // In the WAIT_READ state, stall is low and data output is valid main\n")
        self.vf.write("      // memory answers the read request.\n")
        self.vf.write("      //\n")
        self.vf.write("      // Data output is valid even if the current request is write since read\n")
        self.vf.write("      // is non-destructive.\n")
        self.vf.write("      //\n")
        self.vf.write("      // Note:\n")
        self.vf.write("      // No need to use bypass registers here since data hazard is not\n")
        self.vf.write("      // possible.\n")
        self.vf.write("      WAIT_READ: begin\n")
        self.vf.write("        // Check if main memory answers to the read request.\n")
        self.vf.write("        if (!main_stall) begin\n")
        self.vf.write("          stall = 0;\n")
        self.vf.write("          dout  = main_dout[offset * WORD_WIDTH +: WORD_WIDTH];\n")
        self.vf.write("        end\n")
        self.vf.write("      end\n\n")

        self.vf.write("      default: begin\n")
        self.vf.write("        stall = 1;\n")
        self.vf.write("        dout  = 'bx;\n")
        self.vf.write("      end\n\n")

        self.vf.write("    endcase\n\n")
        self.vf.write("  end\n\n\n")


    def write_replacement_block(self):
        """ Write the replacement always block. """

        title = "Replacement Block"
        descr = "In this block, LRU numbers are updated and evicted way is " + \
                "selected according to LRU replacement policy."

        self.write_title_banner(title, descr, indent=1)
        self.vf.write("  always @* begin\n")
        self.vf.write("    way_next       = way;\n")
        self.vf.write("    lru_read_csb   = 0;\n")
        self.vf.write("    lru_read_addr  = 0;\n")
        self.vf.write("    lru_write_csb  = 1;\n")
        self.vf.write("    lru_write_addr = 0;\n")
        self.vf.write("    lru_write_din  = 0;\n\n")

        self.vf.write("    // If rst is high, way is reset and LRU numbers are reset.\n")
        self.vf.write("    // way register becomes 0 since it is going to be used to reset all\n")
        self.vf.write("    // ways in LRU and tag lines.\n")
        self.vf.write("    if (rst) begin\n")
        self.vf.write("      way_next       = 0;\n")
        self.vf.write("      lru_write_csb  = 0;\n")
        self.vf.write("      lru_write_addr = 0;\n")
        self.vf.write("      lru_write_din  = 0;\n")
        self.vf.write("    end\n\n")

        self.vf.write("    // If flush is high, way is reset.\n")
        self.vf.write("    // way register becomes 0 since it is going to be used to write all\n")
        self.vf.write("    // data lines back to main memory.\n")
        self.vf.write("    else if (flush) begin \n")
        self.vf.write("      way_next = 0;\n")
        self.vf.write("    end\n\n")

        self.vf.write("    else begin\n")
        self.vf.write("      case (state)\n\n")

        # RESET state
        self.vf.write("        // In the RESET state, way register is used to reset all ways in LRU\n")
        self.vf.write("        // and tag lines.\n")
        self.vf.write("        RESET: begin\n")
        self.vf.write("          lru_write_csb  = 0;\n")
        self.vf.write("          lru_write_addr = set;\n")
        self.vf.write("          lru_write_din  = 0;\n")
        self.vf.write("        end\n\n")

        # FLUSH state
        self.vf.write("        // In the FLUSH state, way register is used to write all data lines\n")
        self.vf.write("        // back to main memory.\n")
        self.vf.write("        // TODO: Flush should only write dirty lines back.\n")
        self.vf.write("        FLUSH: begin\n")
        self.vf.write("          if (!main_stall)\n")
        self.vf.write("            way_next = way + 1;\n")
        self.vf.write("        end\n\n")

        # IDLE state
        self.vf.write("        // In the IDLE state, way is reset and the corresponding line from the\n")
        self.vf.write("        // LRU array is requested.\n")
        self.vf.write("        IDLE: begin\n")
        self.vf.write("          if (!csb) begin\n")
        self.vf.write("            way_next      = 0;\n")
        self.vf.write("            lru_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n\n")

        # COMPARE state
        self.vf.write("        // In the COMPARE state, way is selected according to the replacement\n")
        self.vf.write("        // policy of the cache.\n")
        self.vf.write("        // Also LRU numbers are updated if current request is hit.\n")
        self.vf.write("        COMPARE: begin\n")
        self.vf.write("          for (var_9 = 0; var_9 < WAY_DEPTH; var_9 = var_9 + 1) begin\n")
        self.vf.write("            // Find the least recently used way (the way having 0 LRU number)\n")

        lines = "!lru_read_dout[var_9 * WAY_WIDTH +: WAY_WIDTH]"
        lines = self.wrap_data_hazard(lines)

        self.vf.write("            if ({}) begin\n".format(lines))
        self.vf.write("              way_next = var_9;\n")
        self.vf.write("              // Check if current request is a clean miss\n")

        lines = "tag_read_dout[var_9 * (TAG_WIDTH + 2) + TAG_WIDTH +: 2] == 2'b11"
        lines = self.wrap_data_hazard(lines)

        self.vf.write("              if (!({})) begin\n".format(lines))
        self.vf.write("                if (!main_stall) begin\n")
        self.vf.write("                  lru_read_addr = set;\n")
        self.vf.write("                end\n")
        self.vf.write("              end\n")
        self.vf.write("            end\n")
        self.vf.write("          end\n")
        self.vf.write("          // Check if current request is a hit\n")
        self.vf.write("          for (var_9 = 0; var_9 < WAY_DEPTH; var_9 = var_9 + 1) begin\n")

        lines = "tag_read_dout[var_9 * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && tag_read_dout[var_9 * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag"
        lines = self.wrap_data_hazard(lines)

        self.vf.write("            if ({}) begin\n".format(lines))
        self.vf.write("              lru_write_csb  = 0;\n")
        self.vf.write("              lru_write_addr = set;\n")
        self.vf.write("              // Each way in a set has its own LRU numbers. These numbers\n")
        self.vf.write("              // start from 0. Every time a way is needed to be evicted,\n")
        self.vf.write("              // the way having 0 LRU number is chosen.\n")
        self.vf.write("              //\n")
        self.vf.write("              // Every time a way is accessed (read or write), its corresponding\n")
        self.vf.write("              // LRU number is increased to the maximum value and other ways which\n")
        self.vf.write("              // have LRU numbers more than accessed way's LRU number are decremented\n")
        self.vf.write("              // by 1.\n")

        if self.data_hazard:
            self.vf.write("              if (bypass) begin\n")
            self.write_lru_update(8, True, False, "var_9", for_var="var_10")
            self.vf.write("                  end else begin\n")
            self.write_lru_update(8, False, False, "var_9", for_var="var_10")
            self.vf.write("                  end\n")
        else:
            self.write_lru_update(7, False, False, "var_9", for_var="var_10")

        self.vf.write("              if (!csb) begin\n")
        self.vf.write("                lru_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("              end\n")
        self.vf.write("            end\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n\n")

        # WAIT_WRITE and READ states
        self.vf.write("        // In the WAIT_WRITE and READ states, LRU line is read to update it\n")
        self.vf.write("        // in the WAIT_READ state.\n")
        self.vf.write("        WAIT_WRITE, READ: begin\n")
        self.vf.write("          lru_read_addr = set;\n")
        self.vf.write("        end\n\n")

        # WAIT_READ state
        self.vf.write("        // In the WAIT_READ state, LRU numbers are updated.\n")
        self.vf.write("        WAIT_READ: begin\n")
        self.vf.write("          lru_read_addr = set;\n")
        self.vf.write("          if (!main_stall) begin // Switch to COMPARE\n")
        self.vf.write("            // Each way in a set has its own LRU numbers. These numbers\n")
        self.vf.write("            // start from 0. Every time a way is needed to be evicted,\n")
        self.vf.write("            // the way having 0 LRU number is chosen.\n")
        self.vf.write("            //\n")
        self.vf.write("            // Every time a way is accessed (read or write), its corresponding\n")
        self.vf.write("            // LRU number is increased to the maximum value and other ways which\n")
        self.vf.write("            // have LRU numbers more than accessed way's LRU number are decremented\n")
        self.vf.write("            // by 1.\n")
        self.vf.write("            lru_write_csb  = 0;\n")
        self.vf.write("            lru_write_addr = set;\n")
        self.write_lru_update(6, False, False, for_var="var_10")
        self.vf.write("            if (!csb)\n")
        self.vf.write("              lru_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n\n")

        self.vf.write("        default: begin\n")
        self.vf.write("          way_next       = way;\n")
        self.vf.write("          lru_read_csb   = 0;\n")
        self.vf.write("          lru_read_addr  = 0;\n")
        self.vf.write("          lru_write_csb  = 1;\n")
        self.vf.write("          lru_write_addr = 0;\n")
        self.vf.write("          lru_write_din  = 0;\n")
        self.vf.write("        end\n\n")

        self.vf.write("      endcase\n")
        self.vf.write("    end\n\n")
        self.vf.write("  end\n\n\n")


    def write_bypass_block(self):
        """ Write the bypass register always block. """

        title = "Bypass Register Block"
        descr = "In this block, bypass registers are controlled. Bypass registers are " + \
                "used to prevent data hazard from SRAMs. Data hazard can occur when " + \
                "there are read and write requests to the same row at the same cycle."

        self.write_title_banner(title, descr, indent=1)
        self.vf.write("  always @* begin\n")
        self.vf.write("    bypass_next   = 0;\n")
        self.vf.write("    new_lru_next  = 0;\n")
        self.vf.write("    new_tag_next  = 0;\n")
        self.vf.write("    new_data_next = 0;\n\n")

        self.vf.write("    case (state)\n\n")

        # COMPARE state
        self.vf.write("      // In the COMPARE state, bypass registers can be used in the next\n")
        self.vf.write("      // cycle if the current request is hit.\n")
        self.vf.write("      //\n")
        self.vf.write("      // Otherwise, bypass registers won't probably be used; therefore,\n")
        self.vf.write("      // will be reset.\n")
        self.vf.write("      COMPARE: begin\n")
        self.vf.write("        new_lru_next  = 0;\n")
        self.vf.write("        new_tag_next  = 0;\n")
        self.vf.write("        new_data_next = 0;\n")
        self.vf.write("        // Check if:\n")
        self.vf.write("        //   CPU is sending a new request\n")
        self.vf.write("        //   Current request is hit\n")
        self.vf.write("        //   Next address is in the same set\n")
        self.vf.write("        if (!csb) begin\n")
        self.vf.write("          for (var_6 = 0; var_6 < WAY_DEPTH; var_6 = var_6 + 1) begin\n")
        self.vf.write("            if (((bypass && new_tag[var_6 * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && new_tag[var_6 * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag) || (!bypass && tag_read_dout[var_6 * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && tag_read_dout[var_6 * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag))\n")
        self.vf.write("            && addr[OFFSET_WIDTH +: SET_WIDTH] == set)\n")
        self.vf.write("            begin\n")
        self.vf.write("              bypass_next = 1;\n")
        self.vf.write("              if (bypass) begin\n")
        self.write_lru_update(8, True, True, "var_6", "var_8")
        self.vf.write("                new_tag_next  = new_tag;\n")
        self.vf.write("                new_data_next = new_data;\n")
        self.vf.write("              end else begin\n")
        self.write_lru_update(8, False, True, "var_6", "var_8")
        self.vf.write("                new_tag_next  = tag_read_dout;\n")
        self.vf.write("                new_data_next = data_read_dout;\n")
        self.vf.write("              end\n")
        self.vf.write("              new_tag_next[var_6 * (2 + TAG_WIDTH) + TAG_WIDTH] = 1;\n")
        self.vf.write("              for (var_7 = 0; var_7 < WORD_WIDTH; var_7 = var_7 + 1)\n")
        self.vf.write("                new_data_next[var_6 * LINE_WIDTH + offset * WORD_WIDTH + var_7] = din_reg[var_7];\n")
        self.vf.write("            end\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n")
        self.vf.write("      end\n\n")

        # WAIT_READ state
        self.vf.write("      // In the WAIT_READ state, bypass registers will be used in the next\n")
        self.vf.write("      // cycle if the next request is in the same set.\n")
        self.vf.write("      //\n")
        self.vf.write("      // Otherwise, bypass registers won't probably be used; therefore,\n")
        self.vf.write("      // will be reset.\n")
        self.vf.write("      //\n")
        self.vf.write("      // Note:\n")
        self.vf.write("      // No need to use bypass registers here since data hazard is not\n")
        self.vf.write("      // possible.\n")
        self.vf.write("      WAIT_READ: begin\n")
        self.vf.write("        // Main memory is answering to the read request\n")
        self.vf.write("        if (!main_stall) begin\n")
        self.vf.write("          new_lru_next  = 0;\n")
        self.vf.write("          new_tag_next  = 0;\n")
        self.vf.write("          new_data_next = 0;\n")
        self.vf.write("          // Check if:\n")
        self.vf.write("          //   CPU is sending a new request\n")
        self.vf.write("          //   Next address is in the same set\n")
        self.vf.write("          if (!csb && addr[OFFSET_WIDTH +: SET_WIDTH] == set) begin\n")
        self.vf.write("            bypass_next = 1;\n")
        self.write_lru_update(6, False, True, for_var="var_6")
        self.vf.write("            new_tag_next     = tag_read_dout;\n")
        self.vf.write("            new_tag_next[way * (2 + TAG_WIDTH) + TAG_WIDTH + 1] = 1;\n")
        self.vf.write("            new_tag_next[way * (2 + TAG_WIDTH) + TAG_WIDTH]     = ~web_reg;\n")
        self.vf.write("            for (var_6 = 0; var_6 < TAG_WIDTH; var_6 = var_6 + 1)\n")
        self.vf.write("              new_tag_next[way * (2 + TAG_WIDTH) + var_6] = tag[var_6];\n")
        self.vf.write("            new_data_next = data_read_dout;\n")
        self.vf.write("            for (var_6 = 0; var_6 < LINE_WIDTH; var_6 = var_6 + 1)\n")
        self.vf.write("              new_data_next[way * LINE_WIDTH + var_6] = main_dout[var_6];\n")
        self.vf.write("            // Perform the write request\n")
        self.vf.write("            if (!web_reg) begin\n")
        self.vf.write("              for (var_6 = 0; var_6 < WORD_WIDTH; var_6 = var_6 + 1)\n")
        self.vf.write("                new_data_next[way * LINE_WIDTH + offset * WORD_WIDTH + var_6]  = din_reg[var_6];\n")
        self.vf.write("            end\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n")
        self.vf.write("      end\n\n")

        self.vf.write("      default: begin\n")
        self.vf.write("        bypass_next   = 0;\n")
        self.vf.write("        new_lru_next  = 0;\n")
        self.vf.write("        new_tag_next  = 0;\n")
        self.vf.write("        new_data_next = 0;\n")
        self.vf.write("      end\n\n")

        self.vf.write("    endcase\n\n")
        self.vf.write("  end\n\n\n")


    def write_lru_update(self, base_indent, data_hazard, update_bypass_regs, way_var="way", for_var="?"):
        """ Write a multiplexer to update LRU bits of the cache. """

        if type(base_indent) == int:
            base_indent *= "  "

        if data_hazard:
            rhs = "new_lru"
        else:
            rhs = "lru_read_dout"

        if update_bypass_regs:
            lhs = "new_lru_next"
        else:
            lhs = "lru_write_din"

        for i in range(self.num_ways):
            lsb = i * self.way_size
            self.vf.write(base_indent + "{0}[{1}:{2}] = {3}[{1}:{2}] - ({3}[{1}:{2}] > {3}[{4} * WAY_WIDTH +: WAY_WIDTH]);\n".format(lhs,
                                                                                                                                     lsb + self.way_size - 1,
                                                                                                                                     lsb,
                                                                                                                                     rhs,
                                                                                                                                     way_var))

        self.vf.write(base_indent + "for ({0} = 0; {0} < WAY_WIDTH; {0} = {0} + 1)\n".format(for_var))
        self.vf.write(base_indent + "  {0}[{1} * WAY_WIDTH + {2}] = WAY_LIMIT[{2}];\n".format(lhs, way_var, for_var))