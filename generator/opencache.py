#!/usr/bin/env python3
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
g.init_opencache(config_file=args[0],
                 is_unit_test=False)

# Only print banner here so it's not in unit tests
g.print_banner()

# Keep track of running stats
start_time = datetime.datetime.now()
g.print_time("Start", start_time)

# Output info about this run
g.report_status()

from cache_config import cache_config

# Configure the cache organization
conf = cache_config(total_size=OPTS.total_size,
                    word_size=OPTS.word_size,
                    words_per_line=OPTS.words_per_line,
                    address_size=OPTS.address_size,
                    write_size=OPTS.write_size,
                    num_ways=OPTS.num_ways)

from cache import cache
c = cache(cache_config=conf,
          name=OPTS.output_name)

# Output the files for the resulting cache
c.save()

# Run verification
if OPTS.simulate or OPTS.synthesize:
    from verify import verify
    v = verify(cache_config=conf,
               name=OPTS.output_name)
    v.verify()

# Delete temp files etc.
g.end_opencache()
g.print_time("End", datetime.datetime.now(), start_time)