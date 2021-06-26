# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from random import randrange, choice


class test_data:
    """
    Class to generate the test data file for simulation.
    """

    def __init__(self, cache_config, name):

        cache_config.set_local_config(self)
        self.name = name


    def generate_data(self):
        """  Generate random test data and expected outputs. """

        data_size = 1 + self.address_size + self.word_size
        test_size = 2
        self.data = []

        # TODO: How to create random data in a smart way?
        # Write random data to random addresses initially
        for i in range(test_size):
            self.data.append("{0:0{1}b}".format(randrange(2 ** (data_size - 1)), data_size))

        # Read from random addresses which are written to in the first half
        for i in range(test_size):
            random_input = choice(self.data[0:test_size])
            self.data.append("1{0}{1}".format(random_input[1:self.address_size+1], random_input[-self.word_size:]))


    def write(self, data_path):
        """ Write the test data file. """

        data_size = 1 + self.address_size + self.word_size

        self.tdf = open(data_path + "test_data.v", "w")

        for i in range(len(self.data)):
            self.tdf.write("test_data[{0}] = {1}'b{2}_{3}_{4};\n".format(i, data_size, self.data[i][0], self.data[i][1:self.address_size + 1], self.data[i][-self.word_size:]))

        self.tdf.close()