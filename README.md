# OpenCache
An open-source cache generator using [OpenRAM](https://github.com/VLSIDA/OpenRAM) SRAM arrays.

# What is OpenCache?
OpenCache is an open-source Python generator to create a cache design using OpenRAM's SRAM arrays.

# Usage
Clone the repository.
```
git clone ...
cd OpenCache
```
Create a Python configuration file. All configuration parameters can be found in [here](CONFIG.md). A simple configuration file is:
```python
# data array size
total_size = 256
# data word bit size
word_size = 4
# number of words per line
words_per_line = 4
# address port size
address_size = 11
# number of ways
num_ways = 1
# replacement policy
replacement_policy = None
# output file name
output_name = "cache"
```

# License

OpenCache is licensed under the [BSD 3-clause License](LICENSE).