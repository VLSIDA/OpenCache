# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from globals import OPTS, VERSION


class core:
    """
    Class to generate the CORE file for FuseSoC.
    """

    def __init__(self):

        # This is used in FuseSoC for the current run
        self.core_name = "opencache:cache:{0}:{1}".format(OPTS.output_name,
                                                          VERSION)


    def write(self, core_path):
        """ Write the CORE file for simulation. """

        with open(core_path, "w") as file:
            file.write("CAPI=2:\n")
            file.write("name: {}\n".format(self.core_name))
            file.write("description: A cache design by OpenCache\n\n")

            file.write("filesets:\n")
            file.write("  sim_files:\n")
            file.write("    files:\n")
            file.write("      - dram.v\n")
            if OPTS.replacement_policy.has_sram_array():
                file.write("      - {}.v\n".format(OPTS.use_array_name))
            file.write("      - {}.v\n".format(OPTS.tag_array_name))
            file.write("      - {}.v\n".format(OPTS.data_array_name))
            file.write("      - {}.v\n".format(OPTS.output_name))
            file.write("      - test_bench.v\n")
            file.write("      - test_data.v:\n")
            file.write("          is_include_file: true\n")
            file.write("    file_type: verilogSource\n\n")

            file.write("  synth_files:\n")
            file.write("    files:\n")
            if OPTS.replacement_policy.has_sram_array():
                file.write("      - {}_bb.v\n".format(OPTS.use_array_name))
            file.write("      - {}_bb.v\n".format(OPTS.tag_array_name))
            file.write("      - {}_bb.v\n".format(OPTS.data_array_name))
            file.write("      - {}.v\n".format(OPTS.output_name))
            file.write("    file_type: verilogSource\n\n")

            # FIXME: What is the default fileset?
            file.write("targets:\n")
            file.write("  default:\n")
            file.write("    filesets:\n")
            file.write("      - sim_files\n\n")

            file.write("  sim:\n")
            file.write("    description: Simulate the cache design\n")
            file.write("    default_tool: icarus\n")
            file.write("    filesets:\n")
            file.write("      - sim_files\n")
            file.write("    tools:\n")
            file.write("      icarus:\n")
            file.write("        timescale: 1ns/1ps\n")
            file.write("    toplevel: test_bench\n\n")

            file.write("  synth:\n")
            file.write("    description: Synthesize the cache design\n")
            file.write("    default_tool: yosys\n")
            file.write("    filesets:\n")
            file.write("      - synth_files\n")
            file.write("    tools:\n")
            file.write("      yosys:\n")
            file.write("        arch: xilinx\n")
            file.write("    toplevel: {}\n".format(OPTS.output_name))