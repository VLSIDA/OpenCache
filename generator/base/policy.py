# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
"""
Enum classes to represent cache policies are defined here.
"""
from enum import IntEnum


class associativity(IntEnum):
    """ Enum class to represent associativity. """

    DIRECT = 0
    N_WAY = 1
    FULLY = 2


    def __str__(self):
        if self == associativity.DIRECT:
            return "Direct-mapped"
        if self == associativity.N_WAY:
            return "N-way Set Associative"
        if self == associativity.FULLY:
            return "Fully Associative"


class replacement_policy(IntEnum):
    """ Enum class to represent replacement policies. """

    NONE = 0
    FIFO = 1
    LRU = 2
    RANDOM = 3


    def __str__(self):
        return self.name.lower()


    def upper(self):
        return self.name


    def long_name(self):
        """ Get the long name of the replacement policy. """

        if self == replacement_policy.NONE:
            return "None"
        if self == replacement_policy.FIFO:
            return "First In First Out"
        if self == replacement_policy.LRU:
            return "Least Recently Used"
        if self == replacement_policy.RANDOM:
            return "Random"


    def has_sram_array(self):
        """ Return True if the replacement policy needs a separate SRAM array. """

        return self not in [
            replacement_policy.NONE,
            replacement_policy.RANDOM
        ]


    @staticmethod
    def get_value(name):
        """ Get the replacement policy enum value. """

        if name is None:
            return replacement_policy.NONE
        for k, v in replacement_policy.__members__.items():
            if name.upper() == k:
                return v


class write_policy(IntEnum):
    """ Enum class to represent write policies. """

    WRITE_BACK = 0
    WRITE_THROUGH = 1


    def __str__(self):
        return self.name.lower()


    def upper(self):
        return self.name


    def long_name(self):
        """ Get the long name of the write policy. """

        if self == write_policy.WRITE_BACK:
            return "Write-back"
        if self == write_policy.WRITE_THROUGH:
            return "Write-through"


    @staticmethod
    def get_value(name):
        """ Get the write policy enum value. """

        if name is None or name == "write-back":
            return write_policy.WRITE_BACK
        if name == "write-through":
            return write_policy.WRITE_THROUGH