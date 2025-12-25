# py-xl-sindy
The main repository for the python library of the Xl Sindy framework.

Xl-Sindy stand for Lagrangian based Sparse Identification of Non linear DYnamics. This framework enables the automatic discovery of dynamics of Lagrangian compatible system (mainly robotics and mechanics related).

The documentation of every function of the library can be found on the [py-xl-sindy GitHub pages](https://eymeric65.github.io/py-xl-sindy/index.html).

## Usage

py-xl-sindy is distributed on PyPi under the same name :
```sh
python -m pip install py-xl-sindy
```

However this library needs to be imported using a slightly different name :
```python
import xlsindy
```

For extensive usage, it is strongly recommended to read the doc and the exemple file provided in this repository.

Batch generation and complete analysis framework can be found in [util](/util/)

## Citing this library

The following bibtex can be used to cite the library :
```bibtex
@misc{py-xl-sindy,
  author       = {Eymeric Chauchat},
  title        = {py-xl-sindy: A Python library implementing Lagrangian Sparse Identification of Non linear DYnamics},
  year         = {2024},
  url          = {https://github.com/Eymeric65/py-xl-sindy},
  note         = {Version 1.0.0, released on 2024-11-19},
}
```

Multiple research work are on-going and can be tracked in [research_work](/research_work/)

The main article using `py-xl-sindy` has been used with the version `2.1.0`, data reproducibility can only be guaranteed with this version.

## Theorical background and DevBlog

The different ressources needed for the creation of this library can be found on the different Report posted on the subject :
- [May 2024](https://eymeric65.github.io/p/22a56c0680934dcdb94881992c682390/)
- [December 2024](https://eymeric65.github.io/p/5cb398f1511e45b095fa3e65c118dd62/)


## Build your own python library

A standard tutorial on "How to make a python library" can be found on [my personnal GitHub pages](https://eymeric65.github.io/p/738f25b6283a408aa2f517964cda0fc5/)
