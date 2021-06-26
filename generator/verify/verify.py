# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import os
from shutil import copyfile
from subprocess import call, DEVNULL
from core import core
from test_bench import test_bench
from test_data import test_data
from dram import dram
import debug
from globals import OPTS


class verify:
    """
    Class to generate files for verification and verify the design
    by running EDA tools.
    """

    def __init__(self, cache_config, name):

        cache_config.set_local_config(self)
        self.name = name

        if OPTS.simulate:
            self.core = core(cache_config, name)
            self.tb   = test_bench(cache_config, name)
            self.data = test_data(cache_config, name)
            self.dram = dram(cache_config, name)


    def verify(self):
        """ Run the verifier. """

        debug.print_raw("Initializing verification...")

        if OPTS.simulate:
            self.simulate()


    def simulate(self):
        """
        Save required files and simulate the design
        by running an EDA tool's simulator.
        """

        debug.print_raw("  Writing simulation files...")

        path = OPTS.output_path + "simulation/"

        # Write the CORE file
        debug.print_raw("    CORE: Writing to {}".format(path))
        self.core.write(path)

        # Write the test bench file
        debug.print_raw("    Verilog (Test bench): Writing to {}".format(path))
        self.tb.write(path)

        # Write the test data file
        debug.print_raw("    Verilog (Test data): Writing to {}".format(path))
        self.data.generate_data()
        self.data.write(path)

        # Write the DRAM file
        debug.print_raw("    Verilog (DRAM): Writing to {}".format(path))
        self.dram.write(path)

        # Copy the generated cache Verilog file
        debug.print_raw("  Copying the cache design file to the simulation subfolder")
        copyfile(OPTS.output_path + self.name + ".v", path + self.name + ".v")

        # Copy the configuration files
        debug.print_raw("  Copying the config files to the simulation subfolder")
        self.copy_config_file(self.name + "_data_array_config.py", path)
        self.copy_config_file(self.name + "_tag_array_config.py", path)

        if self.replacement_policy == "fifo":
            self.copy_config_file(self.name + "_fifo_array_config.py", path)
        elif self.replacement_policy == "lru":
            self.copy_config_file(self.name + "_lru_array_config.py", path)

        # Run OpenRAM to generate Verilog files of SRAMs
        debug.print_raw("  Running OpenRAM for the data array...")
        if call("python3 $OPENRAM_HOME/openram.py {}_data_array_config.py".format(path + self.name), cwd=path, shell=True, stdout=DEVNULL) < 0:
            debug.error("    OpenRAM failed!")

        debug.print_raw("  Running OpenRAM for the tag array...")
        if call("python3 $OPENRAM_HOME/openram.py {}_tag_array_config.py".format(path + self.name), cwd=path, shell=True, stdout=DEVNULL) < 0:
            debug.error("    OpenRAM failed!")

        if self.replacement_policy == "fifo":
            debug.print_raw("  Running OpenRAM for the FIFO array")
            if call("python3 $OPENRAM_HOME/openram.py {}_fifo_array_config.py".format(path + self.name), cwd=path, shell=True, stdout=DEVNULL) < 0:
                debug.error("    OpenRAM failed!")
        elif self.replacement_policy == "lru":
            debug.print_raw("  Running OpenRAM for the LRU array")
            if call("python3 $OPENRAM_HOME/openram.py {}_lru_array_config.py".format(path + self.name), cwd=path, shell=True, stdout=DEVNULL) < 0:
                debug.error("    OpenRAM failed!")

        # Run FuseSoc for simulation
        debug.print_raw("  Running FuseSoC for simulation...")

        debug.print_raw("    Adding simulation as library...")
        if call("fusesoc library add {0} {1}".format(self.name, path), cwd=path, shell=True, stdout=DEVNULL) < 0:
            debug.error("    FuseSoC failed to add simulation core.")

        debug.print_raw("    Running the simulation...")
        if call("fusesoc run --target=sim --no-export opencache:cache:{}:0.1.0".format(self.name), cwd=path, shell=True, stdout=DEVNULL) < 0:
            debug.error("    FuseSoC failed to run the simulation.")

        # Delete the temporary CONF file
        # If this file is not deleted, it can cause simulations
        # to fail in the future.
        os.remove(path + "fusesoc.conf")

        # Check the result of the simulation
        if self.check_sim_result(path, "icarus.log"):
            debug.print_raw("  Simulation successful.")
        else:
            debug.error("  Simulation failed.")

        debug.print_raw("  Verification completed.")


    def copy_config_file(self, file_name, dest):
        """ Copy and modify the config file for simulation. """

        new_file = open(dest + file_name, "w")

        with open(OPTS.output_path + file_name) as f:
            for line in f:
                if line.startswith("output_path"):
                    new_file.write("output_path = \"{}\"\n".format(dest))
                else:
                    new_file.write(line)

        # Simulation needs only the Verilog files
        # This option will decrease OpenRAM's runtime
        new_file.write("netlist_only = True\n")

        new_file.close()


    def check_sim_result(self, path, file_name):
        """ Read the log file of the simulation. """

        # Result of the simulation is supposed to be at the end
        with open("{0}build/opencache_cache_{1}_0.1.0/sim-icarus/{2}".format(path, self.name, file_name)) as f:
            for line in f:
                pass
            return line.rstrip() == "Simulation successful."