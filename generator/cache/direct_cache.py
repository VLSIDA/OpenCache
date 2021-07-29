# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from cache_base import cache_base
from nmigen import *
from nmigen.utils import log2_int
from rtl import State


class direct_cache(cache_base):
    """
    This is the design module of direct-mapped cache.
    """

    def __init__(self, cache_config, name):

        super().__init__(cache_config, name)


    def add_memory_controller_block(self, m):
        """ Add memory controller always block to cache design. """

        # In this block, cache communicates with memory components which are
        # tag array, data array, and main memory.

        # If rst is high, state switches to RESET.
        # Registers, which are reset only once, are reset here.
        # In the RESET state, cache will set all tag array lines to 0.
        with m.If(self.rst):
            m.d.comb += self.tag_write_csb.eq(0)
            m.d.comb += self.tag_write_addr.eq(0)
            m.d.comb += self.tag_write_din.eq(0)

        # If flush is high, state switches to FLUSH.
        # In the FLUSH state, cache will write all data lines back to main
        # memory.
        # TODO: Cache should write only dirty lines back.
        with m.Elif(self.flush):
            m.d.comb += self.tag_read_csb.eq(0)
            m.d.comb += self.tag_read_addr.eq(0)
            m.d.comb += self.data_read_csb.eq(0)
            m.d.comb += self.data_read_addr.eq(0)

        with m.Else():
            with m.Switch(self.state):

                # In the RESET state, cache sends write request to the tag array
                # to reset the current set.
                # set register is incremented by the Request Decode Block.
                # When set register reaches the end, state switches to IDLE.
                with m.Case(State.RESET):
                    m.d.comb += self.tag_write_csb.eq(0)
                    m.d.comb += self.tag_write_addr.eq(self.set)
                    m.d.comb += self.tag_write_din.eq(0)

                # In the FLUSH state, cache sends write request to main memory.
                # set register is incremented by the Request Decode Block.
                # When set register reaches the end, state switches to IDLE.
                # TODO: Cache should write only dirty lines back.
                with m.Case(State.FLUSH):
                    m.d.comb += self.tag_read_csb.eq(0)
                    m.d.comb += self.tag_read_addr.eq(self.set)
                    m.d.comb += self.data_read_csb.eq(0)
                    m.d.comb += self.data_read_addr.eq(self.set)
                    m.d.comb += self.main_csb.eq(0)
                    m.d.comb += self.main_web.eq(0)
                    m.d.comb += self.main_addr.eq(Cat(self.set, self.tag_read_dout[:self.tag_size+1]))
                    m.d.comb += self.main_din.eq(self.data_read_dout)
                    with m.If(~self.main_stall):
                        m.d.comb += self.tag_read_addr.eq(self.set + 1)
                        m.d.comb += self.data_read_addr.eq(self.set + 1)

                # In the IDLE state, cache waits for CPU to send a new request.
                # Until there is a new request from the cache, stall is low.
                # When there is a new request from the cache stall is asserted,
                # request is decoded and corresponding tag and data lines are
                # read from internal SRAM arrays.
                with m.Case(State.IDLE):
                    with m.If(~self.csb):
                        m.d.comb += self.tag_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))
                        m.d.comb += self.data_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))
                        # FIXME: Don't write 0 in testbench (might result in missed errors).
                        m.d.comb += self.data_write_din.eq(0)

                # In the COMPARE state, cache compares tags.
                with m.Case(State.COMPARE):
                    # Check if current request is hit
                    with m.If(
                        (self.bypass & self.new_tag[-1] & (self.new_tag[:self.tag_size] == self.tag)) | 
                        (~self.bypass & self.tag_read_dout[-1] & (self.tag_read_dout[:self.tag_size] == self.tag))
                    ):
                        # Perform the write request
                        with m.If(~self.web_reg):
                            m.d.comb += self.tag_write_csb.eq(0)
                            m.d.comb += self.tag_write_addr.eq(self.set)
                            m.d.comb += self.tag_write_din.eq(Cat(self.tag, Const(3, 2)))
                            m.d.comb += self.data_write_csb.eq(0)
                            m.d.comb += self.data_write_addr.eq(self.set)
                            # Use bypass registers if needed
                            m.d.comb += self.data_write_din.eq(Mux(self.bypass, self.new_data, self.data_read_dout))
                            # Write the word over the write mask
                            num_bytes = Const(self.num_bytes, log2_int(self.words_per_line))
                            for i in range(self.num_bytes):
                                with m.If(self.wmask_reg[i]):
                                    m.d.comb += self.data_write_din.word_select(self.offset * num_bytes + i, 8).eq(self.din_reg.word_select(i, 8))
                        # If CPU is sending a new request, read next lines from SRAMs
                        # Even if bypass registers are going to be used, read requests
                        # are sent to SRAMs since read is non-destructive (hopefully?).
                        with m.If(~self.csb):
                            m.d.comb += self.tag_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))
                            m.d.comb += self.data_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))
                    # Check if current request is dirty miss
                    with m.Elif(
                        (self.bypass & (self.new_tag[-2:] == Const(3, 2))) |
                        (~self.bypass & (self.tag_read_dout[-2:] == Const(3, 2)))
                    ):
                        # If main memory is busy, switch to WRITE and wait for main
                        # memory to be available.
                        with m.If(self.main_stall):
                            m.d.comb += self.tag_read_addr.eq(self.set)
                            m.d.comb += self.data_read_addr.eq(self.set)
                        # If main memory is available, switch to WAIT_WRITE and wait
                        # for main memory to complete writing.
                        with m.Else():
                            m.d.comb += self.main_csb.eq(0)
                            m.d.comb += self.main_web.eq(0)
                            # Use bypass registers if needed
                            with m.If(self.bypass):
                                m.d.comb += self.main_addr.eq(Cat(self.set, self.new_tag[:self.tag_size+1]))
                                m.d.comb += self.main_din.eq(self.new_data)
                            with m.Else():
                                m.d.comb += self.main_addr.eq(Cat(self.set, self.tag_read_dout[:self.tag_size+1]))
                                m.d.comb += self.main_din.eq(self.data_read_dout)
                    # Else, current request is clean a miss
                    with m.Else():
                        # If main memory is busy, switch to WRITE and wait for main
                        # memory to be available.
                        # If main memory is available, switch to WAIT_WRITE and wait
                        # for main memory to complete writing.
                        with m.If(~self.main_stall):
                            m.d.comb += self.main_csb.eq(0)
                            m.d.comb += self.main_addr.eq(Cat(self.set, self.tag))

                # In the WRITE state, cache waits for main memory to be available.
                # When main memory is available, write request is sent.
                with m.Case(State.WRITE):
                    m.d.comb += self.tag_read_addr.eq(self.set)
                    m.d.comb += self.data_read_addr.eq(self.set)
                    # If main memory is busy, wait in this state.
                    # If main memory is available, switch to WAIT_WRITE and wait for
                    # main memory to complete writing.
                    with m.If(~self.main_stall):
                        m.d.comb += self.main_csb.eq(0)
                        m.d.comb += self.main_web.eq(0)
                        m.d.comb += self.main_addr.eq(Cat(self.set, self.tag_read_dout[:self.tag_size+1]))
                        m.d.comb += self.main_din.eq(self.data_read_dout)

                # In the WAIT_WRITE state, cache waits for main memory to complete
                # writing.
                # When main memory completes writing, read request is sent.
                with m.Case(State.WAIT_WRITE):
                    # If main memory is busy, wait in this state.
                    # If main memory completes writing, switch to WAIT_READ and wait
                    # for main memory to complete reading.
                    with m.If(~self.main_stall):
                        m.d.comb += self.main_csb.eq(0)
                        m.d.comb += self.main_addr.eq(Cat(self.set, self.tag))

                # In the READ state, cache waits for main memory to be available.
                # When main memory is available, read request is sent.
                # TODO: Is this state really necessary? WAIT_WRITE state may be used instead.
                with m.Case(State.READ):
                    # If main memory is busy, wait in this state.
                    # If main memory completes writing, switch to WAIT_READ and wait
                    # for main memory to complete reading.
                    with m.If(~self.main_stall):
                        m.d.comb += self.main_csb.eq(0)
                        m.d.comb += self.main_addr.eq(Cat(self.set, self.tag))

                # In the WAIT_READ state, cache waits for main memory to complete
                # reading.
                # When main memory completes reading, request is completed.
                with m.Case(State.WAIT_READ):
                    # If main memory is busy, cache waits in this state.
                    # If main memory completes reading, cache switches to:
                    #   IDLE    if CPU isn't sending a new request
                    #   COMPARE if CPU is sending a new request
                    with m.If(~self.main_stall):
                        # TODO: Use wmask feature of OpenRAM.
                        m.d.comb += self.tag_write_csb.eq(0)
                        m.d.comb += self.tag_write_addr.eq(self.set)
                        m.d.comb += self.tag_write_din.eq(Cat(self.tag, ~self.web_reg, Const(1, 1)))
                        m.d.comb += self.data_write_csb.eq(0)
                        m.d.comb += self.data_write_addr.eq(self.set)
                        m.d.comb += self.data_write_din.eq(self.main_dout)
                        # Perform the write request
                        with m.If(~self.web_reg):
                            # Write the word over the write mask
                            num_bytes = Const(self.num_bytes, log2_int(self.words_per_line))
                            for i in range(self.num_bytes):
                                with m.If(self.wmask_reg[i]):
                                    m.d.comb += self.data_write_din.word_select(self.offset * num_bytes + i, 8).eq(self.din_reg.word_select(i, 8))
                        # If CPU is sending a new request, read next lines from SRAMs
                        # Even if bypass registers are going to be used, read requests
                        # are sent to SRAMs since read is non-destructive (hopefully?).
                        with m.If(~self.csb):
                            m.d.comb += self.tag_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))
                            m.d.comb += self.data_read_addr.eq(self.addr.bit_select(self.offset_size, self.set_size))


    def add_state_block(self, m):
        """ Add state controller always block to cache design. """

        # In this block, cache's state is controlled. state flip-flop
        # register is changed in order to switch between states.

        m.d.comb += self.state_next.eq(self.state)

        # If rst is high, state switches to RESET.
        with m.If(self.rst):
            m.d.comb += self.state_next.eq(State.RESET)

        # If flush is high, state switches to FLUSH.
        with m.Elif(self.flush):
            m.d.comb += self.state_next.eq(State.FLUSH)

        with m.Else():
            with m.Switch(self.state):

                # In the RESET state, state switches to IDLE if reset is completed.
                with m.Case(State.RESET):
                    # When set reaches the limit, the last write request is sent
                    # to the tag array.
                    with m.If(self.set == self.num_rows - 1):
                        m.d.comb += self.state_next.eq(State.IDLE)

                # In the FLUSH state, state switches to IDLE if flush is completed.
                with m.Case(State.FLUSH):
                    # If main memory completes the last write request, flush is
                    # completed.
                    with m.If(~self.main_stall & (self.set == self.num_rows - 1)):
                        m.d.comb += self.state_next.eq(State.IDLE)

                # In the IDLE state, state switches to COMPARE if CPU is sending
                # a new request.
                with m.Case(State.IDLE):
                    with m.If(~self.csb):
                        m.d.comb += self.state_next.eq(State.COMPARE)

                # In the COMPARE state, state switches to:
                #   IDLE       if current request is hit and CPU isn't sending a new request
                #   COMPARE    if current request is hit and CPU is sending a new request
                #   WRITE      if current request is dirty miss and main memory is busy
                #   WAIT_WRITE if current request is dirty miss and main memory is available
                #   READ       if current request is clean a miss and main memory is busy
                #   WAIT_READ  if current request is clean a miss and main memory is available
                with m.Case(State.COMPARE):
                    # Check if current request is hit
                    with m.If(
                        (self.bypass & self.new_tag[-1] & (self.new_tag[:self.tag_size] == self.tag)) | 
                        (~self.bypass & self.tag_read_dout[-1] & (self.tag_read_dout[:self.tag_size] == self.tag))
                    ):
                        with m.If(self.csb):
                            m.d.comb += self.state_next.eq(State.IDLE)
                        with m.Else():
                            m.d.comb += self.state_next.eq(State.COMPARE)
                    # Check if current request is dirty miss
                    with m.Elif(
                        (self.bypass & (self.new_tag[-2:] == Const(3, 2))) |
                        (~self.bypass & (self.tag_read_dout[-2:] == Const(3, 2)))
                    ):
                        with m.If(self.csb):
                            m.d.comb += self.state_next.eq(State.WRITE)
                        with m.Else():
                            m.d.comb += self.state_next.eq(State.WAIT_WRITE)
                    # Else, current request is clean a miss
                    with m.Else():
                        with m.If(self.csb):
                            m.d.comb += self.state_next.eq(State.READ)
                        with m.Else():
                            m.d.comb += self.state_next.eq(State.WAIT_READ)

                # In the WRITE state, state switches to:
                #   WRITE      if main memory didn't respond yet
                #   WAIT_WRITE if main memory responded
                with m.Case(State.WRITE):
                    with m.If(~self.main_stall):
                        m.d.comb += self.state_next.eq(State.WAIT_WRITE)

                # In the WAIT_WRITE state, state switches to:
                #   WAIT_WRITE if main memory didn't respond yet
                #   WAIT_READ  if main memory responded
                with m.Case(State.WAIT_WRITE):
                    with m.If(~self.main_stall):
                        m.d.comb += self.state_next.eq(State.WAIT_READ)

                # In the READ state, state switches to:
                #   READ      if main memory didn't respond yet
                #   WAIT_READ if main memory responded
                with m.Case(State.READ):
                    with m.If(~self.main_stall):
                        m.d.comb += self.state_next.eq(State.WAIT_READ)

                # In the WAIT_READ state, state switches to:
                #   IDLE    if CPU isn't sending a new request
                #   COMPARE if CPU is sending a new request
                with m.Case(State.WAIT_READ):
                    with m.If(~self.main_stall):
                        with m.If(self.csb):
                            m.d.comb += self.state_next.eq(State.IDLE)
                        with m.Else():
                            m.d.comb += self.state_next.eq(State.COMPARE)


    def add_request_block(self, m):
        """ Add request decode always block to cache design. """

        # In this block, CPU's request is decoded. Address is parsed
        # into tag, set and offset values, and write enable and data
        # input are saved in registers.

        m.d.comb += self.tag_next.eq(self.tag)
        m.d.comb += self.set_next.eq(self.set)
        m.d.comb += self.offset_next.eq(self.offset)
        m.d.comb += self.web_reg_next.eq(self.web_reg)
        m.d.comb += self.wmask_reg_next.eq(self.wmask_reg)
        m.d.comb += self.din_reg_next.eq(self.din_reg)

        # If rst is high, input registers are reset.
        # set register becomes 1 since it is going to be used to reset
        # all lines in the tag array.
        with m.If(self.rst):
            m.d.comb += self.tag_next.eq(0)
            m.d.comb += self.set_next.eq(1)
            m.d.comb += self.offset_next.eq(0)
            m.d.comb += self.web_reg_next.eq(1)
            m.d.comb += self.wmask_reg_next.eq(0)
            m.d.comb += self.din_reg_next.eq(0)

        # If flush is high, input registers are not reset.
        # However, set register becomes 0 since it is going to be used to
        # write dirty lines back to main memory.
        with m.Elif(self.flush):
            m.d.comb += self.set_next.eq(0)

        with m.Else():
            with m.Switch(self.state):

                # In the RESET state, set register is used to reset all lines in
                # the tag array.
                with m.Case(State.RESET):
                    m.d.comb += self.set_next.eq(self.set + 1)

                # In the FLUSH state, set register is used to write all dirty lines
                # back to main memory.
                with m.Case(State.FLUSH):
                    with m.If(~self.main_stall):
                        m.d.comb += self.set_next.eq(self.set + 1)

                # In the IDLE state, the request is decoded.
                with m.Case(State.IDLE):
                    m.d.comb += self.tag_next.eq(self.addr[-self.tag_size:])
                    m.d.comb += self.set_next.eq(self.addr.bit_select(self.offset_size, self.set_size))
                    m.d.comb += self.offset_next.eq(self.addr[:self.offset_size+1])
                    m.d.comb += self.web_reg_next.eq(self.web)
                    m.d.comb += self.wmask_reg_next.eq(self.wmask)
                    m.d.comb += self.din_reg_next.eq(self.din)

                # In the COMPARE state, the request is decoded if current request
                # is hit.
                with m.Case(State.COMPARE):
                    with m.If(
                        (self.bypass & self.new_tag[-1] & (self.new_tag[:self.tag_size] == self.tag)) | 
                        (~self.bypass & self.tag_read_dout[-1] & (self.tag_read_dout[:self.tag_size] == self.tag))
                    ):
                        m.d.comb += self.tag_next.eq(self.addr[-self.tag_size:])
                        m.d.comb += self.set_next.eq(self.addr.bit_select(self.offset_size, self.set_size))
                        m.d.comb += self.offset_next.eq(self.addr[:self.offset_size+1])
                        m.d.comb += self.web_reg_next.eq(self.web)
                        m.d.comb += self.wmask_reg_next.eq(self.wmask)
                        m.d.comb += self.din_reg_next.eq(self.din)

                # In the COMPARE state, the request is decoded if main memory
                # completed read request.
                with m.Case(State.WAIT_READ):
                    with m.If(~self.main_stall):
                        m.d.comb += self.tag_next.eq(self.addr[-self.tag_size:])
                        m.d.comb += self.set_next.eq(self.addr.bit_select(self.offset_size, self.set_size))
                        m.d.comb += self.offset_next.eq(self.addr[:self.offset_size+1])
                        m.d.comb += self.web_reg_next.eq(self.web)
                        m.d.comb += self.wmask_reg_next.eq(self.wmask)
                        m.d.comb += self.din_reg_next.eq(self.din)


    def add_output_block(self, m):
        """ Add the output always block to cache design. """

        # In this block, cache's output signals, which are stall and
        # dout, are controlled.

        m.d.comb += self.stall.eq(1)
        # FIXME: Don't write 0 in testbench (might result in missed errors).
        m.d.comb += self.dout.eq(0)

        with m.Switch(self.state):

            # In the IDLE state, stall is low while there is no request from
            # the CPU. When there is a request, state switches to COMPARE and
            # stall becomes high in the next cycle.
            with m.Case(State.IDLE):
                m.d.comb += self.stall.eq(0)

            # In the COMPARE state, stall is low if the current request is hit.
            # Data output is valid if the request is hit and even if the current
            # request is write since read is non-destructive.
            with m.Case(State.COMPARE):
                # Check if current request is hit
                with m.If(
                    (self.bypass & self.new_tag[-1] & (self.new_tag[:self.tag_size] == self.tag)) | 
                    (~self.bypass & self.tag_read_dout[-1] & (self.tag_read_dout[:self.tag_size] == self.tag))
                ):
                    m.d.comb += self.stall.eq(0)
                    # Use bypass registers if needed
                    with m.If(self.bypass):
                        m.d.comb += self.dout.eq(self.new_data.word_select(self.offset, self.word_size))
                    with m.Else():
                        m.d.comb += self.dout.eq(self.data_read_dout.word_select(self.offset, self.word_size))

            # In the WAIT_READ state, stall is low and data output is valid when
            # main memory completes the read request.
            # Data output is valid even if the current request is write since read
            # is non-destructive.
            # NOTE: No need to use bypass registers here since data hazard is not
            # possible. Data is coming from main memory.
            with m.Case(State.WAIT_READ):
                # Check if main memory answers to the read request
                with m.If(~self.main_stall):
                    m.d.comb += self.stall.eq(0)
                    m.d.comb += self.dout.eq(self.main_dout.word_select(self.offset, self.word_size))


    def add_bypass_block(self, m):
        """ Add bypass register always block to cache design. """

        # In this block, bypass registers are controlled.
        # Bypass registers are used to prevent data hazard from SRAMs.
        # Data hazard can occur when there are read and write requests
        # to the same row at the same cycle.

        m.d.comb += self.bypass_next.eq(0)
        m.d.comb += self.new_tag_next.eq(0)
        m.d.comb += self.new_data_next.eq(0)

        with m.Switch(self.state):

            # In the COMPARE state, bypass registers can be used in the next
            # cycle if the current request is hit and write.
            # Otherwise, bypass registers won't probably be used; therefore,
            # will be reset.
            with m.Case(State.COMPARE):
                # Check if:
                #   CPU is sending a new request
                #   Current request is hit
                #   Current request is write
                #   Next address is in the same set
                with m.If(
                    ~self.csb &
                    ~self.web_reg &
                    (self.set == self.addr.bit_select(self.offset_size, self.set_size)) &
                    ((self.bypass & self.new_tag[-1] & (self.new_tag[:self.tag_size] == self.tag)) | (~self.bypass & self.tag_read_dout[-1] & (self.tag_read_dout[:self.tag_size] == self.tag)))
                ):
                    # Enable bypass registers
                    m.d.comb += self.bypass_next.eq(1)
                    m.d.comb += self.new_tag_next.eq(Cat(self.tag, Const(3, 2)))
                    with m.If(self.bypass):
                        m.d.comb += self.new_data_next.eq(self.new_data)
                    with m.Else():
                        m.d.comb += self.new_data_next.eq(self.data_read_dout)
                    # Write the word over the write mask
                    num_bytes = Const(self.num_bytes, log2_int(self.words_per_line))
                    for i in range(self.num_bytes):
                        with m.If(self.wmask_reg[i]):
                            m.d.comb += self.new_data_next.word_select(self.offset * num_bytes + i, 8).eq(self.din_reg.word_select(i, 8))

            # In the WAIT_READ state, bypass registers will be used in the next
            # cycle if the next request is in the same set.
            # Otherwise, bypass registers won't probably be used; therefore, will
            # be reset.
            # NOTE: No need to use bypass registers here since data hazard is not
            # possible. Data is coming from main memory.
            with m.Case(State.WAIT_READ):
                # Check if:
                #   CPU is sending a new request
                #   Next address is in the same set
                with m.If(~self.main_stall & ~self.csb & (self.set == self.addr.bit_select(self.offset_size, self.set_size))):
                    m.d.comb += self.bypass_next.eq(1)
                    m.d.comb += self.new_tag_next.eq(Cat(self.tag, ~self.web_reg, Const(1, 1)))
                    m.d.comb += self.new_data_next.eq(self.main_dout)
                    # Perform the write request
                    with m.If(~self.web_reg):
                        # Write the word over the write mask
                        num_bytes = Const(self.num_bytes, log2_int(self.words_per_line))
                        for i in range(self.num_bytes):
                            with m.If(self.wmask_reg[i]):
                                m.d.comb += self.new_data_next.word_select(self.offset * num_bytes + i, 8).eq(self.din_reg.word_select(i, 8))