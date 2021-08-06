# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from enum import IntEnum


class State(IntEnum):
    """ Enum class for internal states of a cache. """

    RESET       = 0
    FLUSH       = 1
    IDLE        = 2
    WAIT_HAZARD = 3
    COMPARE     = 4
    WRITE       = 5
    WAIT_WRITE  = 6
    READ        = 7
    WAIT_READ   = 8