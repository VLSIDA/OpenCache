# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from .sim_cache import sim_cache
from .verification import verification


def run(cache_config, name):
    """ Run the verification. """

    ver = verification(cache_config, name)
    ver.verify()