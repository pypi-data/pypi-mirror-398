# Continuous Ordinal Patterns (ContOP / COP) Library

Ordinal patterns are a way of analyzing time series in which values in sub-windows are studied in terms of their relative amplitude, or, in other words, of the permutation required to sort them. Such permutations are then represented as symbols, and their frequency is used to characterize the dynamics generating the time series. This, thus, represents a conceptually simple way of synthesizing a whole time series into a discrete distribution and, not surprisingly, has been applied to a plethora of real-world problems.

Continuous Ordinal Patterns (COP in short) turn this idea around: instead of using fixed patterns, we created a continuous version of these, that can be optimized to tackle a specific problem. In other words, instead of counting permutation patterns in a time series, we find the specific pattern that is better representing the same time series.

The underlying concept was firstly described in the paper:

Zanin, M. (2023). Continuous ordinal patterns: Creating a bridge between ordinal analysis and deep learning. Chaos: An Interdisciplinary Journal of Nonlinear Science, 33(3).
https://doi.org/10.1063/5.0136492


In addition, specific extensions and use cases have been discussed in multiple papers, as e.g.:

Zanin, M. (2024). Augmenting granger causality through continuous ordinal patterns. Communications in Nonlinear Science and Numerical Simulation, 128, 107606. 
https://doi.org/10.1016/j.cnsns.2023.107606

Zanin, M. (2024). Manipulating Time Series Irreversibility Through Continuous Ordinal Patterns. Symmetry, 16(12), 1696.
https://doi.org/10.3390/sym16121696




## Setup

This package can be installed from PyPI using pip:

```
bash
pip install contop
```

This will automatically install all the necessary dependencies as specified in the `pyproject.toml` file.



## Getting started

Information about all functions and tests available can be found in the wiki: [Go to the wiki](https://gitlab.com/MZanin/contop/-/wikis/home). Please make sure to visit the [examples' page](https://gitlab.com/MZanin/contop/-/wikis/home/Examples), where you will find several examples on how to use the package.

Please note that we welcome readers to send us comments, suggestions and corrections, using the "Issues" feature.



## Change log

See the [Version History](https://gitlab.com/MZanin/contop/-/wikis/home/Version-History) section of the Wiki for details.



## Acknowledgements

This project has received funding from the European Research Council (ERC) under the European Union's Horizon 2020 research and innovation programme (grant agreement No 851255).

This work was partially supported by the María de Maeztu project CEX2021-001164-M funded by the MICIU/AEI/10.13039/501100011033 and FEDER, EU.

This work was partially supported by grant CNS2023-144775 funded by MICIU/AEI/10.13039/501100011033 by "European Union NextGenerationEU/PRTR".


