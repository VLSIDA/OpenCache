# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from globals import OPTS, NAME
from verilog import verilog


class cache_base(verilog):
    """
    This is the abstract parent class of cache modules.
    Some common methods among different cache modules
    are implemented here.
    """

    def __init__(self, cache_config, name):
        verilog.__init__(self)

        cache_config.set_local_config(self)
        self.name = name


    def config_write(self, config_paths):
        """ Write the configuration files for OpenRAM SRAM arrays. """

        self.dcf = open(config_paths[0], "w")

        self.dcf.write("word_size    = {}\n".format(self.row_size))
        self.dcf.write("num_words    = {}\n".format(self.num_rows))
        self.dcf.write("num_rw_ports = 0\n")
        self.dcf.write("num_r_ports  = 1\n")
        self.dcf.write("num_w_ports  = 1\n")
        # OpenRAM outputs of the data array are saved to a separate folder
        self.dcf.write("output_path  = \"{}/data_array\"\n".format(OPTS.output_path))
        self.dcf.write("output_name  = \"{}\"\n".format(OPTS.data_array_name))

        self.dcf.close()

        self.tcf = open(config_paths[1], "w")

        self.tcf.write("word_size    = {}\n".format((2 + self.tag_size) * self.num_ways))
        self.tcf.write("num_words    = {}\n".format(self.num_rows))
        self.tcf.write("num_rw_ports = 0\n")
        self.tcf.write("num_r_ports  = 1\n")
        self.tcf.write("num_w_ports  = 1\n")
        # OpenRAM outputs of the tag array are saved to a separate folder
        self.tcf.write("output_path  = \"{}/tag_array\"\n".format(OPTS.output_path))
        self.tcf.write("output_name  = \"{}\"\n".format(OPTS.tag_array_name))

        self.tcf.close()