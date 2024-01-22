# elgold toolset

This is the accompanying repository for the elgold dataset.
The elgold dataset can be obtained here: ...

The elgold toolset provides a command line interface 
for managing, exporting and calculation of various
statistics for elgold dataset.

## Installation

The elgold toolset was tested with Python 3.11, but it
should also work with future Python versions.

1. Download the elgold dataset and unzip it
in main project directory. The repository should now
contain `data` directory.
2. Install pip requirements: `pip install -r requirements.txt`.

## Usage

The elgold toolset consists of four main modules:
* `convert.py` - export Elgold dataset
to different formats.
* `elgold.py` - manage Elgold dataset.
* `plot.py` - plot various dataset statistics.

The detailed information about each module can be 
obtained using `--help` flag. E.g. `python convert.py --help`.

## Licence

The elgold toolset is released under the MIT licence.

The elgold dataset is licensed under CC-BY 4.0.