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
    RESET       = 0
    FLUSH       = 1
    IDLE        = 2
    WAIT_HAZARD = 3
    COMPARE     = 4
    WRITE       = 5
    WAIT_WRITE  = 6
    READ        = 7
    WAIT_READ   = 8


def get_flop_signals(name, shape=None, reset=0, reset_less=True):
    """ Return two signals for a flip-flop. """

    sigs = [Signal(shape=shape, reset=reset, reset_less=reset_less) for _ in range(2)]
    sigs[0].name = name
    sigs[1].name = name + "_next"
    return sigs


def trim_verilog(code):
    """ Trim unnecessary lines in a Verilog code. """

    lines = code.splitlines(True)

    for i in range(len(lines)):
        # Delete \initial register
        if "\\initial" in lines[i]:
            lines[i] = ""
        # Delete auto-generated flops
        if "$next" in lines[i]:
            lines[i] = ""

    code = "".join(lines)
    return code