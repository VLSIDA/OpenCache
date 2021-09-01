# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import os
import datetime
from shutil import copyfile
from subprocess import call, DEVNULL, STDOUT
from re import findall
from core import core
from test_bench import test_bench
from test_data import test_data
from sim_dram import sim_dram
import debug
from globals import OPTS, print_time


class verify:
    """
    Class to generate files for verification and verify the design by running
    EDA tools.
    """

    def __init__(self, cache_config, name):

        cache_config.set_local_config(self)
        self.name = name

        self.core = core()
        if OPTS.simulate:
            self.tb   = test_bench(cache_config, name)
            self.data = test_data(cache_config)
            self.dram = sim_dram(cache_config, self.data.sc.dram)

        # Print subprocess outputs on the terminal if verbose debug is enabled
        self.stdout = None if OPTS.verbose_level >= 2 else DEVNULL
        self.stderr = None if OPTS.verbose_level >= 2 else STDOUT


    def verify(self):
        """ Run the verifier. """

        debug.print_raw("Initializing verification...")

        self.prepare_files()
        if OPTS.simulate:
            self.simulate()
        if OPTS.synthesize:
            self.synthesize()

        debug.print_raw("Verification completed.")


    def simulate(self):
        """
        Save required files and simulate the design by running an EDA tool's
        simulator.
        """
        debug.info(1, "Initializing simulation...")
        debug.info(1, "Writing simulation files...")

        start_time = datetime.datetime.now()

        # Write the test bench file
        tb_path = OPTS.temp_path + "test_bench.v"
        debug.info(1, "Verilog (Test bench): Writing to {}".format(tb_path))
        self.tb.test_bench_write(tb_path)

        # Write the test data file
        data_path = OPTS.temp_path + "test_data.v"
        debug.info(1, "Verilog (Test data): Writing to {}".format(data_path))
        self.data.generate_data(OPTS.sim_size)
        self.data.test_data_write(data_path)

        # Write the DRAM file
        dram_path = OPTS.temp_path + "dram.v"
        debug.info(1, "Verilog (DRAM): Writing to {}".format(dram_path))
        self.dram.sim_dram_write(dram_path)

        # Run FuseSoc for simulation
        debug.info(1, "Running FuseSoC for simulation...")
        self.run_fusesoc(self.name, self.core.core_name, OPTS.temp_path, True)

        # Check the result of the simulation
        self.check_sim_result(OPTS.temp_path, "icarus.log")

        print_time("Simulation", datetime.datetime.now(), start_time)


    def synthesize(self):
        """
        Save required files and synthesize the design by running an EDA tool's
        synthesizer.
        """
        debug.info(1, "Initializing synthesis...")

        start_time = datetime.datetime.now()

        # Convert SRAM modules to blackbox
        debug.info(1, "Converting OpenRAM modules to blackbox...")
        self.convert_to_blacbox(OPTS.temp_path + OPTS.tag_array_name + ".v")
        self.convert_to_blacbox(OPTS.temp_path + OPTS.data_array_name + ".v")
        if OPTS.replacement_policy.has_sram_array():
            self.convert_to_blacbox(OPTS.temp_path + OPTS.use_array_name + ".v")

        # Run FuseSoc for synthesis
        debug.info(1, "Running FuseSoC for synthesis...")
        self.run_fusesoc(self.name, self.core.core_name, OPTS.temp_path, False)

        # Check the result of the synthesis
        self.check_synth_result(OPTS.temp_path, "yosys.log")

        print_time("Synthesis", datetime.datetime.now(), start_time)


    def prepare_files(self):
        """ Prepare common files among simulation and synthesis. """

        # Write the CORE file
        core_path = OPTS.temp_path + "verify.core"
        debug.info(1, "CORE: Writing to {}".format(core_path))
        self.core.core_write(core_path)

        # Copy the generated cache Verilog file
        cache_path = OPTS.temp_path + self.name + ".v"
        debug.info(1, "Copying the cache design file to the temp subfolder")
        copyfile(OPTS.output_path + self.name + ".v", cache_path)

        if OPTS.run_openram:
            # Copy the configuration files
            debug.info(1, "Copying the config files to the temp subfolder")
            self.copy_config_file(OPTS.data_array_name + "_config.py", OPTS.temp_path)
            self.copy_config_file(OPTS.tag_array_name + "_config.py", OPTS.temp_path)

            # Random replacement policy doesn't need a separate SRAM array
            if OPTS.replacement_policy.has_sram_array():
                self.copy_config_file(OPTS.use_array_name + "_config.py", OPTS.temp_path)

            # Run OpenRAM to generate Verilog files of SRAMs
            debug.info(1, "Running OpenRAM for the data array...")
            self.run_openram("{}_config.py".format(OPTS.temp_path + OPTS.data_array_name))

            debug.info(1, "Running OpenRAM for the tag array...")
            self.run_openram("{}_config.py".format(OPTS.temp_path + OPTS.tag_array_name))

            # Random replacement policy doesn't need a separate SRAM array
            if OPTS.replacement_policy.has_sram_array():
                debug.info(1, "Running OpenRAM for the use array")
                self.run_openram("{}_config.py".format(OPTS.temp_path + OPTS.use_array_name))
        else:
            debug.info(1, "Skipping to run OpenRAM")


    def run_openram(self, config_path):
        """ Run OpenRAM to generate Verilog modules. """

        openram_command = "python3 $OPENRAM_HOME/openram.py"

        if call("{0} {1}".format(openram_command, config_path),
                cwd=OPTS.temp_path,
                shell=True,
                stdout=self.stdout,
                stderr=self.stderr) != 0:
            debug.error("OpenRAM failed!", -1)

        if not OPTS.keep_openram_files:
            file_list = [item for item in os.listdir(OPTS.temp_path) if not os.path.isdir(item)]
            for file in file_list:
                if all([x not in file for x in [".v", ".py", ".core"]]):
                    os.remove(OPTS.temp_path + file)


    def run_fusesoc(self, library_name, core_name, path, is_sim):
        """ Run FuseSoC for simulation or synthesis. """

        fusesoc_library_command = "fusesoc library add {0} {1}".format(library_name,
                                                                       path)
        fusesoc_run_command = "fusesoc run --target={0} --no-export {1}".format("sim" if is_sim else "syn",
                                                                                core_name)

        debug.info(1, "Adding {} core as library...".format("simulation" if is_sim else "synthesis"))
        debug.info(1, "Running the {}...".format("simulation" if is_sim else "synthesis"))

        # Add the CORE file as a library
        if call(fusesoc_library_command,
                cwd=path,
                shell=True,
                stdout=self.stdout,
                stderr=self.stderr) != 0:
            debug.error("FuseSoC failed to add library!", -1)

        # Run the library for simulation or synthesis
        if call(fusesoc_run_command,
                cwd=path,
                shell=True,
                stdout=self.stdout,
                stderr=self.stderr) != 0:
            debug.error("FuseSoC failed to run!", -1)

        # Delete the temporary CONF file.
        # If this file is not deleted, it can cause syntheses to fail in the
        # future.
        os.remove(path + "fusesoc.conf")


    def copy_config_file(self, file_name, dest):
        """ Copy and modify the config file for simulation and synthesis. """

        new_file = open(dest + file_name, "w")

        with open(OPTS.output_path + file_name) as f:
            for line in f:
                if line.startswith("output_path"):
                    new_file.write("output_path = \"{}\"\n".format(dest))
                else:
                    new_file.write(line)

        # Verification needs only the Verilog files.
        # This option will decrease OpenRAM's runtime (hopefully).
        new_file.write("netlist_only = True\n")

        new_file.close()


    def convert_to_blacbox(self, file_path):
        """ Convert the given Verilog module file to blackbox. """

        keep = []
        # Save blackbox file as "filename_bb.v"
        bb_file_path = file_path[:-2] + "_bb.v"

        with open(file_path, "r") as f:
            delete = False

            for line in f:
                if line.lstrip().startswith("reg"):
                    delete = True

                if not delete:
                    keep.append(line)

        keep.append("endmodule\n")

        f = open(bb_file_path, "w")
        f.writelines(keep)
        f.close()


    def check_synth_result(self, path, file_name):
        """ Read the log file of the simulation. """

        error_prefix = "found and reported"

        # Check the error count lines
        with open("{0}build/{1}/syn-yosys/{2}".format(path,
                                                      self.core.core_name.replace(":", "_"),
                                                      file_name)) as f:
            for line in f:
                # TODO: How to check whether the synthesis was successful?
                # Check if error count is nonzero
                if line.find(error_prefix) != -1 and int(findall(r"\d+", line)[0]) != 0:
                    debug.error("Synthesis failed!", -1)
                # Check if there is an "ERROR"
                if line.find("ERROR") != -1:
                    debug.error("Synthesis failed!", -1)
        debug.info(1, "Synthesis successful.")


    def check_sim_result(self, path, file_name):
        """ Read the log file of the simulation. """

        # Result of the simulation is supposed to be at the end of the log file
        with open("{0}build/{1}/sim-icarus/{2}".format(path,
                                                       self.core.core_name.replace(":", "_"),
                                                       file_name)) as f:
            for line in f:
                pass
            if line.rstrip() == self.tb.success_message:
                debug.info(1, "Simulation successful.")
            else:
                debug.error("Simulation failed!", -1)