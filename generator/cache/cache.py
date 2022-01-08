# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import debug
import datetime
from policy import associativity, replacement_policy as RP
from globals import OPTS, print_time


class cache:
    """
    This is not a design module, but contains a cache design instance.
    """

    def __init__(self, cache_config, name):

        cache_config.set_local_config(self)
        self.name = name

        # Import the design module of the cache
        if OPTS.associativity == associativity.DIRECT:
            from direct_cache import direct_cache as cache
        elif OPTS.associativity == associativity.N_WAY:
            from n_way_cache import n_way_cache as cache
        elif OPTS.associativity == associativity.FULLY:
            # TODO: from full_cache import full_cache as cache
            debug.error("Fully associative cache is not supported at the moment.", -1)
        else:
            debug.error("Invalid associativity.", -1)

        self.c = cache(cache_config, name)


    def config_write(self, paths):
        """ Save the config files. """

        self.c.config_write(paths)


    def verilog_write(self, path):
        """ Save the Verilog file. """

        self.c.verilog_write(path)


    def save(self):
        """ Save all the output files. """

        debug.print_raw("Saving output files...")

        # Write the config files
        start_time = datetime.datetime.now()
        cpaths = {
            "data": OPTS.output_path + OPTS.data_array_name + "_config.py",
            "tag":  OPTS.output_path + OPTS.tag_array_name + "_config.py",
            "use":  OPTS.output_path + OPTS.use_array_name + "_config.py"
        }
        if not OPTS.replacement_policy.has_sram_array(): del cpaths["use"]
        for k, cpath in cpaths.items():
            debug.print_raw("Config: Writing to {}".format(cpath))
        self.config_write(cpaths)
        print_time("Config", datetime.datetime.now(), start_time)

        # Write the Verilog file
        start_time = datetime.datetime.now()
        vpath = OPTS.output_path + self.c.name + ".v"
        debug.print_raw("Verilog: Writing to {}".format(vpath))
        self.verilog_write(vpath)
        print_time("Verilog", datetime.datetime.now(), start_time)