# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from design import design
from configuration import configuration


class cache_base(design, configuration):
    """
    This is the abstract parent class of cache modules.
    Some common methods among different cache modules
    are implemented here.
    """

    def __init__(self, cache_config, name):
        design.__init__(self)
        configuration.__init__(self)

        cache_config.set_local_config(self)
        self.name = name

    # TODO: Implement common base design methods here.