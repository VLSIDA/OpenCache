# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from .sim_cache import sim_cache
from .verification import verification
import debug
from globals import OPTS
from globals import find_exe


# Check FuseSoC executable
if find_exe("fusesoc") is None:
    debug.error("FuseSoC isn't installed. Disable verification to ignore.", -1)

# Check simulation tool executable
if OPTS.simulate:
    if find_exe("iverilog") is None:
        debug.error("Icarus isn't installed. Disable simulation to ignore.", -1)

# Check synthesis tool executable
if OPTS.synthesize:
    if find_exe("yosys") is None:
        debug.error("Yosys isn't installed. Disable synthesis to ignore.", -1)


def run(cache_config, name):
    """ Run the verification. """

    ver = verification(cache_config, name)
    ver.verify()