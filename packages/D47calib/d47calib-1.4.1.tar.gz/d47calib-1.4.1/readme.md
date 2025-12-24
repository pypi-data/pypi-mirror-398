[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8357232.svg)](https://doi.org/10.5281/zenodo.8357232)
[![PyPI Version](https://img.shields.io/pypi/v/D47calib.svg)](https://pypi.python.org/pypi/D47calib)

# D47calib

Generate, combine, display and apply Δ<sub>47</sub> calibrations.

## Link with OGLS regression

The calibrations use *Omnivariant Generalized Least Squares*, a generalized from of least-squares regression combining the features of GLS and York regression. It is described in an upcoming paper by [*Daëron & Vermeesch* (2024)](https://doi.org/10.1016/j.chemgeo.2023.121881), where the full reprocessing and regression of the various `D47calib` calibrations is described. See the `build_calibs` directory in this repo for the corresponding reprocessing code.

## Contact

All questions and suggestions are welcome and should be directed at [Mathieu Daëron](mailto:daeron@lsce.ipsl.fr?subject=[D47calib]), or feel free to open an issue [here](https://github.com/mdaeron/D47calib/issues).

## Documentation

For the full API and examples, see [https://mdaeron.github.io/D47calib](https://mdaeron.github.io/D47calib).