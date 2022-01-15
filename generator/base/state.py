# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from enum import IntEnum


class state(IntEnum):
    """ Enum class for internal states of a cache. """

    RESET = 0
    FLUSH = 1
    IDLE = 2
    COMPARE = 3
    WRITE = 4
    WAIT_WRITE = 5
    READ = 6
    WAIT_READ = 7
    FLUSH_HAZARD = 8
    WAIT_HAZARD = 9