# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
"""
This script contains utility structures and functions
for RTL design scripts.
"""
from nmigen import Signal
from enum import IntEnum


class State(IntEnum):
    RESET      = 0
    FLUSH      = 1
    IDLE       = 2
    COMPARE    = 3
    WRITE      = 4
    WAIT_WRITE = 5
    READ       = 6
    WAIT_READ  = 7


def get_ff_signals(name, shape=None, reset=0, reset_less=True):
    """ Return two signals for an FF. """

    sigs = [Signal(shape=shape, reset=reset, reset_less=reset_less) for _ in range(2)]
    sigs[0].name = name
    sigs[1].name = name + "_next"
    return sigs