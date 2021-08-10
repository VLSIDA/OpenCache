# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import debug
from block_factory import factory


class logic:
    """
    This is the logic base class. Design block classes are instantiated here.
    This is inherited by the cache_base class.
    """

    def __init__(self):
        pass


    def add_logic_blocks(self, m):
        """ Instantiate and add logic blocks. """
        debug.info(1, "Adding logic blocks...")

        blocks = []
        blocks.append(factory.create("memory_block"))
        blocks.append(factory.create("state_block"))
        blocks.append(factory.create("request_block"))
        blocks.append(factory.create("output_block"))
        blocks.append(factory.create("replacement_block"))

        for block in blocks:
            block.add(self, m)