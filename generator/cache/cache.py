# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import os
import debug
from globals import OPTS


class cache:
    """
    This is not a design module, but contains a cache design instance.
    """
    def __init__(self, cache_config, name):

        cache_config.set_local_config(self)

        self.name = name        

        if self.num_ways == 1:
            from direct_cache import direct_cache as cache
        elif self.set_size:
            if self.replacement_policy == "fifo":
                from n_way_fifo_cache import n_way_fifo_cache as cache
            elif self.replacement_policy == "lru":
                from n_way_lru_cache import n_way_lru_cache as cache
            elif self.replacement_policy == "random":
                from n_way_random_cache import n_way_random_cache as cache
            else:
                debug.error("Invalid replacement policy.", -1)
        elif not self.set_size:
            # TODO: from full_cache import full_cache as cache
            debug.error("Fully associative cache is not supported at the moment.", -1)
        else:
            debug.error("Invalid number of ways.", -1)

        self.c = cache(cache_config, name)


    def config_write(self, path):
        """ Save the config files. """

        self.c.config_write(path)


    def verilog_write(self, path):
        """ Save the Verilog file. """

        self.c.verilog_write(path)


    def save(self):
        """ Save all the output files (Config and Verilog). """

        debug.print_raw("Saving output files...")

        # Write the config file
        cpath = OPTS.output_path + self.c.name
        debug.print_raw("  Config:  Writing to {}".format(cpath))
        self.config_write(cpath)

        # Write the Verilog model
        vpath = OPTS.output_path + self.c.name
        debug.print_raw("  Verilog: Writing to {}".format(vpath))
        self.verilog_write(vpath)