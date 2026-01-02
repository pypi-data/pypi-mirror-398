# microfinity

[![PyPI](https://img.shields.io/pypi/v/microfinity.svg)](https://pypi.org/project/microfinity/)
![python version](https://img.shields.io/static/v1?label=python&message=3.9%2B&color=blue&style=flat&logo=python)
[![CadQuery](https://img.shields.io/static/v1?label=dependencies&message=CadQuery%202.0%2B&color=blue&style=flat)](https://github.com/CadQuery/cadquery)
[![cq-kit](https://img.shields.io/badge/CQ--kit-blue)](https://github.com/michaelgale/cq-kit)
![license](https://img.shields.io/badge/license-MIT-blue.svg)
[![code style: black](https://img.shields.io/badge/code%20style-black-black.svg)](http://github.com/psf/black)

A Python library to make [Gridfinity](https://gridfinity.xyz) compatible objects with [CadQuery](https://github.com/CadQuery/cadquery).

The Gridfinity system was created by [Zach Freedman](https://www.youtube.com/c/ZackFreedman) as a versatile system of modular organization and storage modules. This library provides Python classes to create parameterized Gridfinity components including boxes, baseplates, drawer spacers, and rugged storage boxes.

> **Note:** This is a fork of [cq-gridfinity](https://github.com/michaelgale/cq-gridfinity) by Michael Gale.

## Installation

```bash
pip install microfinity
```

Or install from source:

```bash
git clone https://github.com/nullstack65/microfinity.git
cd microfinity
pip install -e .
```

### Dependencies

- [CadQuery](https://github.com/CadQuery/cadquery)
- [cq-kit](https://github.com/michaelgale/cq-kit)

## Quick Start

```python
import microfinity
print(microfinity.__version__)
```

```python
from microfinity import *

# Make a simple box
box = GridfinityBox(3, 2, 5, holes=True, scoops=True, labels=True)
box.save_stl_file()
# Output: gf_box_3x2x5_holes_scoops_labels.stl
```

## CLI Commands

### `microfinity-box`

```bash
microfinity-box 2 3 5 -m -f stl
```

### `microfinity-base`

```bash
microfinity-base 7 4 -s -f stl
```

### `microfinity-rugged`

```bash
microfinity-rugged 5 4 6 --box --lid -f stl
```

## Classes

- `GridfinityBox` - Boxes with dividers, scoops, labels, magnet holes
- `GridfinityBaseplate` - Baseplates with optional mounting tabs
- `GridfinityDrawerSpacer` - Spacers for fitting baseplates in drawers
- `GridfinityRuggedBox` - Rugged storage boxes with lids and handles

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## References

- [Gridfinity wiki](https://gridfinity.xyz)
- [Original cq-gridfinity](https://github.com/michaelgale/cq-gridfinity) by Michael Gale

## License

MIT License. Originally created by [Michael Gale](https://github.com/michaelgale).
