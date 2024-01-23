# elgold toolset

This is the accompanying repository for the elgold dataset.
The elgold dataset can be obtained here: https://doi.org/10.34808/9wvq-th71

The elgold toolset provides a command-line interface 
for managing, converting, and plotting the elgold dataset.

## Installation

The elgold toolset was tested with Python 3.11, but it
should also work with future Python versions.

1. Download the [elgold dataset](https://doi.org/10.34808/9wvq-th71) and unzip it
in main project directory. The repository should now
contain the `data` directory.
2. Install pip requirements: `pip install -r requirements.txt`.

## Usage

The elgold toolset consists of four main modules:
* `convert.py` - Convert the elgold dataset to different formats.
* `elgold.py` - Manage the elgold dataset.
* `plot.py` - Plot various dataset statistics.

Detailed information about each module can be 
obtained using the `--help` flag. E.g. `python convert.py --help`.

## Licence

The elgold toolset is released under the MIT license.

The elgold dataset is licensed under CC-BY 4.0.