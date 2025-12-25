# gdutils

[**Documentation**](https://gdutils-a2ef81.gitlabpages.inria.fr/)

**gdutils** is a lightweight Python utility library. It provides tools for organized file management, clean logging, and quality plotting.

## Installation

```bash
pip install gd-py-utils
```

## Quick Start

### 1. Data Management (`Container`)
A `Container` manages a directory and maintains a **logical registry** of your files.

```python
import numpy as np
import gdutils as gd

# Create a managed directory "experiments/run_01" (cleans it first)
with gd.Container("experiments/run_01", clean=True) as ct:
    
    # Create file paths naturally (automatically registered by stem name)
    data_file = ct / "data/results.npy"
    np.save(data_file, np.random.randn(100))

# Access files later using their logical key (filename without extension)
print(ct.results)  
# -> /abs/path/to/experiments/run_01/data/results.npy
```

### 2. Plotting Helpers (`SPlot`)

```python
import matplotlib.pyplot as plt

# Context manager handles plt.show() or saving automatically
with gd.SPlot(fname=ct / "my_plot.png", show=False):
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6], label="Data")
    
    # Utilities for cleaner figures
    gd.despine(ax, trim=True)  # Remove top/right spines
    gd.move_legend(ax, loc="upper right")
```

### 3. Logging
Get clean, readable logs with minimal setup.

```python
log = gd.get_logger()
log.info("Experiment started")
# [INFO] Experiment started
```

## Features

- **DataContainer**: Persistent key-value registry for filesystem paths.
- **TempContainer**: Automatic temporary directory cleanup.
- **Plotting**: `despine`, `move_legend`, `get_color_cycle`, and `SPlot` context manager.
- **Logging**: Zero-config formatted logger.
- **IO**: Path manipulation helpers (`fPath`).
