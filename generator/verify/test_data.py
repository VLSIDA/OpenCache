# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from random import randrange, choice
from sim_cache import sim_cache


class test_data:
    """
    Class to generate the test data file for simulation.
    """

    def __init__(self, cache_config, name):

        cache_config.set_local_config(self)
        self.name = name
        self.sc = sim_cache(cache_config)


    def generate_data(self):
        """  Generate random test data and expected outputs. """

        test_size = 2
        self.web  = []
        self.addr = []
        self.data = []

        # TODO: How to create random data in a smart way?
        # Write random data to random addresses initially
        for i in range(test_size):
            self.web.append(0)
            self.addr.append(randrange(2 ** self.address_size))
            self.data.append(randrange(2 ** self.word_size))

        indices = list(range(test_size))

        # Read from random addresses which are written to in the first half
        while len(indices) > 0:
            index = choice(indices)

            self.web.append(1)
            self.addr.append(self.addr[index])
            self.data.append(self.data[index])

            indices.remove(index)

        # Insert noop entries for miss stalls
        i = 0
        while i < len(self.web):
            stall_cycles = 0
            if not self.sc.is_hit(self.addr[i]):
                stall_cycles = 4 * (2 if self.sc.is_dirty(self.addr[i]) else 1)

                self.web[i+1:i+1]  = [None] * stall_cycles
                self.addr[i+1:i+1] = [None] * stall_cycles
                self.data[i+1:i+1] = [None] * stall_cycles

            if self.web[i]:
                self.sc.read(self.addr[i])
            else:
                self.sc.write(self.addr[i], self.data[i])

            i += stall_cycles + 1


    def write(self, data_path):
        """ Write the test data file. """

        pipeline_filled = False
        prev_delayed    = False
        test_count      = 0

        self.tdf = open(data_path, "w")
        self.tdf.write("// Initial delay to align with the cache and SRAMs.\n")
        self.tdf.write("// SRAMs return data at the negedge of the clock.\n")
        self.tdf.write("// Therefore, cache's output will be valid at the negedge.\n")
        self.tdf.write("#(CLOCK_DELAY + DELAY + 1);\n\n")

        # Check delay during reset
        for i in range(self.num_rows - 2):
            self.tdf.write("// No operation (Test #{}, reset)\n".format(test_count))
            self.tdf.write("#(CLOCK_DELAY * 2);\n")
            self.tdf.write("check_stall({});\n\n".format(test_count))

            test_count += 1

        # Check requests
        i = 0
        while i < len(self.web):
            self.tdf.write("// {0} operation (Test #{1})\n".format("Read" if self.web[i] else "Write",
                                                                   test_count))

            if not prev_delayed:
                self.tdf.write("#(CLOCK_DELAY * 2);\n")

            prev_delayed = False

            self.tdf.write("cache_csb  = 0;\n")
            self.tdf.write("cache_web  = {};\n".format(self.web[i]))
            self.tdf.write("cache_addr = {};\n".format(self.addr[i]))

            if not self.web[i]:
                self.tdf.write("cache_din  = {};\n".format(self.data[i]))


            self.tdf.write("#(CLOCK_DELAY * 2);\n\n")

            if not pipeline_filled:
                pipeline_filled = True
                self.tdf.write("// Delay for the IDLE state\n")
                self.tdf.write("#(CLOCK_DELAY * 2);\n\n")

            old_i = i
            old_test_count = test_count

            # Check stall signal while waiting for the request to be completed
            while i + 1 < len(self.web) and self.web[i + 1] is None:
                i += 1
                test_count += 1

                self.tdf.write("// No operation (Test #{})\n".format(test_count))
                self.tdf.write("#(CLOCK_DELAY * 2);\n")
                self.tdf.write("check_stall({});\n\n".format(test_count))

            # Check read request after stalls
            if self.web[old_i]:
                prev_delayed = True
                self.tdf.write("// Test #{} continues here\n".format(old_test_count))
                self.tdf.write("#(CLOCK_DELAY * 2);\n")
                self.tdf.write("check_dout({0}, {1});\n\n".format(self.data[old_i], old_test_count))

            i += 1
            test_count += 1

        self.tdf.write("end_simulation();\n")
        self.tdf.write("$finish;\n")

        self.tdf.close()