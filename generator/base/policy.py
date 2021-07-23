# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from enum import IntEnum

"""
Enum classes to represent cache policies
are defined here.
"""

class Associativity(IntEnum):
    """ Enum class to represent associativity. """

    DIRECT = 0
    N_WAY  = 1
    FULLY  = 2


    def __str__(self):
        if self == Associativity.DIRECT:
            return "Direct-mapped"
        if self == Associativity.N_WAY:
            return "N-way Set Associative"
        if self == Associativity.FULLY:
            return "Fully Associative"


class ReplacementPolicy(IntEnum):
    """ Enum class to represent replacement policies. """

    NONE   = 0
    FIFO   = 1
    LRU    = 2
    RANDOM = 3


    def __str__(self):
        return self.name.lower()


    def upper(self):
        return self.name


    def long_name(self):
        """ Get the long name of the replacement policy. """

        if self == ReplacementPolicy.NONE:
            return "None"
        if self == ReplacementPolicy.FIFO:
            return "First In First Out"
        if self == ReplacementPolicy.LRU:
            return "Least Recently Used"
        if self == ReplacementPolicy.RANDOM:
            return "Random"


    def has_sram_array(self):
        """
        Return True if the replacement policy
        needs a separate SRAM array.
        """

        return self not in [
            ReplacementPolicy.NONE,
            ReplacementPolicy.RANDOM
        ]


    @staticmethod
    def get_default():
        """ Get the default replacement policy. """

        return ReplacementPolicy.NONE


class WritePolicy(IntEnum):
    """ Enum class to represent write policies. """

    WR_BACK = 0
    WR_THRU = 1


    def __str__(self):
        return self.name.lower()


    def upper(self):
        return self.name


    def long_name(self):
        """ Get the long name of the write policy. """

        if self == WritePolicy.WR_BACK:
            return "Write-back"
        if self == WritePolicy.WR_THRU:
            return "Write-through"


    @staticmethod
    def get_default():
        """ Get the default write policy. """

        return WritePolicy.WR_BACK