# Cache States
![State Diagram](./images/state_diagram.png)

## RESET
This is the initial state and a multi-cycle reset. It sets all rows of internal SRAMs
to zero. Cache enters this state when `rst` signal is high. Until it exits the state,
`stall` signal stays high. After the reset is over, cache switches to the **IDLE**
state.

## FLUSH
This state is independent from other states. If `flush` signal is high, cache enters
this state. `stall` signal becomes high and cache starts writing all dirty data lines
back to DRAM. When all dirty data lines are written back to DRAM, cache switches to
the **IDLE** state.

## IDLE
In this state, cache reads `addr` input and requests tag and data lines from its
internal SRAMs. If `csb` input is high, cache waits in this state. Otherwise, cache
switches to the **COMPARE** state.

## WAIT_HAZARD
In this state, cache avoids data hazard by stalling itself for 1 cycle. Cache requests
tag and data lines from its internal SRAMS, and switches to the **COMPARE** state.

## COMPARE
Tag and data lines are returned by internal SRAMs. Cache checks whether the request is
a hit or miss.

* If it is a hit, cache immediately performs the request; returns the data if read,
writes the input if write.

    * If `csb` is low, it also reads the next address from the pipeline and requests
    corresponding tag and data lines from internal SRAMs. If the next address is in
    the same set with the current address, data hazard might occur. In this case, cache
    switches to the **WAIT_HAZARD** state.

    * If `csb` is high, cache switches to the **IDLE** state and stall signals stays
    low.

* If it is a miss, cache checks whether the data line is dirty or not. In either case,
`stall` becomes high since cache will wait for DRAM’s response.

    * If the data line is dirty, cache sends the dirty line to DRAM. Cache switches to
    the **WAIT_WRITE** state if DRAM’s `main_stall` signal is low. Otherwise, it
    switches to the **WRITE** state.

    * If the data line is not dirty, cache requests the new data line from DRAM. Cache
    switches to the **WAIT_READ** state if `main_stall` signal is low. Otherwise, it
    switches to the **READ** state.

## WRITE
Cache waits in this state until `main_stall` signal is low. When it is low, cache sends
the dirty line to DRAM and switches to the **WAIT_WRITE** state.

## WAIT_WRITE
Cache waits in this state until `main_stall` signal becomes low. When it is low, cache
requests the new data line from DRAM. `stall` signal stays high. Cache switches to the
**WAIT_READ** state.

## READ
Cache waits in this state until `stall` signal is low. When it is low, cache requests
the new data line from DRAM and switches to the **WAIT_READ** state.

## WAIT_READ
Cache waits in this state until `main_stall` signal becomes low. When it is low, cache
sends the new tag and data lines to internal SRAMs.

* If `csb` is low, cache reads the next address from the pipeline and requests
corresponding tag and data lines from internal SRAMs. It avoids data hazard similar to
the **COMPARE** state.

* If `csb` is high, cache switches to the **IDLE** state; otherwise, it switches to the
**COMPARE** state.