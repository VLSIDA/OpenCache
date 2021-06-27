# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#

class core:
    """
    Class to generate the CORE file for FuseSoC.
    """

    def __init__(self, cache_config, name):

        cache_config.set_local_config(self)
        self.name = name

        # This is used in FuseSoC for the current run
        self.core_name = "opencache:cache:{}:0.1.0".format(name)


    def write(self, core_path):
        """ Write the CORE file for simulation. """

        self.cf = open(core_path, "w")

        self.cf.write("CAPI=2:\n")
        self.cf.write("name: {}\n".format(self.core_name))
        self.cf.write("description: A cache design by OpenCache\n\n")

        self.cf.write("filesets:\n")
        self.cf.write("  rtl_files:\n")
        self.cf.write("    files:\n")
        self.cf.write("      - dram.v\n")
        self.cf.write("      - {}_tag_array.v\n".format(self.name))
        self.cf.write("      - {}_data_array.v\n".format(self.name))
        self.cf.write("      - {}.v\n".format(self.name))
        self.cf.write("    file_type: verilogSource\n\n")

        self.cf.write("  tb_files:\n")
        self.cf.write("    files:\n")
        self.cf.write("      - test_bench.v\n")
        self.cf.write("      - test_data.v:\n")
        self.cf.write("          is_include_file: true\n")
        self.cf.write("    file_type: verilogSource\n\n")

        self.cf.write("targets:\n")
        self.cf.write("  default:\n")
        self.cf.write("    filesets:\n")
        self.cf.write("      - rtl_files\n\n")

        self.cf.write("  sim:\n")
        self.cf.write("    description: Simulate the cache design\n")
        self.cf.write("    default_tool: icarus\n")
        self.cf.write("    filesets:\n")
        self.cf.write("      - rtl_files\n")
        self.cf.write("      - tb_files\n")
        self.cf.write("    tools:\n")
        self.cf.write("      icarus:\n")
        self.cf.write("        timescale: 1ns/1ps\n")
        self.cf.write("    toplevel: test_bench\n")

        self.cf.close()