# Replacement Policies
Replacement policies are defined in [policy.py](../generator/base/policy.py).

## None
Direct-mapped cache doesn't have a replacement policy.

## First In First Out
First In First Out (FIFO) replacement policy is implemented with a single pointer entry
in the use array.

Each set in the cache has its own use number. This number points to the next way
to be replaced when a data needs to be brought from DRAM.

When a way is replaced, the corresponding use number is incremented by 1. Since it
starts from 0 and flips when it reaches the way limit, data will be evicted in the order
they arrive. 

## Least Recently Used
Least Recently Used (LRU) replacement policy is implemented with a queue of use order
entries in the use array.

Each set in the cache has its own queue of use numbers. Each queue has a number for each
way in the set. These numbers show the relative use order of each way.

When a way is used (read or write), its use number is brought to the end of the queue
(maximum value). When a way needs to be evicted, the way with 0 use number is chosen.

## Random
Random replacement policy is implemented with a single counter, without a separate use
array.

The counter points to the way to be evicted. At every positive edge of the clock, the
counter is incremented by 1.

Since we can't know when the cache will need to evict a data and how long it will take
the DRAM to return a data, this counter essentially points to a random way.