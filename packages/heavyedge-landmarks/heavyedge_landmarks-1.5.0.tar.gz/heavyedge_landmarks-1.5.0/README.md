# HeavyEdge-Landmarks

[![Supported Python Versions](https://img.shields.io/pypi/pyversions/heavyedge-landmarks.svg)](https://pypi.python.org/pypi/heavyedge-landmarks/)
[![PyPI Version](https://img.shields.io/pypi/v/heavyedge-landmarks.svg)](https://pypi.python.org/pypi/heavyedge-landmarks/)
[![License](https://img.shields.io/github/license/heavyedge/heavyedge-landmarks)](https://github.com/heavyedge/heavyedge-landmarks/blob/master/LICENSE)
[![CI](https://github.com/heavyedge/heavyedge-landmarks/actions/workflows/ci.yml/badge.svg)](https://github.com/heavyedge/heavyedge-landmarks/actions/workflows/ci.yml)
[![CD](https://github.com/heavyedge/heavyedge-landmarks/actions/workflows/cd.yml/badge.svg)](https://github.com/heavyedge/heavyedge-landmarks/actions/workflows/cd.yml)
[![Docs](https://readthedocs.org/projects/heavyedge-landmarks/badge/?version=latest)](https://heavyedge-landmarks.readthedocs.io/en/latest/?badge=latest)

![title](https://heavyedge-landmarks.readthedocs.io/en/latest/_images/plot-header.png)

Python package to locate landmarks from edge profiles.

Supports:

- Pseudo-landmark sampling.
- Mathematical landmark detection.
- Converting configuration matrix to pre-shape.
- Plateau fitting.

## Usage

HeavyEdge-Landmarks provides functions to locate landmarks from multiple profiles.

A simple use case to locate 10 pseudo-landmarks:

```python
from heavyedge import get_sample_path, ProfileData
from heavyedge_landmarks import pseudo_landmarks
with ProfileData(get_sample_path("Prep-Type2.h5")) as data:
    x = data.x()
    Ys, Ls, _ = data[:]
lm = pseudo_landmarks(x, Ys, Ls, 10)
```

Refer to the package documentation for more information.

## Installation

```
$ pip install heavyedge-landmarks
```

## Documentation

The manual can be found online:

> https://heavyedge-landmarks.readthedocs.io

If you want to build the document yourself, get the source code and install with `[doc]` dependency.
Then, go to `doc` directory and build the document:

```
$ pip install .[doc]
$ cd doc
$ make html
```

Document will be generated in `build/html` directory. Open `index.html` to see the central page.

## Developing

### Installation

For development features, you must install the package by `pip install -e .[dev]`.

### Testing

Run `pytest` command to perform unit test.
