import cache.cache_base


class n_way_random_cache(cache_base):
    """
    This is the design module of N-way set associative cache
    with random replacement policy.
    """
    def __init__(self, name, cache_config):

        super().__init__(name, cache_config)


    def write_registers(self):
        """ Write the registers of the cache. """

        self.vf.write("  reg rst_reg, rst_reg_next;\n")
        self.vf.write("  reg web_reg, web_reg_next;\n")
        self.vf.write("  reg stall;\n")
        self.vf.write("  reg [TAG_WIDTH-1:0]    tag, tag_next;\n")
        self.vf.write("  reg [SET_WIDTH-1:0]    set, set_next;\n")
        self.vf.write("  reg [OFFSET_WIDTH-1:0] offset, offset_next;\n")
        self.vf.write("  reg [WORD_WIDTH-1:0]   din_reg, din_reg_next;\n")
        self.vf.write("  reg [WORD_WIDTH-1:0]   dout;\n")
        self.vf.write("  reg [1:0]              state, state_next;   // state is used while reading/writing main memory\n")
        self.vf.write("  reg [WAY_WIDTH-1:0]    way, way_next;       // to place in a way\n")
        self.vf.write("  reg [WAY_WIDTH-1:0]    random, random_next; // random bits\n")
        # No need for bypass registers if the cache is not pipelined or RAMs are guaranteed to be data hazard proof
        if self.data_hazard:
            self.vf.write("  // When the next fetch is in the same set, tag_array and data_array might be old (data hazard).\n")
            self.vf.write("  reg data_hazard, data_hazard_next; // high if must write and read from arrays at the same cycle\n")
            self.vf.write("  reg [(2 + TAG_WIDTH) * WAY_DEPTH-1:0] new_tag, new_tag_next;   // new tag line from the previous cycle\n")
            self.vf.write("  reg [LINE_WIDTH * WAY_DEPTH-1:0]      new_data, new_data_next; // new data line from the previous cycle\n\n")

        self.vf.write("  reg main_csb;\n")
        self.vf.write("  reg main_web;\n")
        self.vf.write("  reg [ADDR_WIDTH - OFFSET_WIDTH-1:0] main_addr;\n")
        self.vf.write("  reg [LINE_WIDTH-1:0] main_din;\n\n")

        self.vf.write("  reg  tag_read_csb;  // tag read port active low chip select\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] tag_read_addr;\n")
        self.vf.write("  wire [(2 + TAG_WIDTH) * WAY_DEPTH-1:0] tag_read_dout;\n")
        self.vf.write("  reg  tag_write_csb; // tag write port active low chip select\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] tag_write_addr;\n")
        self.vf.write("  reg  [(2 + TAG_WIDTH) * WAY_DEPTH-1:0] tag_write_din;\n\n")

        self.vf.write("  reg  data_read_csb;  // data read port active low chip select\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] data_read_addr;\n")
        self.vf.write("  wire [LINE_WIDTH * WAY_DEPTH-1:0] data_read_dout;\n")
        self.vf.write("  reg  data_write_csb; // data write port active low chip select\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] data_write_addr;\n")
        self.vf.write("  reg  [LINE_WIDTH * WAY_DEPTH-1:0] data_write_din;\n")


    def write_flops(self):
        """ Write the flip-flops of the cache. """

        self.vf.write("  always @(posedge clk) begin\n")
        self.vf.write("    state       <= #(DELAY) state_next;\n")
        self.vf.write("    way         <= #(DELAY) way_next;\n")
        self.vf.write("    random      <= #(DELAY) random_next;\n")
        self.vf.write("    tag         <= #(DELAY) tag_next;\n")
        self.vf.write("    set         <= #(DELAY) set_next;\n")
        self.vf.write("    offset      <= #(DELAY) offset_next;\n")
        if self.data_hazard:
            self.vf.write("    data_hazard <= #(DELAY) data_hazard_next;\n")
            self.vf.write("    new_tag     <= #(DELAY) new_tag_next;\n")
            self.vf.write("    new_data    <= #(DELAY) new_data_next;\n")
        self.vf.write("    rst_reg     <= #(DELAY) rst_reg_next;\n")
        self.vf.write("    web_reg     <= #(DELAY) web_reg_next;\n")
        self.vf.write("    din_reg     <= #(DELAY) din_reg_next;\n")
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
        self.vf.write("    dout             = {{WORD_WIDTH{{1'bx}}}};\n")
        self.vf.write("    stall            = 1;\n")
        self.vf.write("    state_next       = state;\n")
        self.vf.write("    way_next         = way;\n")
        self.vf.write("    random_next      = random + 1;\n")
        self.vf.write("    tag_next         = tag;\n")
        self.vf.write("    set_next         = set;\n")
        self.vf.write("    offset_next      = offset;\n")
        self.vf.write("    web_reg_next     = web_reg;\n")
        self.vf.write("    rst_reg_next     = rst_reg;\n")
        self.vf.write("    din_reg_next     = din_reg;\n")
        self.vf.write("    main_csb         = 1;\n")
        self.vf.write("    main_web         = 1;\n")
        self.vf.write("    main_addr        = 0;\n")
        self.vf.write("    main_din         = 0;\n")
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
            self.vf.write("    new_tag_next     = new_tag;\n")
            self.vf.write("    new_data_next    = new_data;\n")

        # Reset state
        # This is a multi-cycle reset. It sets all rows of the internal arrays to 0.
        # Cache enters this state when rst signal is high. Until it exits the state,
        # stall signal is high.
        self.vf.write("    if (rst || rst_reg) begin // RESET: Multi-cycle reset\n")
        self.vf.write("      state_next  = 0;\n")
        self.vf.write("      random_next = 0;\n")
        self.vf.write("      tag_next    = 0;\n")
        self.vf.write("      set_next    = 1;\n")
        self.vf.write("      if (rst_reg)\n")
        self.vf.write("        set_next = set + 1;\n")
        self.vf.write("      offset_next    = 0;\n")
        self.vf.write("      web_reg_next   = 1;\n")
        self.vf.write("      rst_reg_next   = 1;\n")
        self.vf.write("      din_reg_next   = 0;\n")
        self.vf.write("      tag_write_csb  = 0;\n")
        self.vf.write("      if (rst_reg)\n")
        self.vf.write("        tag_write_addr  = set;\n")
        self.vf.write("      if (rst_reg && set == CACHE_DEPTH-1) begin\n")
        self.vf.write("        rst_reg_next = 0;\n")
        self.vf.write("        stall        = 0;\n")
        self.vf.write("      end\n")
        self.vf.write("    end else begin\n")

        # State 0
        # This is the initial state of cache. Cache reads the address input and fetches
        # tag and data lines from its internal OpenRAM arrays. State switches to 1. Stall
        # signal is not low in this state since we want to fill the pipeline. If csb
        # input is high, cache waits in this state.
        self.vf.write("      case(state)\n")
        self.vf.write("      0: begin // STATE 0: Read tag line\n")
        self.vf.write("        stall = 0;\n")
        self.vf.write("        if (!csb) begin\n")
        # If cache is not pipelined, stall must be high in state 0 since we will not fill
        # a pipeline.
        if not self.pipeline:
            self.vf.write("          stall            = 1;\n")
        self.vf.write("          state_next       = 1;\n")
        self.vf.write("          way_next         = 0;\n")
        self.vf.write("          tag_next         = addr[ADDR_WIDTH-1 -: TAG_WIDTH];\n")
        self.vf.write("          set_next         = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("          offset_next      = addr[OFFSET_WIDTH-1:0];\n")
        if self.data_hazard:
            self.vf.write("          data_hazard_next = 0;\n")
            self.vf.write("          new_tag_next     = 0;\n")
            self.vf.write("          new_data_next    = 0;\n")
        self.vf.write("          web_reg_next     = web;\n")
        self.vf.write("          din_reg_next     = din;\n")
        self.vf.write("          tag_read_addr    = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("          data_read_addr   = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("          data_write_din   = {{LINE_WIDTH * WAY_DEPTH{{1'bx}}}};\n")
        self.vf.write("        end\n")
        self.vf.write("      end\n")

        # State 1
        # Tag and data lines are returned by internal arrays. Cache checks whether hit or
        # miss.
        # 
        # If it is a hit, cache immediately performs the request (returns data if read,
        # writes input if write). If csb is low, it also reads the next address from the
        # pipeline and requests corresponding tag and data lines from internal arrays. If
        # the next address is in the same set with the current address and current request
        # is write (data needs to be updated), data hazard might occur. In this case, cache
        # uses “bypass registers” so that it can use up-to-date data in the next cycle. If
        # csb is high, state switches to 0; otherwise, it stays the same. Stall signal stays
        # low to keep the pipeline running.
        # 
        # If it is a miss, cache checks whether the data line is dirty or not. In either case,
        # stall becomes high.
        # 
        # If the data line is dirty, cache sends the dirty line to the lower memory. State
        # switches to 2.
        # 
        # If the data line is not dirty, cache requests the new data line from the lower
        # memory. State switches to 3.
        self.vf.write("      1: begin // STATE 1: Check if hit/miss\n")
        if self.data_hazard:
            self.vf.write("        data_hazard_next = 0;\n")
            self.vf.write("        new_tag_next     = 0;\n")
            self.vf.write("        new_data_next    = 0;\n")
            self.vf.write("        if ((data_hazard && new_tag[random * (TAG_WIDTH + 2) + TAG_WIDTH +: 2] == 2'b11) || (!data_hazard && tag_read_dout[random * (TAG_WIDTH + 2) + TAG_WIDTH +: 2] == 2'b11)) begin // Miss (valid and dirty)\n")
        else:
            self.vf.write("        if (tag_read_dout[random * (TAG_WIDTH + 2) + TAG_WIDTH +: 2] == 2'b11) begin // Miss (valid and dirty)\n")
        self.vf.write("          state_next = 2;\n")
        self.vf.write("          way_next   = random;\n")
        self.vf.write("          main_csb   = 0;\n")
        self.vf.write("          main_web   = 0;\n")
        if self.data_hazard:
            self.vf.write("          if (data_hazard) begin\n")
            self.vf.write("            main_addr = {new_tag[random * (TAG_WIDTH + 2) +: TAG_WIDTH], set};\n")
            self.vf.write("            main_din  = new_data[random * LINE_WIDTH +: LINE_WIDTH];\n")
            self.vf.write("          end else begin\n")
            self.vf.write("            main_addr = {tag_read_dout[random * (TAG_WIDTH + 2) +: TAG_WIDTH], set};\n")
            self.vf.write("            main_din  = data_read_dout[random * LINE_WIDTH +: LINE_WIDTH];\n")
            self.vf.write("          end\n")
        else:
            self.vf.write("          main_addr = {tag_read_dout[random * (TAG_WIDTH + 2) +: TAG_WIDTH], set};\n")
            self.vf.write("          main_din  = data_read_dout[random * LINE_WIDTH +: LINE_WIDTH];\n")
        self.vf.write("        end else begin // Miss (not valid or not dirty)\n")
        self.vf.write("          state_next     = 3;\n")
        self.vf.write("          way_next       = random;\n")
        self.vf.write("          tag_read_addr  = set; // needed in state 3 to keep other ways' tags\n")
        self.vf.write("          data_read_addr = set; // needed in state 3 to keep other ways' data\n")
        self.vf.write("          main_csb       = 0;\n")
        self.vf.write("          main_addr      = {tag, set};\n")
        self.vf.write("        end\n")
        # Find an empty way to fill
        self.vf.write("        for (j = 0; j < WAY_DEPTH; j = j + 1) // Find empty way\n")
        if self.data_hazard:
            self.vf.write("          if ((data_hazard && !new_tag[j * (TAG_WIDTH + 2) + TAG_WIDTH + 1]) || (!data_hazard && !tag_read_dout[j * (TAG_WIDTH + 2) + TAG_WIDTH + 1])) begin\n")
        else:
            self.vf.write("          if (!tag_read_dout[j * (TAG_WIDTH + 2) + TAG_WIDTH + 1]) begin\n")
        self.vf.write("            state_next     = 3;\n")
        self.vf.write("            way_next       = j;\n")
        self.vf.write("            tag_read_addr  = set; // needed in state 3 to keep other ways' tags\n")
        self.vf.write("            data_read_addr = set; // needed in state 3 to keep other ways' data\n")
        self.vf.write("            main_csb       = 0;\n")
        self.vf.write("            main_web       = 1;\n")
        self.vf.write("            main_addr      = {tag, set};\n")
        self.vf.write("          end\n")
        # Check if hit
        self.vf.write("        for (j = 0; j < WAY_DEPTH; j = j + 1) // Tag comparison\n")
        if self.data_hazard:
            self.vf.write("          if ((data_hazard && new_tag[j * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && new_tag[j * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag) || (!data_hazard && tag_read_dout[j * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && tag_read_dout[j * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag)) begin // Hit\n")
        else:
            self.vf.write("          if (tag_read_dout[j * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && tag_read_dout[j * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag) begin // Hit\n")
        self.vf.write("            stall      = 0;\n")
        self.vf.write("            state_next = 0; // If nothing is requested, go back to state 0\n")
        self.vf.write("            main_csb   = 1;\n")
        self.vf.write("            if (web_reg)\n")
        if self.data_hazard:
            self.vf.write("              if (data_hazard)\n")
            self.vf.write("                dout = new_data[j * LINE_WIDTH + offset * WORD_WIDTH +: WORD_WIDTH];\n")
            self.vf.write("              else\n")
            self.vf.write("                dout = data_read_dout[j * LINE_WIDTH + offset * WORD_WIDTH +: WORD_WIDTH];\n")
        else:
            self.vf.write("              dout = data_read_dout[j * LINE_WIDTH + offset * WORD_WIDTH +: WORD_WIDTH];\n")
        self.vf.write("            else begin\n")
        self.vf.write("              tag_write_csb   = 0;\n")
        self.vf.write("              tag_write_addr  = set;\n")
        self.vf.write("              data_write_csb  = 0;\n")
        self.vf.write("              data_write_addr = set;\n")
        if self.data_hazard:
            self.vf.write("              if (data_hazard) begin\n")
            self.vf.write("                tag_write_din  = new_tag;\n")
            self.vf.write("                data_write_din = new_data;\n")
            self.vf.write("              end else begin\n")
            self.vf.write("                tag_write_din  = tag_read_dout;\n")
            self.vf.write("                data_write_din = data_read_dout;\n")
            self.vf.write("              end\n")
        else:
            self.vf.write("              tag_write_din  = tag_read_dout;\n")
            self.vf.write("              data_write_din = data_read_dout;\n")
        self.vf.write("              tag_write_din[j * (2 + TAG_WIDTH) + TAG_WIDTH] = 1'b1;\n")
        self.vf.write("              for (i = 0; i < WORD_WIDTH; i = i + 1)\n")
        self.vf.write("                data_write_din[j * LINE_WIDTH + offset * WORD_WIDTH + i] = din_reg[i];\n")
        self.vf.write("            end\n")
        # Pipelining in state 1
        if self.pipeline:
            self.vf.write("            if (!csb) begin // Pipeline\n")
            self.vf.write("              state_next   = 1;\n")
            self.vf.write("              tag_next     = addr[ADDR_WIDTH-1 -: TAG_WIDTH];\n")
            self.vf.write("              set_next     = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("              offset_next  = addr[OFFSET_WIDTH-1:0];\n")
            self.vf.write("              web_reg_next = web;\n")
            self.vf.write("              din_reg_next = din;\n")
            if self.data_hazard:
                self.vf.write("              if (!web_reg && addr[OFFSET_WIDTH +: SET_WIDTH] == set) begin // Avoid data hazard\n")
                self.vf.write("                data_hazard_next = 1;\n")
                self.vf.write("                if (data_hazard) begin\n")
                self.vf.write("                  new_tag_next  = new_tag;\n")
                self.vf.write("                  new_data_next = new_data;\n")
                self.vf.write("                end else begin\n")
                self.vf.write("                  new_tag_next  = tag_read_dout;\n")
                self.vf.write("                  new_data_next = data_read_dout;\n")
                self.vf.write("                end\n")
                self.vf.write("                new_tag_next[j * (2 + TAG_WIDTH) + TAG_WIDTH] = 1'b1;\n")
                self.vf.write("                for (i = 0; i < WORD_WIDTH; i = i + 1)\n")
                self.vf.write("                  new_data_next[j * LINE_WIDTH + offset * WORD_WIDTH + i] = din_reg[i];\n")
                self.vf.write("              end else begin\n")
                self.vf.write("                tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
                self.vf.write("                data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
                self.vf.write("              end\n")
            else:
                self.vf.write("              tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
                self.vf.write("              data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("            end\n\n")
        self.vf.write("          end\n")
        self.vf.write("      end\n")

        # State 2
        # Cache waits in this state until lower memory’s stall signal becomes low. When it
        # is low, cache requests the new data line from the lower memory. State switches
        # to 3. Stall signal stays high.
        self.vf.write("      2: begin // STATE 2: Wait for main memory to write\n")
        self.vf.write("        tag_read_addr  = set; // needed in state 3 to keep other ways' tags\n")
        self.vf.write("        data_read_addr = set; // needed in state 3 to keep other ways' data\n")
        self.vf.write("        if (!main_stall) begin // Read line from main memory\n")
        self.vf.write("          state_next = 3;\n")
        self.vf.write("          main_csb   = 0;\n")
        self.vf.write("          main_addr  = {tag, set};\n")
        self.vf.write("        end\n")
        self.vf.write("      end\n")
    
        # State 3
        # Cache waits in this state until lower memory’s stall signal becomes low. When it
        # is low, cache sends new tag and data lines to internal arrays. If csb is low,
        # cache reads the next address from the pipeline and requests corresponding tag and
        # data lines from internal arrays. It avoids data hazard just like state 1. If csb
        # is high, state switches to 0; otherwise, it switches to 1.
        self.vf.write("      3: begin // STATE 3: Wait line from main memory\n")
        self.vf.write("        tag_read_addr  = set;\n")
        self.vf.write("        data_read_addr = set;\n")
        self.vf.write("        if (!main_stall) begin // Switch to state 1\n")
        self.vf.write("          stall          = 0;\n")
        self.vf.write("          state_next     = 0; // If nothing is requested, go back to state 0\n")
        self.vf.write("          tag_write_csb  = 0;\n")
        self.vf.write("          tag_write_addr = set;\n")
        self.vf.write("          tag_write_din  = tag_read_dout;\n")
        self.vf.write("          tag_write_din[way * (2 + TAG_WIDTH) + TAG_WIDTH]     = 1'b1;\n")
        self.vf.write("          tag_write_din[way * (2 + TAG_WIDTH) + TAG_WIDTH + 1] = ~web_reg;\n")
        self.vf.write("          for (k = 0; k < TAG_WIDTH; k = k + 1)\n")
        self.vf.write("            tag_write_din[way * (2 + TAG_WIDTH) + k] = tag[k];\n")
        self.vf.write("          data_write_csb  = 0;\n")
        self.vf.write("          data_write_addr = set;\n")
        self.vf.write("          data_write_din  = data_read_dout;\n")
        self.vf.write("          for (l = 0; l < LINE_WIDTH; l = l + 1)\n")
        self.vf.write("            data_write_din[way * LINE_WIDTH + l] = main_dout[l];\n")
        if self.data_hazard:
            self.vf.write("          new_tag_next  = 0;\n")
            self.vf.write("          new_data_next = 0;\n")
        self.vf.write("          if (web_reg)\n")
        self.vf.write("            dout = main_dout[offset * WORD_WIDTH +: WORD_WIDTH];\n")
        self.vf.write("          else\n")
        self.vf.write("            for (i = 0; i < WORD_WIDTH; i = i + 1)\n")
        self.vf.write("              data_write_din[way * LINE_WIDTH + offset * WORD_WIDTH + i] = din_reg[i];\n")
        # Pipelining in state 3
        if self.pipeline:
            self.vf.write("          if (!csb) begin // Pipeline\n")
            self.vf.write("            state_next   = 1;\n")
            self.vf.write("            tag_next     = addr[ADDR_WIDTH-1 -: TAG_WIDTH];\n")
            self.vf.write("            set_next     = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("            offset_next  = addr[OFFSET_WIDTH-1:0];\n")
            self.vf.write("            web_reg_next = web;\n")
            self.vf.write("            din_reg_next = din;\n")
            if self.data_hazard:
                self.vf.write("            if (addr[OFFSET_WIDTH +: SET_WIDTH] == set) begin // Avoid data hazard\n")
                self.vf.write("              data_hazard_next = 1;\n")
                self.vf.write("              new_tag_next     = tag_read_dout;\n")
                self.vf.write("              new_tag_next[way * (2 + TAG_WIDTH) + TAG_WIDTH]     = 1'b1;\n")
                self.vf.write("              new_tag_next[way * (2 + TAG_WIDTH) + TAG_WIDTH + 1] = ~web_reg;\n")
                self.vf.write("              for (k = 0; k < TAG_WIDTH; k = k + 1)\n")
                self.vf.write("                new_tag_next[way * (2 + TAG_WIDTH) + k] = tag[k];\n")
                self.vf.write("              new_data_next = data_read_dout;\n")
                self.vf.write("              for (l = 0; l < LINE_WIDTH; l = l + 1)\n")
                self.vf.write("                new_data_next[way * LINE_WIDTH + l] = main_dout[l];\n")
                self.vf.write("              if (!web_reg)\n")
                self.vf.write("                for (i = 0; i < WORD_WIDTH; i = i + 1)\n")
                self.vf.write("                  new_data_next[way * LINE_WIDTH + offset * WORD_WIDTH + i]  = din_reg[i];\n")
                self.vf.write("            end else begin\n")
                self.vf.write("              tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
                self.vf.write("              data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
                self.vf.write("            end            \n")
            else:
                self.vf.write("            tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
                self.vf.write("            data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n")
        self.vf.write("      end\n")
        self.vf.write("      endcase\n")
        self.vf.write("    end\n")
        self.vf.write("  end\n\n")
        self.vf.write("endmodule\n")