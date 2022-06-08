# plotannot
[![PyPI Version](https://img.shields.io/pypi/v/plotannot.svg?style=plastic)](https://pypi.org/project/plotannot/)

# Introduction
_plotannot_ is a a python package to automatically highlight and adjust overlapping ticklabels in matplotlib/seaborn plots. It is written with great inspiration and appreciation for the _statannot_ package ([webermarcolivier/statannot](https://github.com/webermarcolivier/statannot) - now maintained at [trevismd/statannotations](https://github.com/trevismd/statannotations)), as well as the _adjustText_ package ([Phlya/adjustText](https://github.com/Phlya/adjustText)).

I originally created this package for myself, as I wanted to create ComplexHeatmap (R package) style annotations for Python plots - but maybe it is of use to you too? 

<img src="examples/before_after.png"/>

## Features

- Add annotation lines for certain row/column labels
- Shift labels to not overlap
- Add additional highlights such as color, fontsize, etc. to certain row/column labels


## Getting started

Install from PyPI:

```pip install plotannot```

Or directly from github:

``` pip install git+git://github.com/msbentsen/plotannot ```

Requirements for package:
- Python >= 3.6
- matplotlib
- numpy


## Simple example

```
import pandas as pd
import seaborn as sns
import plotannot

#Plot heatmap
table = pd.DataFrame(np.random.random((100,50)))
ax = sns.heatmap(table, xticklabels=True, yticklabels=False)

#Rotate all labels
plotannot.format_ticklabels(ax, axis="xaxis", rotation=45)

#Annotate labels
to_label = range(20,35)
plotannot.annotate_ticks(ax, axis="xaxis", labels=to_label) 

#Color individual labels
plotannot.format_ticklabels(ax, axis="xaxis", labels=[25], color="red")
```
<img src="examples/simple_example.png"/>

Additional examples are found in the [examples notebook](examples/examples.ipynb). 

## Documentation and help

Documentation of the main functions are found at: [plotannot.readthedocs.io](https://plotannot.readthedocs.io/en/latest/). Examples of how to use these are in the examples notebook here: [examples/examples.ipynb](examples/examples.ipynb). 

Issues and PRs are very welcome - please use the [repository issues](https://github.com/msbentsen/plotannot/issues) to raise an issue/contribute.


