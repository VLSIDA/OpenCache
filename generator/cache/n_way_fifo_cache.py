# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from cache_base import cache_base


class n_way_fifo_cache(cache_base):
    """
    This is the design module of N-way set associative cache
    with FIFO replacement policy.
    """
    def __init__(self, name, cache_config):

        super().__init__(name, cache_config)


    def config_write(self, config_path):
        """ Write the configuration files for OpenRAM SRAM arrays. """

        super().config_write(config_path)

        self.fcf = open(config_path + "_fifo_array_config.py", "w")
        self.fcf.write("word_size = {}\n".format(self.way_size))
        self.fcf.write("num_words = {}\n".format(self.num_rows))
        # OpenRAM outputs of the FIFO array are saved to a separate folder
        self.fcf.write("output_path = \"{}/fifo_array\"\n".format(config_path))
        self.fcf.write("output_name = \"{}_fifo_array\"\n".format(self.name))
        self.fcf.close()


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
        # No need for bypass registers if SRAMs are guaranteed to be data hazard proof
        if self.data_hazard:
            self.vf.write("  // When the next fetch is in the same set, tag_array and data_array might be old (data hazard).\n")
            self.vf.write("  reg data_hazard, data_hazard_next;                             // high when bypass registers are used\n")
            self.vf.write("  reg [WAY_WIDTH-1:0]                   new_fifo, new_fifo_next; // new FIFO bits from the previous cycle\n")
            self.vf.write("  reg [(2 + TAG_WIDTH) * WAY_DEPTH-1:0] new_tag, new_tag_next;   // new tag line from the previous cycle\n")
            self.vf.write("  reg [LINE_WIDTH * WAY_DEPTH-1:0]      new_data, new_data_next; // new data line from the previous cycle\n\n")

        self.vf.write("  // Main memory ports\n")
        self.vf.write("  reg main_csb;\n")
        self.vf.write("  reg main_web;\n")
        self.vf.write("  reg [ADDR_WIDTH - OFFSET_WIDTH-1:0] main_addr;\n")
        self.vf.write("  reg [LINE_WIDTH-1:0] main_din;\n\n")

        self.vf.write("  // FIFO array read port\n")
        self.vf.write("  reg  fifo_read_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] fifo_read_addr;\n")
        self.vf.write("  wire [WAY_WIDTH-1:0] fifo_read_dout;\n")
        self.vf.write("  // FIFO array write port\n")
        self.vf.write("  reg  fifo_write_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] fifo_write_addr;\n")
        self.vf.write("  reg  [WAY_WIDTH-1:0] fifo_write_din;\n\n")

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


    def write_flops(self):
        """ Write the flip-flops of the cache. """

        self.vf.write("  always @(posedge clk) begin\n")
        self.vf.write("    state       <= #(DELAY) state_next;\n")
        self.vf.write("    way         <= #(DELAY) way_next;\n")
        self.vf.write("    tag         <= #(DELAY) tag_next;\n")
        self.vf.write("    set         <= #(DELAY) set_next;\n")
        self.vf.write("    offset      <= #(DELAY) offset_next;\n")
        self.vf.write("    web_reg     <= #(DELAY) web_reg_next;\n")
        self.vf.write("    din_reg     <= #(DELAY) din_reg_next;\n")
        if self.data_hazard:
            self.vf.write("    data_hazard <= #(DELAY) data_hazard_next;\n")
            self.vf.write("    new_fifo    <= #(DELAY) new_fifo_next;\n")
            self.vf.write("    new_tag     <= #(DELAY) new_tag_next;\n")
            self.vf.write("    new_data    <= #(DELAY) new_data_next;\n")
        self.vf.write("  end\n\n")


    def write_temp_variables(self):
        """ Write the temporary variables of the cache. """

        # For loop variables
        self.vf.write("  // These should be unrolled during synthesis.\n")
        self.vf.write("  integer i; // Used in for loops since indexed part select is illegal (offset)\n")
        self.vf.write("  integer j; // Used in for loops to reach all ways\n")
        self.vf.write("  integer k; // Used in for loops since indexed part select is illegal (tag)\n")
        self.vf.write("  integer l; // Used in for loops since indexed part select is illegal (data line)\n\n")


    def write_logic_block(self):
        """ Write the logic always block of the cache. """

        self.vf.write("  always @* begin\n")
        self.vf.write("    dout             = {WORD_WIDTH{1'bx}};\n")
        self.vf.write("    stall            = 1;\n")
        self.vf.write("    state_next       = state;\n")
        self.vf.write("    way_next         = way;\n")
        self.vf.write("    tag_next         = tag;\n")
        self.vf.write("    set_next         = set;\n")
        self.vf.write("    offset_next      = offset;\n")
        self.vf.write("    web_reg_next     = web_reg;\n")
        self.vf.write("    din_reg_next     = din_reg;\n")
        self.vf.write("    main_csb         = 1;\n")
        self.vf.write("    main_web         = 1;\n")
        self.vf.write("    main_addr        = 0;\n")
        self.vf.write("    main_din         = 0;\n")
        self.vf.write("    fifo_read_csb    = 0;\n")
        self.vf.write("    fifo_read_addr   = 0;\n")
        self.vf.write("    fifo_write_csb   = 1;\n")
        self.vf.write("    fifo_write_addr  = 0;\n")
        self.vf.write("    fifo_write_din   = 0;\n")
        self.vf.write("    tag_read_csb     = 0;\n")
        self.vf.write("    tag_read_addr    = 0;\n")
        self.vf.write("    tag_write_csb    = 1;\n")
        self.vf.write("    tag_write_addr   = 0;\n")
        self.vf.write("    tag_write_din    = 0;\n")
        self.vf.write("    data_read_csb    = 0;\n")
        self.vf.write("    data_read_addr   = 0;\n")
        self.vf.write("    data_write_csb   = 1;\n")
        self.vf.write("    data_write_addr  = 0;\n")
        self.vf.write("    data_write_din   = 0;\n")
        if self.data_hazard:
            self.vf.write("    data_hazard_next = 0;\n")
            self.vf.write("    new_fifo_next    = new_fifo;\n")
            self.vf.write("    new_tag_next     = new_tag;\n")
            self.vf.write("    new_data_next    = new_data;\n")
        self.vf.write("    if (rst) begin // Beginning of reset\n")
        self.vf.write("      state_next      = RESET;\n")
        self.vf.write("      way_next        = 0;\n")
        self.vf.write("      tag_next        = 0;\n")
        self.vf.write("      set_next        = 1;\n")
        self.vf.write("      offset_next     = 0;\n")
        self.vf.write("      web_reg_next    = 1;\n")
        self.vf.write("      din_reg_next    = 0;\n")
        self.vf.write("      new_fifo_next   = 0;\n")
        self.vf.write("      new_tag_next    = 0;\n")
        self.vf.write("      new_data_next   = 0;\n")
        self.vf.write("      fifo_write_csb  = 0;\n")
        self.vf.write("      fifo_write_addr = 0;\n")
        self.vf.write("      fifo_write_din  = 0;\n")
        self.vf.write("      tag_write_csb   = 0;\n")
        self.vf.write("      tag_write_addr  = 0;\n")
        self.vf.write("      tag_write_din   = 0;\n")
        self.vf.write("    end else begin\n")
        self.vf.write("      case (state)\n")

        # RESET state
        self.vf.write("        RESET: begin // Multi-cycle reset\n")
        self.write_reset_state()
        self.vf.write("        end\n")

        # IDLE state
        self.vf.write("        IDLE: begin // Read tag line\n")
        self.write_idle_state()
        self.vf.write("        end\n")

        # COMPARE state
        self.vf.write("        COMPARE: begin // Check if hit/miss\n")
        self.write_compare_state()
        self.vf.write("        end\n")

        # WRITE state
        self.vf.write("        WRITE: begin // Wait for main memory to be ready\n")
        self.write_write_state()
        self.vf.write("        end\n")

        # WAIT_WRITE state
        self.vf.write("        WAIT_WRITE: begin // Wait for main memory to write\n")
        self.write_wait_write_state()
        self.vf.write("        end\n")

        # READ state
        # TODO: Is this state really necessary? WAIT_WRITE state may be used instead.
        self.vf.write("        READ: begin // Wait for main memory to be ready\n")
        self.write_read_state()
        self.vf.write("        end\n")

        # WAIT_READ state
        self.vf.write("        WAIT_READ: begin // Wait line from main memory\n")
        self.write_wait_read_state()
        self.vf.write("        end\n")

        self.vf.write("      endcase\n")
        self.vf.write("    end\n")
        self.vf.write("  end\n\n")
        self.vf.write("endmodule\n")


    def write_reset_state(self):
        """ Write the RESET state of the cache. """

        self.vf.write("          set_next        = set + 1;\n")
        self.vf.write("          fifo_write_csb  = 0;\n")
        self.vf.write("          fifo_write_addr = set;\n")
        self.vf.write("          fifo_write_din  = 0;\n")
        self.vf.write("          tag_write_csb   = 0;\n")
        self.vf.write("          tag_write_addr  = set;\n")
        self.vf.write("          tag_write_din   = 0;\n")
        self.vf.write("          if (set == CACHE_DEPTH-1) begin // Reset is completed\n")
        self.vf.write("            state_next = IDLE;\n")
        self.vf.write("            stall      = 0;\n")
        self.vf.write("          end\n")


    def write_idle_state(self):
        """ Write the IDLE state of the cache. """

        self.vf.write("          stall = 0;\n")
        self.vf.write("          if (!csb) begin // CPU requests\n")
        self.vf.write("            state_next       = COMPARE;\n")
        self.vf.write("            way_next         = 0;\n")
        self.vf.write("            tag_next         = addr[ADDR_WIDTH-1 -: TAG_WIDTH];\n")
        self.vf.write("            set_next         = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("            offset_next      = addr[OFFSET_WIDTH-1:0];\n")
        if self.data_hazard:
            self.vf.write("            data_hazard_next = 0;\n")
            self.vf.write("            new_fifo_next    = 0;\n")
            self.vf.write("            new_tag_next     = 0;\n")
            self.vf.write("            new_data_next    = 0;\n")
        self.vf.write("            web_reg_next     = web;\n")
        self.vf.write("            din_reg_next     = din;\n")
        self.vf.write("            fifo_read_addr   = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("            tag_read_addr    = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("            data_read_addr   = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("            data_write_din   = {LINE_WIDTH * WAY_DEPTH{1'bx}};\n")
        self.vf.write("          end\n")


    def write_compare_state(self):
        """ Write the COMPARE state of the cache. """

        if self.data_hazard:
            self.vf.write("          data_hazard_next = 0;\n")
            self.vf.write("          new_fifo_next    = 0;\n")
            self.vf.write("          new_tag_next     = 0;\n")
            self.vf.write("          new_data_next    = 0;\n")
            self.vf.write("          if (data_hazard)\n")
            self.vf.write("            way_next = new_fifo;\n")
            self.vf.write("          else\n")
            self.vf.write("            way_next = fifo_read_dout;\n")
            self.vf.write("          if ((data_hazard && new_tag[new_fifo * (TAG_WIDTH + 2) + TAG_WIDTH +: 2] == 2'b11) || (!data_hazard && tag_read_dout[fifo_read_dout * (TAG_WIDTH + 2) + TAG_WIDTH +: 2] == 2'b11)) begin // Miss (valid and dirty)\n")
        else:
            self.vf.write("          way_next = fifo_read_dout;\n")
            self.vf.write("          if (tag_read_dout[fifo_read_dout * (TAG_WIDTH + 2) + TAG_WIDTH +: 2] == 2'b11) begin // Miss (valid and dirty)\n")
        self.vf.write("            if (main_stall) begin // Main memory is busy\n")
        self.vf.write("              state_next     = WRITE;\n")
        self.vf.write("              tag_read_addr  = set;\n")
        self.vf.write("              data_read_addr = set;\n")
        self.vf.write("            end else begin // Main memory is ready\n")
        self.vf.write("              state_next     = WAIT_WRITE;\n")
        self.vf.write("              main_csb       = 0;\n")
        self.vf.write("              main_web       = 0;\n")
        if self.data_hazard:
            self.vf.write("              if (data_hazard) begin\n")
            self.vf.write("                main_addr = {new_tag[new_fifo * (TAG_WIDTH + 2) +: TAG_WIDTH], set};\n")
            self.vf.write("                main_din  = new_data[new_fifo * LINE_WIDTH +: LINE_WIDTH];\n")
            self.vf.write("              end else begin\n")
            self.vf.write("                main_addr = {tag_read_dout[fifo_read_dout * (TAG_WIDTH + 2) +: TAG_WIDTH], set};\n")
            self.vf.write("                main_din  = data_read_dout[fifo_read_dout * LINE_WIDTH +: LINE_WIDTH];\n")
            self.vf.write("              end\n")
        else:
            self.vf.write("              main_addr = {tag_read_dout[fifo_read_dout * (TAG_WIDTH + 2) +: TAG_WIDTH], set};\n")
            self.vf.write("              main_din  = data_read_dout[fifo_read_dout * LINE_WIDTH +: LINE_WIDTH];\n")
        self.vf.write("            end\n")
        self.vf.write("          end else begin // Miss (not valid or not dirty)\n")
        self.vf.write("            if (main_stall) // Main memory is busy\n")
        self.vf.write("              state_next = READ;\n")
        self.vf.write("            else begin // Main memory is ready\n")
        self.vf.write("              state_next     = WAIT_READ;\n")
        self.vf.write("              tag_read_addr  = set; // needed in WAIT_READ to keep other ways' tags\n")
        self.vf.write("              data_read_addr = set; // needed in WAIT_READ to keep other ways' data\n")
        self.vf.write("              main_csb       = 0;\n")
        self.vf.write("              main_addr      = {tag, set};\n")
        self.vf.write("            end\n")
        self.vf.write("          end\n")
        # Check if hit
        self.vf.write("          for (j = 0; j < WAY_DEPTH; j = j + 1) // Tag comparison\n")
        if self.data_hazard:
            self.vf.write("            if ((data_hazard && new_tag[j * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && new_tag[j * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag) || (!data_hazard && tag_read_dout[j * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && tag_read_dout[j * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag)) begin // Hit\n")
        else:
            self.vf.write("            if (tag_read_dout[j * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && tag_read_dout[j * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag) begin // Hit\n")
        self.vf.write("              stall      = 0;\n")
        self.vf.write("              state_next = IDLE; // If nothing is requested, go back to IDLE\n")
        self.vf.write("              main_csb   = 1;\n")
        self.vf.write("              if (web_reg) // Read request\n")
        if self.data_hazard:
            self.vf.write("                if (data_hazard)\n")
            self.vf.write("                  dout = new_data[j * LINE_WIDTH + offset * WORD_WIDTH +: WORD_WIDTH];\n")
            self.vf.write("                else\n")
            self.vf.write("                  dout = data_read_dout[j * LINE_WIDTH + offset * WORD_WIDTH +: WORD_WIDTH];\n")
        else:
            self.vf.write("                dout = data_read_dout[j * LINE_WIDTH + offset * WORD_WIDTH +: WORD_WIDTH];\n")
        self.vf.write("              else begin  // Write request\n")
        self.vf.write("                tag_write_csb   = 0;\n")
        self.vf.write("                tag_write_addr  = set;\n")
        self.vf.write("                data_write_csb  = 0;\n")
        self.vf.write("                data_write_addr = set;\n")
        if self.data_hazard:
            self.vf.write("                if (data_hazard) begin\n")
            self.vf.write("                  tag_write_din  = new_tag;\n")
            self.vf.write("                  data_write_din = new_data;\n")
            self.vf.write("                end else begin\n")
            self.vf.write("                  tag_write_din  = tag_read_dout;\n")
            self.vf.write("                  data_write_din = data_read_dout;\n")
            self.vf.write("                end\n")
        else:
            self.vf.write("                tag_write_din  = tag_read_dout;\n")
            self.vf.write("                data_write_din = data_read_dout;\n")
        self.vf.write("                tag_write_din[j * (2 + TAG_WIDTH) + TAG_WIDTH] = 1'b1;\n")
        self.vf.write("                for (i = 0; i < WORD_WIDTH; i = i + 1)\n")
        self.vf.write("                  data_write_din[j * LINE_WIDTH + offset * WORD_WIDTH + i] = din_reg[i];\n")
        self.vf.write("              end\n")
        # Pipelining in COMPARE state
        self.vf.write("              if (!csb) begin // Pipeline\n")
        self.vf.write("                state_next   = COMPARE;\n")
        self.vf.write("                tag_next     = addr[ADDR_WIDTH-1 -: TAG_WIDTH];\n")
        self.vf.write("                set_next     = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("                offset_next  = addr[OFFSET_WIDTH-1:0];\n")
        self.vf.write("                web_reg_next = web;\n")
        self.vf.write("                din_reg_next = din;\n")
        if self.data_hazard:
            self.vf.write("                if (!web_reg && addr[OFFSET_WIDTH +: SET_WIDTH] == set) begin // Avoid data hazard\n")
            self.vf.write("                  data_hazard_next = 1;\n")
            self.vf.write("                  if (data_hazard) begin\n")
            self.vf.write("                    new_fifo_next = new_fifo;\n")
            self.vf.write("                    new_tag_next  = new_tag;\n")
            self.vf.write("                    new_data_next = new_data;\n")
            self.vf.write("                  end else begin\n")
            self.vf.write("                    new_fifo_next = fifo_read_dout;\n")
            self.vf.write("                    new_tag_next  = tag_read_dout;\n")
            self.vf.write("                    new_data_next = data_read_dout;\n")
            self.vf.write("                  end\n")
            self.vf.write("                  new_tag_next[j * (2 + TAG_WIDTH) + TAG_WIDTH] = 1'b1;\n")
            self.vf.write("                  for (i = 0; i < WORD_WIDTH; i = i + 1)\n")
            self.vf.write("                    new_data_next[j * LINE_WIDTH + offset * WORD_WIDTH + i] = din_reg[i];\n")
            self.vf.write("                end else begin\n")
            self.vf.write("                  fifo_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("                  tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("                  data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("                end              \n")
        else:
            self.vf.write("                fifo_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("                tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("                data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("              end\n")
        self.vf.write("            end\n")

    def write_write_state(self):
        """ Write the WRITE state of the cache. """

        self.vf.write("          tag_read_addr  = set;\n")
        self.vf.write("          data_read_addr = set;\n")
        self.vf.write("          if (!main_stall) begin // Main memory is ready\n")
        self.vf.write("            state_next = WAIT_WRITE;\n")
        self.vf.write("            main_csb   = 0;\n")
        self.vf.write("            main_web   = 0;\n")
        self.vf.write("            main_addr  = {tag_read_dout[way * (TAG_WIDTH + 2) +: TAG_WIDTH], set};\n")
        self.vf.write("            main_din   = data_read_dout[way * LINE_WIDTH +: LINE_WIDTH];\n")
        self.vf.write("          end\n")


    def write_wait_write_state(self):
        """ Write the WAIT_WRITE state of the cache. """

        self.vf.write("          tag_read_addr  = set; // needed in WAIT_READ to keep other ways' tags\n")
        self.vf.write("          data_read_addr = set; // needed in WAIT_READ to keep other ways' data\n")
        self.vf.write("          if (!main_stall) begin // Read line from main memory\n")
        self.vf.write("            state_next = WAIT_READ;\n")
        self.vf.write("            main_csb   = 0;\n")
        self.vf.write("            main_addr  = {tag, set};\n")
        self.vf.write("          end\n")


    def write_read_state(self):
        """ Write the READ state of the cache. """

        self.vf.write("          tag_read_addr  = set; // needed in WAIT_READ to keep other ways' tags\n")
        self.vf.write("          data_read_addr = set; // needed in WAIT_READ to keep other ways' data\n")
        self.vf.write("          if (!main_stall) begin // Main memory is ready\n")
        self.vf.write("            state_next = WAIT_READ;\n")
        self.vf.write("            main_csb   = 0;\n")
        self.vf.write("            main_addr  = {tag, set};\n")
        self.vf.write("          end\n")


    def write_wait_read_state(self):
        """ Write the WAIT_READ state of the cache. """

        self.vf.write("          tag_read_addr    = set;\n")
        self.vf.write("          data_read_addr   = set;\n")
        self.vf.write("          if (!main_stall) begin // Switch to COMPARE\n")
        self.vf.write("            stall           = 0;\n")
        self.vf.write("            state_next      = IDLE; // If nothing is requested, go back to IDLE\n")
        self.vf.write("            fifo_write_csb  = 0;\n")
        self.vf.write("            fifo_write_addr = set;\n")
        self.vf.write("            fifo_write_din  = way + 1;\n")
        self.vf.write("            tag_write_csb   = 0;\n")
        self.vf.write("            tag_write_addr  = set;\n")
        self.vf.write("            tag_write_din   = tag_read_dout;\n")
        self.vf.write("            tag_write_din[way * (2 + TAG_WIDTH) + TAG_WIDTH]     = 1'b1;\n")
        self.vf.write("            tag_write_din[way * (2 + TAG_WIDTH) + TAG_WIDTH + 1] = ~web_reg;\n")
        self.vf.write("            for (k = 0; k < TAG_WIDTH; k = k + 1)\n")
        self.vf.write("              tag_write_din[way * (2 + TAG_WIDTH) + k] = tag[k];\n")
        self.vf.write("            data_write_csb  = 0;\n")
        self.vf.write("            data_write_addr = set;\n")
        self.vf.write("            data_write_din  = data_read_dout;\n")
        self.vf.write("            for (l = 0; l < LINE_WIDTH; l = l + 1)\n")
        self.vf.write("              data_write_din[way * LINE_WIDTH + l] = main_dout[l];\n")
        if self.data_hazard:
            self.vf.write("            new_tag_next    = 0;\n")
            self.vf.write("            new_data_next   = 0;\n")
        self.vf.write("            if (web_reg)\n")
        self.vf.write("              dout = main_dout[offset * WORD_WIDTH +: WORD_WIDTH];\n")
        self.vf.write("            else\n")
        self.vf.write("              for (i = 0; i < WORD_WIDTH; i = i + 1)\n")
        self.vf.write("                data_write_din[way * LINE_WIDTH + offset * WORD_WIDTH + i] = din_reg[i];\n")
        # Pipelining in WAIT_READ state
        self.vf.write("            if (!csb) begin // Pipeline\n")
        self.vf.write("              state_next   = COMPARE;\n")
        self.vf.write("              tag_next     = addr[ADDR_WIDTH-1 -: TAG_WIDTH];\n")
        self.vf.write("              set_next     = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("              offset_next  = addr[OFFSET_WIDTH-1:0];\n")
        self.vf.write("              web_reg_next = web;\n")
        self.vf.write("              din_reg_next = din;\n")
        if self.data_hazard:
            self.vf.write("              if (addr[OFFSET_WIDTH +: SET_WIDTH] == set) begin // Avoid data hazard\n")
            self.vf.write("                data_hazard_next = 1;\n")
            self.vf.write("                new_fifo_next    = way + 1;\n")
            self.vf.write("                new_tag_next     = tag_read_dout;\n")
            self.vf.write("                new_tag_next[way * (2 + TAG_WIDTH) + TAG_WIDTH]     = 1'b1;\n")
            self.vf.write("                new_tag_next[way * (2 + TAG_WIDTH) + TAG_WIDTH + 1] = ~web_reg;\n")
            self.vf.write("                for (k = 0; k < TAG_WIDTH; k = k + 1)\n")
            self.vf.write("                  new_tag_next[way * (2 + TAG_WIDTH) + k] = tag[k];\n")
            self.vf.write("                new_data_next = data_read_dout;\n")
            self.vf.write("                for (l = 0; l < LINE_WIDTH; l = l + 1)\n")
            self.vf.write("                  new_data_next[way * LINE_WIDTH + l] = main_dout[l];\n")
            self.vf.write("                if (!web_reg)\n")
            self.vf.write("                  for (i = 0; i < WORD_WIDTH; i = i + 1)\n")
            self.vf.write("                    new_data_next[way * LINE_WIDTH + offset * WORD_WIDTH + i]  = din_reg[i];\n")
            self.vf.write("              end else begin\n")
            self.vf.write("                tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("                data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("              end\n")
        else:
            self.vf.write("              tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("              data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("            end\n")
        self.vf.write("          end\n")