# Notebooks

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gl/wpettersson%2Fkep_solver/HEAD)

This folder contains notebooks for kep\_solver. You can download and run these
in your own installation of Jupyter Notebook if you wish, or you can utilise
[MyBinder](https://mybinder.org/v2/gl/wpettersson%2Fkep_solver/HEAD).

## Match run

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gl/wpettersson%2Fkep_solver/HEAD?labpath=notebooks%2FMatch%20Run.ipynb)

This notebook gives a complete guide to configuring a kidney exchange programme,
including setting different optimisation criteria and programme parameters such
as maximum chain length and examining the selected transplants in closer detail.

## Statistical Analysis

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gl/wpettersson%2Fkep_solver/HEAD?labpath=notebooks%2FStatistical%20Analysis.ipynb)

This notebook performs a number of in-depth statistical analyses on a set of
instance files. These analyses are not performed by `kep_solver`, but other
third-party modules. However, the results of these analyses is then used by
`kep_solver` to create a complete instance generator which can be used to
create randomly generated kidney exchange programme instances with properties
determined by the analysis. The configuration for this instance generator can
be exported as a JSON file for archival purposes or for publication or sharing
with other researchers.
