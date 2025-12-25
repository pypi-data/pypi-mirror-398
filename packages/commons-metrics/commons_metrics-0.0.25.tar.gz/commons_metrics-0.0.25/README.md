# Simple Stats

A simple Python library for basic statistical calculations.

## Features

- Calculate mean
- Calculate median
- Calculate mode
- Calculate standard deviation

## Dev
pip install setuptools wheel
python3 setup.py sdist bdist_wheel
twine upload dist/*
input token
git ignore buill,commons_metrics.egg-info, dist

## Build Dependencies
pip install twine

pip install commons_metrics==0.0.4


## Installation

You can install the library using pip:

```bash
pip install .

## Usage
from common_stats import mean, median, mode, standard_deviation

data = [1, 2, 3, 4, 5]

print("Mean:", mean(data))
print("Median:", median(data))
print("Mode:", mode(data))
print("Standard Deviation:", standard_deviation(data))