===============
Associativities
===============
Associativities policies are defined in `policy.py <../generator/base/policy.py>`_.

-------------
Direct-mapped
-------------
If ``num_ways`` is 1, the generated cache will be a direct-mapped cache. Direct-mapped
caches have only 1 way for data placement. If a cache miss occurs, the data in the set
which corresponds to the address is replaced.

---------------------
N-way Set Associative
---------------------
If ``num_ways`` is between 1 and ``total_size`` / ``line_size``, the generated cache will be
an N-way set associative cache. Set associative caches have multiple ways for data
placement. If a cache miss occurs, a way in the set corresponding to the address is
replaced. The way to evict is chosen according to the replacement policy of the cache.

-----------------
Fully Associative
-----------------
If ``num_ways`` is equal to :math: ``total_size`` / ``line_size``, the generated cache will
be a fully associative cache. Fully associative caches have only 1 set and the maximum number
of ways for data placement. If a cache miss occurs, the data in the way which is chosen
according to the replacement policy of the cache is replaced.

Fully Associative option is not yet implemented.