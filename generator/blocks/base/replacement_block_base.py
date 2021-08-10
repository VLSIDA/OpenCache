# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from block_base import block_base


class replacement_block_base(block_base):
    """
    This is the base class of replacement always block modules.
    Methods of this class can be overridden for specific implementation
    of different cache designs.
    This class does not have any design implementation since direct-mapped
    design does not have this block. Also we need to extend this design for
    all replacement policies.
    """

    def __init__(self):

        super().__init__()