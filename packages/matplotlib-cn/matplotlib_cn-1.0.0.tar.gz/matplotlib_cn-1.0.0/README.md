# matplotlib_cn

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Description

`matplotlib_cn` is a Python package designed to simplify the use of Matplotlib for Chinese users. It provides localized documentation and examples to help users better understand and utilize Matplotlib for data visualization.

## Features

- Simplified setup for Matplotlib in Chinese environments.
- Localized examples and documentation.
- Compatible with Python 3.9.

## Installation

You can install the package using `pip`:

```bash
pip install matplotlib_cn
```

## Usage
Here is a simple example of how to use `matplotlib_cn`:

```python
from matplotlib_cn import matplotlib_chinese

matplotlib_chinese.enable_matplotlib_chinese()


# example plot with Chinese characters
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(-10, 10, 100)
y = x

plt.plot(x, y)
plt.title("中文标题：y = x")
plt.xlabel("横轴（x）")
plt.ylabel("纵轴（y）")
plt.show()
```