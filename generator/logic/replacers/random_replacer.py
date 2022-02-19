# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from logic_base import logic_base
from state import state


class random_replacer(logic_base):
    """
    This class extends base logic module for random replacement policy.
    """

    def __init__(self):

        super().__init__()


    def add(self, c, m):
        """ Add all sections of the always block code. """

        m.d.comb += c.random.eq(c.random + 1)

        super().add(c, m)


    def add_flush(self, c, m):
        """ Add statements for the FLUSH state. """

        # In the FLUSH state, way register is used to write all data lines back
        # to DRAM.
        with m.Case(state.FLUSH):
            # If current set is clean or DRAM is available, increment the way register
            with m.If((~c.tag_array.output().dirty(c.way) | ~c.dram.stall())):
                m.d.comb += c.way.eq(c.way + 1)


    def add_compare(self, c, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, way is selected according to the replacement
        # policy of the cache.
        with m.Case(state.COMPARE):
            m.d.comb += c.way.eq(c.random)
            # If there is an empty way, it must be filled before evicting the
            # random way.
            for i in c.hit_detector.find_empty():
                m.d.comb += c.way.eq(i)
            # Check if current request is a hit
            for i in c.hit_detector.find_hit():
                m.d.comb += c.way.eq(i)


    def add_flush_sig(self, c, m):
        """ Add flush signal control. """

        # If flush is high, way is reset.
        # way register becomes 0 since it is going to be used to write all data
        # lines back to DRAM.
        with m.If(c.flush):
            m.d.comb += c.way.eq(0)


    def add_reset_sig(self, c, m):
        """ Add reset signal control. """

        # If rst is high, way and random are reset.
        # way register becomes 0 since it is going to be used to reset all ways
        # tag lines.
        with m.If(c.rst):
            m.d.comb += c.way.eq(0)
            m.d.comb += c.random.eq(0)