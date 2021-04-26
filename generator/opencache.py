# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
"""
Cache Generator
The output files append the given suffixes to the output name:
configuration (.py) files for OpenRAM compiler
a Verilog (.v) file for the cache logic
"""

import sys
import datetime
import globals as g

(OPTS, args) = g.parse_args()

# Check that we are left with a single configuration file as argument.
if len(args) != 1:
    print(g.USAGE)
    sys.exit(2)

# Parse config file and set up all the options
g.init_opencache(config_file=args[0])

# Only print banner here so it's not in unit tests
g.print_banner()

# Output info about this run
g.report_status()

from cache_config import cache_config

# Configure the cache organization
c = cache_config(OPTS)

from cache import cache
s = cache(cache_config=c,
          name=OPTS.output_name)

# Output the files for the resulting cache
s.save()