# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from random import randrange, choice
from globals import OPTS


class test_data:
    """
    Class to generate the test data file for simulation.
    """

    def __init__(self, sim_cache, cache_config):

        cache_config.set_local_config(self)
        self.sc = sim_cache


    def generate_data(self, test_size=16):
        """ Generate random test data and expected outputs. """

        # Operation
        self.op = []
        # Write enable
        self.web = []
        # Write mask
        self.wmask = []
        # Address
        self.addr = []
        # Data input/output
        self.data = []
        # Number of stall cycles during the request
        self.stall = []

        self.add_operation("reset")

        # Write and flush only when it's a data cache
        if not OPTS.read_only:
            # Write random data to random addresses initially
            for i in range(test_size):
                self.add_operation("write")

            self.add_operation("flush")

            addresses = []
            for i in range(len(self.op)):
                if self.op[i] == "write":
                    addresses.append(self.addr[i])

            # Read from random addresses which are written to in the first half
            while len(addresses) > 0:
                self.add_operation("read", addresses)
                addresses.remove(self.addr[-1])
        else:
            # Read random data from random addresses
            for i in range(test_size):
                self.add_operation("read")

        # Simulate the cache with sequence operations
        for i in range(len(self.op)):
            self.run_sim_cache(i)


    def add_operation(self, op, addr_list=None):
        """ Add a new operation with random address and data. """

        # Operation
        self.op.append(op)
        # Write enable
        self.web.append(int(op != "write"))

        # Address
        if addr_list is None:
            random_tag = randrange(2 ** self.tag_size)
            # Write to first two sets only so that we can test replacement
            random_set = randrange(2)
            random_offset = randrange(2 ** self.offset_size)
            self.addr.append(self.sc.merge_address(random_tag, random_set, random_offset))
        else:
            self.addr.append(choice(addr_list))

        if op == "write":
            # Write mask
            self.wmask.append("".join(
                [choice(["1", "0"]) for _ in range(self.num_masks)]
            ))
            # Data input
            self.data.append(randrange(1, 2 ** (self.word_size if self.offset_size else self.line_size)))
        else:
            # Write mask
            self.wmask.append("0" * self.num_masks)
            # Data output
            # This will be overwritten when running the sim_cache
            self.data.append(0)

        # Number of stall cycles during the operation
        # This will be overwritten when running the sim_cache
        self.stall.append(0)


    def run_sim_cache(self, op_idx):
        """ Run the sim_cache for the operation in the given index. """

        if self.op[op_idx] == "reset":
            self.stall[op_idx] = self.sc.reset()
        elif self.op[op_idx] == "flush":
            self.stall[op_idx] = self.sc.flush()
        else:
            self.stall[op_idx] = self.sc.stall_cycles(self.addr[op_idx])
            if self.op[op_idx] == "read":
                # Overwrite data for read to prevent bugs
                # NOTE: If the same address is written twice, this data
                # could be old.
                self.data[op_idx] = self.sc.read(self.addr[op_idx])
            elif self.op[op_idx] == "write":
                self.sc.write(self.addr[op_idx], self.wmask[op_idx], self.data[op_idx])


    def test_data_write(self, data_path):
        """ Write the test data file. """

        test_count = 0

        with open(data_path, "w") as file:
            file.write("// Initial delay to align with the cache and SRAMs.\n")
            file.write("// SRAMs return data at the negedge of the clock.\n")
            file.write("// Therefore, cache's output will be valid after the negedge.\n")
            file.write("#(CLOCK_DELAY + DELAY + 1);\n\n")

            # Check requests
            for i in range(len(self.op)):
                file.write("// {0} operation (Test #{1})\n".format(self.op[i].capitalize(),
                                                                   test_count))

                if self.op[i] == "reset" or self.op[i] == "flush":
                    file.write("assert_{}();\n".format(self.op[i]))
                else:
                    file.write("cache_csb   = 0;\n")
                    if not OPTS.read_only:
                        file.write("cache_web   = {};\n".format(self.web[i]))
                    if self.num_masks:
                        file.write("cache_wmask = {0}'b{1};\n".format(self.num_masks, self.wmask[i]))
                    file.write("cache_addr  = {};\n".format(self.addr[i]))
                    if not self.web[i]:
                        file.write("cache_din   = {};\n".format(self.data[i]))

                # Wait for 1 cycle so that cache will receive the request
                file.write("\n#(CLOCK_DELAY * 2);\n\n")

                if self.stall[i]:
                    file.write("check_stall({0}, {1});\n\n".format(self.stall[i], test_count))

                # Check read request after stalls
                if self.op[i] == "read":
                    file.write("check_dout({0}, {1});\n\n".format(self.data[i], test_count))

                test_count += 1

            file.write("end_simulation();\n")
            file.write("$finish;\n")