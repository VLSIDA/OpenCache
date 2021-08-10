# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from globals import OPTS


class configuration:
    """
    Create OpenRAM configuration files.
    This is inherited by the cache_base class.
    """

    def __init__(self):
        pass


    def calculate_configs(self, paths):
        """ Calculate config options for internal SRAM arrays of the cache. """

        # Store config file options in a list
        config_opts = []

        # Data array of the cache
        data_opts = {}
        data_opts["path"] = paths["data"]
        data_opts["opts"] = {}
        data_opts["opts"]["word_size"]    = self.row_size
        data_opts["opts"]["num_words"]    = self.num_rows
        data_opts["opts"]["num_rw_ports"] = 0
        data_opts["opts"]["num_r_ports"]  = 1
        data_opts["opts"]["num_w_ports"]  = 1
        data_opts["opts"]["output_path"]  = '"{}data_array"'.format(OPTS.output_path)
        data_opts["opts"]["output_name"]  = '"{}"'.format(OPTS.data_array_name)
        config_opts.append(data_opts)

        # Tag array of the cache
        tag_opts = {}
        tag_opts["path"] = paths["tag"]
        tag_opts["opts"] = {}
        tag_opts["opts"]["word_size"]    = self.tag_word_size * self.num_ways
        tag_opts["opts"]["num_words"]    = self.num_rows
        tag_opts["opts"]["num_rw_ports"] = 0
        tag_opts["opts"]["num_r_ports"]  = 1
        tag_opts["opts"]["num_w_ports"]  = 1
        tag_opts["opts"]["output_path"]  = '"{}tag_array"'.format(OPTS.output_path)
        tag_opts["opts"]["output_name"]  = '"{}"'.format(OPTS.tag_array_name)
        config_opts.append(tag_opts)

        return config_opts


    def config_write(self, paths):
        """ Write the OpenRAM configuration files. """

        config_opts = self.calculate_configs(paths)

        for opts in config_opts:
            c_file = open(opts["path"], "w")
            for k, v in opts["opts"].items():
                c_file.write("{0} = {1}\n".format(k, v))
            c_file.close()