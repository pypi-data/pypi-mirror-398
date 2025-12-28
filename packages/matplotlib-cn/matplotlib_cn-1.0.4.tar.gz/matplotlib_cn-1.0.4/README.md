# matplotlib_cn

## Description

`matplotlib_cn` is a Python package designed to simplify the use of Matplotlib for Chinese users. It provides localized documentation and examples to help users better understand and utilize Matplotlib for data visualization.

## Features

- Simplified setup for Matplotlib in Chinese environments.
- Localized examples and documentation.
- Compatible with Python 3.8.
- Supports Google Colab and Jupyter Notebook!

## Installation

You can install the package using `pip`:

```bash
pip install -U matplotlib_cn
```

## Usage
Here is a simple example of how to use `matplotlib_cn`:

```python
from matplotlib_cn import matplotlib_chinese

matplotlib_chinese.enable_matplotlib_chinese()

# or just
matplotlib_chinese.plot_chinese()


# example plot with Chinese characters
import numpy as np
import matplotlib.pyplot as plt

from matplotlib_cn import matplotlib_chinese
matplotlib_chinese.plot_chinese()

x = np.linspace(-10, 10, 100)
y = x

plt.plot(x, y)
plt.title("中文标题：y = x")
plt.xlabel("横轴（x）")
plt.ylabel("纵轴（y）")
plt.show()
```

