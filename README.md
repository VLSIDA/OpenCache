# OpenCache
An open-source cache generator using [OpenRAM] SRAM arrays.

# What is OpenCache?
OpenCache is an open-source Python generator to create custom cache designs using OpenRAM's SRAM arrays.
It generates a synthesizable Verilog file for cache logic and configuration files for internal SRAM arrays.

# Documentation
[This](./docs/Overview.rst) serves as the documentation of OpenCache that explains parameters, architecture, etc.

# Basic Setup
## Dependencies
The OpenCache has the following dependencies:
+ Python 3.6 or higher
+ [Amaranth] 0.3 or higher
+ [Yosys] 0.10 or higher

If you want to verify the design via simulation and/or synthesis, you will need:
+ [OpenRAM]
+ [FuseSoC] 1.12 or higher
+ [Icarus] 10.3 or higher

For regression testing, you will need some Python packages, which can be installed with the following command:
```
pip3 install -r requirements.txt
```

## Environment
You must set an environment variable: 
+ **OPENCACHE\_HOME** should point to the generator source directory. 

For example, add this to your .bashrc file:

```bash
export OPENCACHE_HOME="$HOME/opencache/generator"
```

# Usage
## Basic Usage
Clone the repository.
```
git clone https://github.com/VLSIDA/OpenCache.git
cd OpenCache/generator
```
Create a Python configuration file. All configuration parameters can be found in [here](./docs/Parameter.rst).
A simple configuration file is:
```python
# Data array size
total_size = 1024

# Data word bit size
word_size = 8

# Number of words per line
words_per_line = 4

# Address port size
address_size = 11

# Number of ways
num_ways = 1

# Replacement policy
replacement_policy = None

# Write policy
write_policy = "write-back"

# Output file name
output_name = "cache"
```
Run the generator.
```
python3 opencache.py config_file
```

## OpenRAM Options
The `openram_options` option of OpenCache allows you to override configuration files for OpenRAM to generate SRAMs that you desire. An example is:
```python
# Add this to OpenCache config file
openram_options = {
    "tech_name": "scn4m_subm",
    "nominal_corner_only": True,
    "analytical_delay": False,
}
```

## Verification
In order to run verification, you need to add the following lines to your configuration file.
```python
# For simulation
simulate = True

# For synthesis
synthesize = True

# To keep the results
keep_temp = True
```

# Unit Tests
Regression testing performs a number of tests for OpenCache. From the generator directory, use the following command to run all regression tests:
```
python3 regress.py
```
To run a specific test:
```
python3 {unit test}.py
```

# License
OpenCache is licensed under the [BSD 3-clause License](LICENSE).

* * *

[OpenRAM]:  https://github.com/VLSIDA/OpenRAM
[FuseSoC]:  https://github.com/olofk/fusesoc
[Icarus]:   https://github.com/steveicarus/iverilog
[yosys]:    https://github.com/YosysHQ/yosys
[Amaranth]: https://github.com/amaranth-lang/amaranth