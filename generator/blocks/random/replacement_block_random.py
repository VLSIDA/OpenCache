# See LICENSE for licensing information.
#
# Copyright (c) 2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
from replacement_block_base import replacement_block_base
from state import State


class replacement_block_random(replacement_block_base):
    """
    This class extends base replacement module for random replacement policy.
    """

    def __init__(self):

        super().__init__()


    def add(self, dsgn, m):
        """ Add all sections of the always block code. """

        m.d.comb += dsgn.random.eq(dsgn.random + 1)

        super().add(dsgn, m)


    def add_reset_sig(self, dsgn, m):
        """ Add reset signal control. """

        # If rst is high, way and random are reset.
        # way register becomes 0 since it is going to be used to reset all ways
        # tag lines.
        with m.If(dsgn.rst):
            m.d.comb += dsgn.way.eq(0)
            m.d.comb += dsgn.random.eq(0)


    def add_flush_sig(self, dsgn, m):
        """ Add flush signal control. """

        # If flush is high, way is reset.
        # way register becomes 0 since it is going to be used to write all data
        # lines back to DRAM.
        with m.Elif(dsgn.flush):
            m.d.comb += dsgn.way.eq(0)


    def add_states(self, dsgn, m):
        """ Add statements for each cache state. """

        with m.Else():
            with m.Switch(dsgn.state):
                super().add_states(dsgn, m)


    def add_flush(self, dsgn, m):
        """ Add statements for the FLUSH state. """

        # In the FLUSH state, way register is used to write all data lines back
        # to DRAM.
        with m.Case(State.FLUSH):
            # If current set is clean or DRAM is available, increment the way register
            with m.If((~dsgn.tag_array.output().dirty(dsgn.way) | ~dsgn.dram.stall())):
                m.d.comb += dsgn.way.eq(dsgn.way + 1)


    def add_compare(self, dsgn, m):
        """ Add statements for the COMPARE state. """

        # In the COMPARE state, way is selected according to the replacement
        # policy of the cache.
        with m.Case(State.COMPARE):
            m.d.comb += dsgn.way.eq(dsgn.random)
            # If there is an empty way, it must be filled before evicting the
            # random way.
            for i in range(dsgn.num_ways):
                with m.If(~dsgn.tag_array.output().valid(i)):
                    m.d.comb += dsgn.way.eq(i)