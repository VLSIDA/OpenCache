import cache.cache_base


class n_way_lru_cache(cache_base):
    """
    This is the design module of N-way set associative cache
    with LRU replacement policy.
    """
    def __init__(self, name, cache_config):

        super().__init__(name, cache_config)


    def config_write(self, config_path):
        """ Write the configuration files for OpenRAM SRAM arrays. """

        super().config_write(config_path)

        self.fcf = open(config_path + "_lru_array_config.py", "w")
        self.fcf.write("word_size = {}\n".format(self.way_width * self.num_ways))
        self.fcf.write("num_words = {}\n".format(self.num_rows))
        # OpenRAM outputs of the LRU array are saved to a separate folder
        self.fcf.write("output_path = \"{}/lru_array\"\n".format(config_path))
        self.fcf.write("output_name = \"{}_lru_array\"\n".format(self.name))
        self.fcf.close()


    def write_parameters(self):
        """ Write the parameters of the cache. """

        super().write_parameters()

        # These parameters are used to update LRU bits
        self.vf.write("  // These are used in LRU multiplexer.\n")
        for i in range(self.num_ways):
            self.vf.write("  localparam NUM_{0} = {0};\n".format(i))
        self.vf.write("\n")


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
        self.vf.write("  reg [1:0]              state, state_next; // state is used while reading/writing main memory\n")
        self.vf.write("  reg [WAY_WIDTH-1:0]    way, way_next;     // to place in a way\n")
        # No need for bypass registers if SRAMs are guaranteed to be data hazard proof
        if self.data_hazard:
            self.vf.write("  // When the next fetch is in the same set, tag_array and data_array might be old (data hazard).\n")
            self.vf.write("  reg data_hazard, data_hazard_next; // high if write and read from arrays must be done at the same cycle\n")
            self.vf.write("  reg [WAY_WIDTH * WAY_DEPTH-1:0]       new_lru, new_lru_next;   // new replacement bits from the previous cycle\n")
            self.vf.write("  reg [(2 + TAG_WIDTH) * WAY_DEPTH-1:0] new_tag, new_tag_next;   // new tag line from the previous cycle\n")
            self.vf.write("  reg [LINE_WIDTH * WAY_DEPTH-1:0]      new_data, new_data_next; // new data line from the previous cycle\n\n")

        self.vf.write("  // source memory ports\n")
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

        self.vf.write("  // tag array read port\n")
        self.vf.write("  reg  tag_read_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] tag_read_addr;\n")
        self.vf.write("  wire [(2 + TAG_WIDTH) * WAY_DEPTH-1:0] tag_read_dout;\n")
        self.vf.write("  // tag array write port\n")
        self.vf.write("  reg  tag_write_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] tag_write_addr;\n")
        self.vf.write("  reg  [(2 + TAG_WIDTH) * WAY_DEPTH-1:0] tag_write_din;\n\n")

        self.vf.write("  // data array read port\n")
        self.vf.write("  reg  data_read_csb;\n")
        self.vf.write("  reg  [SET_WIDTH-1:0] data_read_addr;\n")
        self.vf.write("  wire [LINE_WIDTH * WAY_DEPTH-1:0] data_read_dout;\n")
        self.vf.write("  // data array write port\n")
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
        self.vf.write("    rst_reg     <= #(DELAY) rst_reg_next;\n")
        self.vf.write("    web_reg     <= #(DELAY) web_reg_next;\n")
        self.vf.write("    din_reg     <= #(DELAY) din_reg_next;\n")
        if self.data_hazard:
            self.vf.write("    data_hazard <= #(DELAY) data_hazard_next;\n")
            self.vf.write("    new_lru     <= #(DELAY) new_lru_next;\n")
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
        self.vf.write("  integer l; // Used in for loops since indexed part select is illegal (data line)\n")
        self.vf.write("  integer m; // Used in for loops to update LRU bits\n")
        self.vf.write("  integer n; // Used in for loops since indexed part select is illegal (way)\n\n")


    def write_logic_block(self):
        """ Write the logic always block of the cache. """

        self.vf.write("  always @* begin\n")
        self.vf.write("    dout             = {{WORD_WIDTH{{1'bx}}}};\n")
        self.vf.write("    stall            = 1;\n")
        self.vf.write("    state_next       = state;\n")
        self.vf.write("    way_next         = way;\n")
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
        self.vf.write("    lru_read_csb     = 0;\n")
        self.vf.write("    lru_read_addr    = 0;\n")
        self.vf.write("    lru_write_csb    = 1;\n")
        self.vf.write("    lru_write_addr   = 0;\n")
        self.vf.write("    lru_write_din    = 0;\n")
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
            self.vf.write("    new_lru_next     = new_lru;\n")
            self.vf.write("    new_tag_next     = new_tag;\n")
            self.vf.write("    new_data_next    = new_data;\n")

        # Reset state
        # This is a multi-cycle reset. It sets all rows of the internal arrays to 0.
        # Cache enters this state when rst signal is high. Until it exits the state,
        # stall signal is high.
        self.vf.write("    if (rst || rst_reg) begin // RESET: Multi-cycle reset\n")
        self.vf.write("      state_next = 0;\n")
        self.vf.write("      tag_next   = 0;\n")
        self.vf.write("      set_next   = 1;\n")
        self.vf.write("      if (rst_reg)\n")
        self.vf.write("        set_next = set + 1;\n")
        self.vf.write("      offset_next   = 0;\n")
        self.vf.write("      web_reg_next  = 1;\n")
        self.vf.write("      rst_reg_next  = 1;\n")
        self.vf.write("      din_reg_next  = 0;\n")
        self.vf.write("      lru_write_csb = 0;\n")
        self.vf.write("      tag_write_csb = 0;\n")
        self.vf.write("      if (rst_reg) begin\n")
        self.vf.write("        lru_write_addr = set;\n")
        self.vf.write("        tag_write_addr = set;\n")
        self.vf.write("      end\n")
        self.vf.write("      if (rst_reg && set == CACHE_DEPTH - 1) begin\n")
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
        self.vf.write("      IDLE_STATE: begin // Read tag line\n")
        self.vf.write("        stall = 0;\n")
        self.vf.write("        if (!csb) begin\n")
        self.vf.write("          state_next       = 1;\n")
        self.vf.write("          way_next         = 0;\n")
        self.vf.write("          tag_next         = addr[ADDR_WIDTH-1 -: TAG_WIDTH];\n")
        self.vf.write("          set_next         = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("          offset_next      = addr[OFFSET_WIDTH-1:0];\n")
        if self.data_hazard:
            self.vf.write("          data_hazard_next = 0;\n")
            self.vf.write("          new_lru_next     = 0;\n")
            self.vf.write("          new_tag_next     = 0;\n")
            self.vf.write("          new_data_next    = 0;\n")
        self.vf.write("          web_reg_next     = web;\n")
        self.vf.write("          din_reg_next     = din;\n")
        self.vf.write("          lru_read_addr    = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
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
        self.vf.write("      CHECK_STATE: begin // Check if hit/miss\n")
        if self.data_hazard:
            self.vf.write("        data_hazard_next = 0;\n")
            self.vf.write("        new_lru_next     = 0;\n")
            self.vf.write("        new_tag_next     = 0;\n")
            self.vf.write("        new_data_next    = 0;\n")
        self.vf.write("        for (j = 0; j < WAY_DEPTH; j = j + 1) begin // Miss\n")
        if self.data_hazard:
            self.vf.write("          if ((data_hazard && !new_lru[j * WAY_WIDTH +: WAY_WIDTH]) || (!data_hazard && !lru_read_dout[j * WAY_WIDTH +: WAY_WIDTH])) begin // Find the LRU way\n")
        else:
            self.vf.write("          if (!lru_read_dout[j * WAY_WIDTH +: WAY_WIDTH]) begin // Find the LRU way\n")
        self.vf.write("            way_next = j;\n")
        if self.data_hazard:
            self.vf.write("            if ((data_hazard && new_tag[j * (TAG_WIDTH + 2) + TAG_WIDTH +: 2] == 2'b11) || (!data_hazard && tag_read_dout[j * (TAG_WIDTH + 2) + TAG_WIDTH +: 2] == 2'b11)) begin // Miss (valid and dirty)\n")
        else:
            self.vf.write("            if (tag_read_dout[j * (TAG_WIDTH + 2) + TAG_WIDTH +: 2] == 2'b11) begin // Miss (valid and dirty)\n")
        self.vf.write("              state_next = 2;\n")
        self.vf.write("              main_csb   = 0;\n")
        self.vf.write("              main_web   = 0;\n")
        if self.data_hazard:
            self.vf.write("              if (data_hazard) begin\n")
            self.vf.write("                main_addr = {new_tag[j * (TAG_WIDTH + 2) +: TAG_WIDTH], set};\n")
            self.vf.write("                main_din  = new_data[j * LINE_WIDTH +: LINE_WIDTH];\n")
            self.vf.write("              end else begin\n")
            self.vf.write("                main_addr = {tag_read_dout[j * (TAG_WIDTH + 2) +: TAG_WIDTH], set};\n")
            self.vf.write("                main_din  = data_read_dout[j * LINE_WIDTH +: LINE_WIDTH];\n")
            self.vf.write("              end\n")
        else:
            self.vf.write("              main_addr = {tag_read_dout[j * (TAG_WIDTH + 2) +: TAG_WIDTH], set};\n")
            self.vf.write("              main_din  = data_read_dout[j * LINE_WIDTH +: LINE_WIDTH];\n")
        self.vf.write("            end else begin // Miss (not valid or not dirty)\n")
        self.vf.write("              state_next     = 3;\n")
        self.vf.write("              lru_read_addr  = set; // needed in state 3 to update LRU bits\n")
        self.vf.write("              tag_read_addr  = set; // needed in state 3 to keep other ways' tags\n")
        self.vf.write("              data_read_addr = set; // needed in state 3 to keep other ways' data\n")
        self.vf.write("              main_csb       = 0;\n")
        self.vf.write("              main_addr      = {tag, set};\n")
        self.vf.write("            end\n")
        self.vf.write("          end\n")
        self.vf.write("        end\n")
        # Check if hit
        self.vf.write("        for (j = 0; j < WAY_DEPTH; j = j + 1) // Tag comparison\n")
        if self.data_hazard:
            self.vf.write("          if ((data_hazard && new_tag[j * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && new_tag[j * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag) || (!data_hazard && tag_read_dout[j * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && tag_read_dout[j * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag)) begin // Hit\n")
        else:
            self.vf.write("          if (tag_read_dout[j * (TAG_WIDTH + 2) + TAG_WIDTH + 1] && tag_read_dout[j * (TAG_WIDTH + 2) +: TAG_WIDTH] == tag) begin // Hit\n")
        self.vf.write("            stall          = 0;\n")
        self.vf.write("            state_next     = 0; // If nothing is requested, go back to state 0\n")
        self.vf.write("            main_csb       = 1;\n")
        self.vf.write("            lru_write_csb  = 0;\n")
        self.vf.write("            lru_write_addr = 0;\n")
        if self.data_hazard:
            self.vf.write("            if (data_hazard) begin\n")
            self.write_lru_mux(7, True, False)
            self.vf.write("            end else begin\n")
            self.write_lru_mux(7, False, False)
            self.vf.write("            end\n")
        else:
            self.write_lru_mux(6, False, False)
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
        self.vf.write("            if (!csb) begin // Pipeline\n")
        self.vf.write("              state_next   = 1;\n")
        self.vf.write("              tag_next     = addr[ADDR_WIDTH-1 -: TAG_WIDTH];\n")
        self.vf.write("              set_next     = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("              offset_next  = addr[OFFSET_WIDTH-1:0];\n")
        self.vf.write("              web_reg_next = web;\n")
        self.vf.write("              din_reg_next = din;\n")
        if self.data_hazard:
            self.vf.write("              if (addr[OFFSET_WIDTH +: SET_WIDTH] == set) begin // Avoid data hazard\n")
            self.vf.write("                data_hazard_next = 1;\n")
            self.vf.write("                if (data_hazard) begin\n")
            self.write_lru_mux(9, True, True)
            self.vf.write("                  new_tag_next  = new_tag;\n")
            self.vf.write("                  new_data_next = new_data;\n")
            self.vf.write("                end else begin\n")
            self.write_lru_mux(9, False, True)
            self.vf.write("                  new_tag_next  = tag_read_dout;\n")
            self.vf.write("                  new_data_next = data_read_dout;\n")
            self.vf.write("                end\n")
            self.vf.write("                new_tag_next[j * (2 + TAG_WIDTH) + TAG_WIDTH] = 1'b1;\n")
            self.vf.write("                if (!web_reg)\n")
            self.vf.write("                  for (i = 0; i < WORD_WIDTH; i = i + 1)\n")
            self.vf.write("                    new_data_next[j * LINE_WIDTH + offset * WORD_WIDTH + i] = din_reg[i];\n")
            self.vf.write("              end else begin\n")
            self.vf.write("                lru_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("                tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("                data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("              end              \n")
        else:
            self.vf.write("              lru_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("              tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("              data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("            end\n")
        self.vf.write("          end\n")
        self.vf.write("      end\n")

        # State 2
        # Cache waits in this state until lower memory’s stall signal becomes low. When it
        # is low, cache requests the new data line from the lower memory. State switches
        # to 3. Stall signal stays high.
        self.vf.write("      WRITE_STATE: begin // Wait for main memory to write\n")
        self.vf.write("        lru_read_addr  = set; // needed in state 3 to update LRU bits\n")
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
        self.vf.write("      READ_STATE: begin // Wait line from main memory\n")
        self.vf.write("        lru_read_addr  = set;\n")
        self.vf.write("        tag_read_addr  = set;\n")
        self.vf.write("        data_read_addr = set;\n")
        self.vf.write("        if (!main_stall) begin // Switch to state 1\n")
        self.vf.write("          stall          = 0;\n")
        self.vf.write("          state_next     = 0; // If nothing is requested, go back to state 0\n")
        self.vf.write("          lru_write_csb  = 0;\n")
        self.vf.write("          lru_write_addr = set;\n")
        self.write_lru_mux(5, False, False)
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
            self.write(7, True, True)
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
            self.vf.write("              lru_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("              tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("              data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("            end\n")
        else:
            self.vf.write("            lru_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("            tag_read_addr  = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
            self.vf.write("            data_read_addr = addr[OFFSET_WIDTH +: SET_WIDTH];\n")
        self.vf.write("          end\n")
        self.vf.write("          end\n")
        self.vf.write("      end\n")
        self.vf.write("      endcase\n")
        self.vf.write("    end\n")
        self.vf.write("  end\n\n")
        self.vf.write("endmodule\n")


    def write_lru_mux(self, base_indent, data_hazard, update_bypass_regs):
        """ Write a multiplexer to update LRU bits of the cache. """

        if type(base_indent) == int:
            base_indent *= "  "

        if data_hazard:
            rhs = "new_lru"
        else:
            rhs = "lru_read_dout"

        # If there is no data hazard, no need for bypass registers
        if data_hazard and update_bypass_regs:
            lhs = "new_lru_next"
        else:
            lhs = "lru_write_din"

        self.vf.write(base_indent + "{0} = {1};\n".format(lhs, rhs))
        self.vf.write(base_indent + "for (m = 0; m < WAY_DEPTH; m = m + 1) begin // Update LRU bits\n")
        self.vf.write(base_indent + "  if (j == m) begin\n")
        self.vf.write(base_indent + "    for (n = 0; n < WAY_WIDTH; n = n + 1)\n")
        self.vf.write(base_indent + "      {0}[j * WAY_WIDTH + n] = NUM_{1}[n];\n".format(lhs, self.num_ways - 1))
        self.vf.write(base_indent + "  end else if ({0}[m * WAY_WIDTH +: WAY_WIDTH] > {0}[j * WAY_WIDTH +: WAY_WIDTH]) begin\n".format(rhs))
        self.vf.write(base_indent + "    for (n = 0; n < WAY_WIDTH; n = n + 1) begin\n")
        self.vf.write(base_indent + "      case({}[m * WAY_WIDTH +: WAY_WIDTH])\n".format(rhs))
        self.vf.write(base_indent + "      0: {}[m * WAY_WIDTH + n] = NUM_0[n];\n".format(lhs))
        for i in range(self.num_ways - 1)
            self.vf.write(base_indent + "      {0}: {1}[m * WAY_WIDTH + n] = NUM_{2}[n];\n".format(i + 1, lhs, i))
        self.vf.write(base_indent + "      endcase\n")
        self.vf.write(base_indent + "    end\n")
        self.vf.write(base_indent + "  end\n")
        self.vf.write(base_indent + "end\n")