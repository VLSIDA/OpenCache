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

    def __init__(self, cache_config):

        cache_config.set_local_config(self)
        self.sc = sim_cache(cache_config)


    def generate_data(self, test_size=16):
        """  Generate random test data and expected outputs. """

        # Operation
        self.op = ["reset"]
        # Write enable
        self.web = [1]
        # Write mask
        self.wmask = ["0" * self.num_masks]
        # Address
        self.addr = [0]
        # Data input/output
        self.data = [0]
        # Number of stall cycles after the request
        self.stall = [0]

        # TODO: How to create random data in a smart way?
        # Write random data to random addresses initially
        for i in range(test_size):
            random_tag = randrange(2 ** self.tag_size)
            # Write to first two sets only so that we can test replacement
            random_set = randrange(2)
            random_offset = randrange(2 ** self.offset_size)
            random_address = self.sc.merge_address(random_tag, random_set, random_offset)

            self.op.append("write")
            self.web.append(0)
            self.wmask.append("".join([choice(["1", "0"]) for _ in range(self.num_masks)]))
            self.addr.append(random_address)
            # Data written should not be 0 since cache output is 0 by default
            self.data.append(randrange(1, 2 ** self.word_size))
            self.stall.append(0)

        # Flush the cache after writing is done
        self.op.append("flush")
        self.web.append(1)
        self.wmask.append("0" * self.num_masks)
        self.addr.append(0)
        self.data.append(0)
        self.stall.append(0)

        indices = list(range(test_size))

        # Read from random addresses which are written to in the first half
        while len(indices) > 0:
            index = choice(indices)

            # Don't take reset and flush operations
            if self.op[index] == "write":
                self.op.append("read")
                self.web.append(1)
                self.wmask.append("0" * self.num_masks)
                self.addr.append(self.addr[index])
                # If the same address is written twice, this data may be old.
                # Therefore, data values for read operations are going to be
                # overwritten in the next for loop.
                self.data.append(self.data[index])
                self.stall.append(0)

            indices.remove(index)

        # Simulate the cache with sequence operations
        for i in range(len(self.op)):
            # Get the number of stall cycles
            if self.op[i] == "reset":
                self.stall[i] = self.sc.reset()
            elif self.op[i] == "flush":
                self.stall[i] = self.sc.flush()
            else:
                self.stall[i] = self.sc.stall_cycles(self.addr[i])
                if self.web[i]:
                    # Overwrite data for read to prevent bugs
                    # NOTE: If the same address is written twice, this data
                    # could be old.
                    self.data[i] = self.sc.read(self.addr[i])
                else:
                    self.sc.write(self.addr[i], self.wmask[i], self.data[i])


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