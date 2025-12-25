# Iker's Python Common Module

[![codecov](https://codecov.io/gh/ruyangshou/iker-python-common/graph/badge.svg?token=0FGT4M40CD)](
https://codecov.io/gh/ruyangshou/iker-python-common)

## Build and Deploy

### Using Conda

We recommend using Conda. You need to install Anaconda packages from
the [official site](https://www.anaconda.com/products/distribution)

Create a Conda environment and install the modules and their dependencies in it

```shell
conda create -n iker python=3.14
conda activate iker

pip install .

conda deactivate
```

To remove the existing Conda environment (and create a brand new one)

```shell
conda env remove -n iker
```
