# Configuration Parameters
This is the list of all configuration parameters of OpenCache.

## `total_size`
This is the total size of the data array of the cache. It must match `word_size` parameter.

## `word_size`
This is the bit size of a word.

## `words_per_line`
This is the number of words per line.

## `address_size`
This is the bit size of address port of the cache.

## `num_ways`
This is the number of the ways in the cache.

## `replacement_policy`
This is the replacement (eviction) policy of the cache. Note that direct-mapped caches (1-way) do not have a replacement policy.
Currently supported replacement policies are:
* First In First Out (FIFO)
* Least Recently Used (LRU)
* Random

## `write_policy`
This is the write policy of the cache. Currently supported write policies are:
* Write-back

## `is_data_cache`
This is whether the cache is a *"data cache"* or an *"instruction cache"*. INSTRUCTION CACHE IS NOT YET SUPPORTED!

## `return_type`
This is which data the cache returns. Currently supported return types are:
* Word

## `data_hazard`
This is whether data hazard may occur in the internal SRAM arrays. Currently OpenRAM SRAM arrays are not read-after-write.
However, this parameter can be set `False` if the user can guarantee that SRAM arrays are going to be *"data hazard proof"*
or OpenRAM SRAM arrays are read-after-write in the future.

## `output_path`
This is where output files are going to be saved to.

## `output_name`
This is what the names of output files are going to be.