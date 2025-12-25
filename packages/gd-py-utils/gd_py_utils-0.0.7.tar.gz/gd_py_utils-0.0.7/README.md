# gdutils

[**Docs**](https://gdutils-a2ef81.gitlabpages.inria.fr/)


```bash
pip install gd-py-utils
```

```python
import gdutils as gd
```

A collection of Python utilities for data management, plotting, and more.
Supports 

- flexible file containers with attribute access,
- easy temporary directories,
- plotting helpers for Matplotlib,
- and streamlined logging.

## Features

- **Container**: Manage files & folders with Pythonic paths and attribute access.
- **TempContainer**: Safe, auto-cleanup temp directories.
- **fPath**: Utility for creating safe, structured output directories.
- **SimplePlot (SPlot)**: Context manager for pretty Matplotlib plots.
- **Logger**: Simple logger setup for scripts and CLIs.

## Basic Usage

```python
import gdutils as gd

# Data container example
with gd.Container("out") as ct:
    x = [1, 2, 3]
    with open(ct / "data.txt", "w") as f:
        f.write(str(x))
    print(ct.data)  # Access file as attribute

# Plotting example
import matplotlib.pyplot as plt
with gd.SPlot():
    plt.plot([1, 2], [3, 4])
```

See `examples/` for more.

## Documentation

Full docs at: https://gdutils-a2ef81.gitlabpages.inria.fr/

