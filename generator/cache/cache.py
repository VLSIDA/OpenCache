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
            debug.error("Fully associative cache is not supported at the moment.", -1)
            # from full_cache import full_cache as cache
        else:
            debug.error("Invalid number of ways.", -1)

        self.c = cache(name, cache_config)


    def config_write(self, path):
        self.c.config_write(path)


    def verilog_write(self, path):
        self.c.verilog_write(path)


    def save(self):
        """ Save all the output files (Config and Verilog). """

        # Write the config file
        cpath = OPTS.output_path + self.c.name
        debug.print_raw("Config: Writing to {}".format(cpath))
        self.config_write(cpath)

        # Write the Verilog model
        vpath = OPTS.output_path + self.c.name
        debug.print_raw("Verilog: Writing to {}".format(vpath))
        self.verilog_write(vpath)