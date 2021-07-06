# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from cache_base import cache_base


class direct_cache(cache_base):
    """
    This is the design module of direct-mapped cache.
    """

    def __init__(self, cache_config, name):

        super().__init__(cache_config, name)


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

        # No need for bypass registers if the SRAMs are guaranteed to be data hazard proof
        if self.data_hazard:
            self.vf.write("  // When the next request is in the same set, tag and data lines might be old (data hazard).\n")
            self.vf.write("  reg [2+TAG_WIDTH-1:0] new_tag, new_tag_next;   // msb is whether to use bypass registers, the rest is dirty bit and tag bits\n")
            self.vf.write("  reg [LINE_WIDTH-1:0]  new_data, new_data_next; // new data line from the previous cycle\n\n")

        self.vf.write("  // Main memory ports\n")
        self.vf.write("  reg main_csb;\n")
        self.vf.write("  reg main_web;\n")
        self.vf.write("  reg [ADDR_WIDTH-OFFSET_WIDTH-1:0] main_addr;\n")
        self.vf.write("  reg [LINE_WIDTH-1:0] main_din;\n\n")

        self.vf.write("  // Tag array read port\n")
        self.vf.write("  reg  tag_read_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0]   tag_read_addr;\n")
        self.vf.write("  wire [2+TAG_WIDTH-1:0] tag_read_dout;\n")
        self.vf.write("  // Tag array write port\n")
        self.vf.write("  reg  tag_write_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0]   tag_write_addr;\n")
        self.vf.write("  reg  [2+TAG_WIDTH-1:0] tag_write_din;\n\n")

        self.vf.write("  // Data array read port\n")
        self.vf.write("  reg  data_read_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0]  data_read_addr;\n")
        self.vf.write("  wire [LINE_WIDTH-1:0] data_read_dout;\n")
        self.vf.write("  // Data array write port\n")
        self.vf.write("  reg  data_write_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0]  data_write_addr;\n")
        self.vf.write("  reg  [LINE_WIDTH-1:0] data_write_din;\n\n")


    def write_flops(self):
        """ Write the flip-flops of the cache. """
    
        self.vf.write("  always @(posedge clk) begin\n")
        self.vf.write("    state    <= #(DELAY) state_next;\n")
        self.vf.write("    tag      <= #(DELAY) tag_next;\n")
        self.vf.write("    set      <= #(DELAY) set_next;\n")
        self.vf.write("    offset   <= #(DELAY) offset_next;\n")
        self.vf.write("    web_reg  <= #(DELAY) web_reg_next;\n")
        self.vf.write("    din_reg  <= #(DELAY) din_reg_next;\n")

        if self.data_hazard:
            self.vf.write("    new_tag  <= #(DELAY) new_tag_next;\n")
            self.vf.write("    new_data <= #(DELAY) new_data_next;\n")

        self.vf.write("  end\n\n")


    def write_temp_variables(self):
        """ Write the temporary variables of the cache. """

        # For loop variable
        self.vf.write("  // This should be unrolled during synthesis.\n")
        self.vf.write("  integer i; // Used in for loops since indexed part select is illegal (offset)\n\n")


    def write_logic_block(self):
        """ Write the logic always block of the cache. """

        self.vf.write("  always @* begin\n")
        self.vf.write("    stall           = 1;\n")
        self.vf.write("    dout            = {WORD_WIDTH{1'bx}};\n")
        self.vf.write("    state_next      = state;\n")
        self.vf.write("    tag_next        = tag;\n")
        self.vf.write("    set_next        = set;\n")
        self.vf.write("    offset_next     = offset;\n")
        self.vf.write("    web_reg_next    = web_reg;\n")
        self.vf.write("    din_reg_next    = din_reg;\n")
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
        self.vf.write("    data_write_din  = 0;\n")

        if self.data_hazard:
            self.vf.write("    new_tag_next    = new_tag;\n")
            self.vf.write("    new_data_next   = new_data;\n")

        self.vf.write("    if (rst) begin // Beginning of reset\n")
        self.vf.write("      state_next     = RESET;\n")
        self.vf.write("      tag_next       = 0;\n")
        self.vf.write("      set_next       = 1;\n")
        self.vf.write("      offset_next    = 0;\n")
        self.vf.write("      web_reg_next   = 1;\n")
        self.vf.write("      din_reg_next   = 0;\n")
        self.vf.write("      new_tag_next   = 0;\n")
        self.vf.write("      new_data_next  = 0;\n")
        self.vf.write("      tag_write_csb  = 0;\n")
        self.vf.write("      tag_write_addr = 0;\n")
        self.vf.write("      tag_write_din  = 0;\n")
        self.vf.write("    end else if (flush) begin // Beginning of flush\n")
        self.vf.write("      state_next     = FLUSH;\n")
        self.vf.write("      set_next       = 0;\n")
        self.vf.write("      tag_read_csb   = 0;\n")
        self.vf.write("      tag_read_addr  = 0;\n")
        self.vf.write("      data_read_csb  = 0;\n")
        self.vf.write("      data_read_addr = 0;\n")
        self.vf.write("    end else begin\n")
        self.vf.write("      case (state)\n")

        # RESET state
        self.vf.write("        RESET: begin // Multi-cycle reset\n")
        self.write_reset_state()
        self.vf.write("        end\n")

        # FLUSH state
        self.vf.write("        FLUSH: begin // Multi-cycle flush\n")
        self.write_flush_state()
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

        self.vf.write("          set_next       = set + 1;\n")
        self.vf.write("          tag_write_csb  = 0;\n")
        self.vf.write("          tag_write_addr = set;\n")
        self.vf.write("          tag_write_din  = 0;\n")
        self.vf.write("          if (set == CACHE_DEPTH-1) begin // Reset is completed\n")
        self.vf.write("            state_next = IDLE;\n")
        self.vf.write("            stall      = 0;\n")
        self.vf.write("          end\n")


    def write_flush_state(self):
        """ Write the FLUSH state of the cache. """

        self.vf.write("          tag_read_csb   = 0;\n")
        self.vf.write("          tag_read_addr  = set;\n")
        self.vf.write("          data_read_csb  = 0;\n")
        self.vf.write("          data_read_addr = set;\n")
        self.vf.write("          main_csb       = 0;\n")
        self.vf.write("          main_web       = 0;\n")
        self.vf.write("          main_addr      = {tag_read_dout[TAG_WIDTH-1:0], set};\n")
        self.vf.write("          main_din       = data_read_dout;\n")
        self.vf.write("          if (!main_stall) begin\n")
        self.vf.write("            set_next       = set + 1;\n")
        self.vf.write("            tag_read_addr  = set + 1;\n")
        self.vf.write("            data_read_addr = set + 1;\n")
        self.vf.write("            if (set == CACHE_DEPTH-1) begin // Flush is completed\n")
        self.vf.write("              state_next = IDLE;\n")
        self.vf.write("              stall      = 0;\n")
        self.vf.write("            end\n")
        self.vf.write("          end\n")


    def write_idle_state(self):
        """ Write the IDLE state of the cache. """

        self.vf.write("          stall = 0;\n")
        self.vf.write("          if (!csb) begin // CPU requests\n")
        self.vf.write("            stall          = 1;\n")
        self.vf.write("            state_next     = COMPARE;\n")
        self.vf.write("            tag_next       = addr[ADDR_WIDTH-1 -: TAG_WIDTH];\n")
        self.vf.write("            set_next       = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("            offset_next    = addr[OFFSET_WIDTH-1:0];\n")

        if self.data_hazard:
            self.vf.write("            new_tag_next   = 0;\n")
            self.vf.write("            new_data_next  = 0;\n")

        self.vf.write("            web_reg_next   = web;\n")
        self.vf.write("            din_reg_next   = din;\n")
        self.vf.write("            tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("            data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("            data_write_din = {LINE_WIDTH{1'bx}};\n")
        self.vf.write("          end\n")


    def write_compare_state(self):
        """ Write the COMPARE state of the cache. """

        if self.data_hazard:
            self.vf.write("          new_tag_next  = 0;\n")
            self.vf.write("          new_data_next = 0;\n")
            self.vf.write("          if ((new_tag[TAG_WIDTH+1] && new_tag[TAG_WIDTH-1:0] == tag) || (!new_tag[TAG_WIDTH+1] && tag_read_dout[TAG_WIDTH+1] && tag_read_dout[TAG_WIDTH-1:0] == tag)) begin // Hit\n")
        else:
            self.vf.write("          if (tag_read_dout[TAG_WIDTH+1] && tag_read_dout[TAG_WIDTH-1:0] == tag) begin // Hit\n")

        self.vf.write("            stall      = 0;\n")
        self.vf.write("            state_next = IDLE; // If nothing is requested, go back to IDLE\n")
        self.vf.write("            if (web_reg) // Read request\n")

        if self.data_hazard:
            self.vf.write("              if (new_tag[TAG_WIDTH+1])\n")
            self.vf.write("                dout = new_data[offset * WORD_WIDTH +: WORD_WIDTH];\n")
            self.vf.write("              else\n")
            self.vf.write("                dout = data_read_dout[offset * WORD_WIDTH +: WORD_WIDTH];\n")
        else:
            self.vf.write("              dout = data_read_dout[offset * WORD_WIDTH +: WORD_WIDTH];\n")

        self.vf.write("            else begin // Write request\n")
        self.vf.write("              tag_write_csb   = 0;\n")
        self.vf.write("              tag_write_addr  = set;\n")
        self.vf.write("              tag_write_din   = {2'b11, tag};\n")
        self.vf.write("              data_write_csb  = 0;\n")
        self.vf.write("              data_write_addr = set;\n")

        if self.data_hazard:
            self.vf.write("              if (new_tag[TAG_WIDTH+1])\n")
            self.vf.write("                data_write_din = new_data;\n")
            self.vf.write("              else\n")
            self.vf.write("                data_write_din = data_read_dout;\n")
        else:
            self.vf.write("              data_write_din = data_read_dout;\n")

        self.vf.write("              for (i = 0; i < WORD_WIDTH; i = i + 1)\n")
        self.vf.write("                data_write_din[offset * WORD_WIDTH + i] = din_reg[i];\n")
        self.vf.write("            end\n")

        # Pipelining in COMPARE state
        self.vf.write("            if (!csb) begin // Pipeline\n")
        self.vf.write("              state_next   = COMPARE;\n")
        self.vf.write("              tag_next     = addr[ADDR_WIDTH-1 -: TAG_WIDTH];\n")
        self.vf.write("              set_next     = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("              offset_next  = addr[OFFSET_WIDTH-1:0];\n")
        self.vf.write("              web_reg_next = web;\n")
        self.vf.write("              din_reg_next = din;\n")

        if self.data_hazard:
            self.vf.write("              if (!web_reg && addr[OFFSET_WIDTH +: SET_WIDTH] == set) begin // Avoid data hazard\n")
            self.vf.write("                new_tag_next = {2'b11, tag};\n")
            self.vf.write("                if (new_tag[TAG_WIDTH+1])\n") 
            self.vf.write("                  new_data_next = new_data;\n")
            self.vf.write("                else\n")
            self.vf.write("                  new_data_next = data_read_dout;\n")
            self.vf.write("                for (i = 0; i < WORD_WIDTH; i = i + 1)\n")
            self.vf.write("                  new_data_next[offset * WORD_WIDTH + i] = din_reg[i];\n")
            self.vf.write("              end else begin\n")
            self.vf.write("                tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("                data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("              end\n")
        else:
            self.vf.write("              tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("              data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")

        self.vf.write("            end\n")

        # Miss (dirty)
        if self.data_hazard:
            self.vf.write("          end else if (new_tag[TAG_WIDTH +: 2] == 2'b11 || (!new_tag[TAG_WIDTH+1] && tag_read_dout[TAG_WIDTH +: 2] == 2'b11)) begin // Miss (valid and dirty)\n")
        else:
            self.vf.write("          end else if (tag_read_dout[TAG_WIDTH +: 2] == 2'b11) begin // Miss (valid and dirty)\n")

        self.vf.write("            if (main_stall) begin // Main memory is busy\n")
        self.vf.write("              state_next     = WRITE;\n")
        self.vf.write("              tag_read_addr  = set;\n")
        self.vf.write("              data_read_addr = set;\n")
        self.vf.write("            end else begin // Main memory is ready\n")
        self.vf.write("              state_next = WAIT_WRITE;\n")
        self.vf.write("              main_csb   = 0;\n")
        self.vf.write("              main_web   = 0;\n")

        if self.data_hazard:
            self.vf.write("              if (new_tag[TAG_WIDTH+1]) begin\n")
            self.vf.write("                main_addr = {new_tag[TAG_WIDTH-1:0], set};\n")
            self.vf.write("                main_din  = new_data;					\n")
            self.vf.write("              end else begin\n")
            self.vf.write("                main_addr = {tag_read_dout[TAG_WIDTH-1:0], set};\n")
            self.vf.write("                main_din  = data_read_dout;\n")
            self.vf.write("              end\n")
        else:
            self.vf.write("              main_addr = {tag_read_dout[TAG_WIDTH-1:0], set};\n")
            self.vf.write("              main_din  = data_read_dout;\n")

        self.vf.write("            end\n")

        # Miss (not dirty)
        self.vf.write("          end else begin // Miss (not valid or not dirty)\n")
        self.vf.write("            if (main_stall) // Main memory is busy\n")
        self.vf.write("              state_next = READ;\n")
        self.vf.write("            else begin // Main memory is ready\n")
        self.vf.write("              state_next = WAIT_READ;\n")
        self.vf.write("              main_csb   = 0;\n")
        self.vf.write("              main_addr  = {tag, set};\n")
        self.vf.write("            end\n")
        self.vf.write("          end\n")


    def write_write_state(self):
        """ Write the WRITE state of the cache. """

        self.vf.write("          tag_read_addr  = set;\n")
        self.vf.write("          data_read_addr = set;\n")
        self.vf.write("          if (!main_stall) begin // Main memory is ready\n")
        self.vf.write("            state_next = WAIT_WRITE;\n")
        self.vf.write("            main_csb   = 0;\n")
        self.vf.write("            main_web   = 0;\n")
        self.vf.write("            main_addr  = {tag_read_dout[TAG_WIDTH-1:0], set};\n")
        self.vf.write("            main_din   = data_read_dout;\n")
        self.vf.write("          end\n")


    def write_wait_write_state(self):
        """ Write the WAIT_WRITE state of the cache. """

        self.vf.write("          if (!main_stall) begin // Read line from main memory\n")
        self.vf.write("            state_next = WAIT_READ;\n")
        self.vf.write("            main_csb   = 0;\n")
        self.vf.write("            main_addr  = {tag, set};\n")
        self.vf.write("          end\n")


    def write_read_state(self):
        """ Write the READ state of the cache. """

        self.vf.write("          if (!main_stall) begin // Main memory is ready\n")
        self.vf.write("            state_next = WAIT_READ;\n")
        self.vf.write("            main_csb   = 0;\n")
        self.vf.write("            main_addr  = {tag, set};\n")
        self.vf.write("          end\n")


    def write_wait_read_state(self):
        """ Write the WAIT_READ state of the cache. """

        self.vf.write("          if (!main_stall) begin // Finish the request\n")
        self.vf.write("            stall           = 0;\n")
        self.vf.write("            state_next      = IDLE; // If nothing is requested, go back to IDLE\n")
        self.vf.write("            tag_write_csb   = 0;\n")
        self.vf.write("            tag_write_addr  = set;\n")
        self.vf.write("            tag_write_din   = {1'b1, ~web_reg, tag};\n")
        self.vf.write("            data_write_csb  = 0;\n")
        self.vf.write("            data_write_addr = set;\n")
        self.vf.write("            data_write_din  = main_dout;\n")

        if self.data_hazard:
            self.vf.write("            new_tag_next    = 0;\n")
            self.vf.write("            new_data_next   = main_dout;\n")

        self.vf.write("            if (web_reg)\n")
        self.vf.write("              dout = main_dout[offset * WORD_WIDTH +: WORD_WIDTH];\n")
        self.vf.write("            else\n")
        self.vf.write("              for (i = 0; i < WORD_WIDTH; i = i + 1) begin\n")
        self.vf.write("                data_write_din[offset * WORD_WIDTH + i] = din_reg[i];\n")

        if self.data_hazard:
            self.vf.write("                new_data_next[offset * WORD_WIDTH + i]  = din_reg[i];\n")

        self.vf.write("              end\n")

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
            self.vf.write("                new_tag_next = {1'b1, ~web_reg, tag};\n")
            self.vf.write("              end else begin\n")
            self.vf.write("                tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("                data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("              end\n")
        else:
            self.vf.write("              tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("              data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")

        self.vf.write("            end\n")
        self.vf.write("          end\n")