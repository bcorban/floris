# FLORIS Wake Modeling and Wind Farm Controls Software

> **This is a fork of [FLORIS](https://github.com/NatLabRockies/floris) v4.6.2 that adds an
> acoustic model.** It is not maintained by the FLORIS team. The changes are listed in
> [Acoustic extension](#acoustic-extension) below. The rest of this README is the original one.

FLORIS is a controls-focused wind farm simulation software incorporating
steady-state engineering wake models into a performance-focused Python
framework. It has been in active development at NLR since 2013 and the latest
release is [FLORIS v.4.6.2](https://github.com/NatLabRockies/floris/releases/latest).
Online documentation is available at https://natlabrockies.github.io/floris.

The software is in active development and engagement with the development team
is highly encouraged. If you are interested in using FLORIS to conduct studies
of a wind farm or extending FLORIS to include your own wake model, please join
the conversation in [GitHub Discussions](https://github.com/NatLabRockies/floris/discussions/)!

## Acoustic extension

This fork estimates the noise emitted by wind turbines and maps it around the farm:

- `FlorisModel.acoustic_results`: A-weighted sound pressure level (SPL) of each turbine,
  100 m from its hub, in dB(A), with shape `(n_findex, n_turbines)`. It uses the empirical
  model of Hagg et al. given in Wagner, Bareiss and Guidati, *Wind Turbine Noise* (Springer,
  1996), which depends on the blade tip speed, the thrust coefficient and the rotor geometry.
  Yaw misalignment and derating change the tip speed and the thrust coefficient, and so the
  noise.
- `FlorisModel.calculate_acoustic_plane(height, ...)`: total SPL of the farm on a horizontal
  plane (for example at ground level), with spherical spreading and a dipole directivity. It
  returns a `CutPlane` that `flow_visualization.visualize_cut_plane` can plot.
- An optional `acoustics` section in the turbine definition, with the rated rotor speed, the
  mean blade chord and the number of blades. It is filled in for `nrel_5MW` and
  `nrel_5MW_calibrated`.

It also changes the following parts of FLORIS:

- The `mixed` operation model accepts a yaw angle and a power setpoint on the same turbine
  (the original raises an error).
- The thrust coefficient is clipped to [1e-4, 0.9999] in the Gauss wake models and the
  derating models, to avoid divisions by zero for shut-down turbines.
- `visualize_cut_plane` takes `colorbar_label` and `line_contour` arguments.
- New turbine `nrel_5MW_calibrated`: `nrel_5MW` with a yaw loss exponent of 3.0.

To install, clone this repository, check out the `acoustics` branch, and run `pip install -e .`
from its root. Example: [examples/examples_acoustics/001_acoustic_noise_map.py](examples/examples_acoustics/001_acoustic_noise_map.py).

```python
from floris import FlorisModel
from floris.flow_visualization import visualize_cut_plane

fmodel = FlorisModel("examples/inputs/gch.yaml")
fmodel.set(layout_x=[0.0, 630.0], layout_y=[0.0, 0.0], wind_speeds=[10.0],
           wind_directions=[270.0], turbulence_intensities=[0.06])
fmodel.run()
print(fmodel.acoustic_results)  # dB(A) at 100 m from each hub
plane = fmodel.calculate_acoustic_plane(height=0.0)
visualize_cut_plane(plane, color_bar=True, colorbar_label="SPL [dB(A)]", line_contour=False)
```

## WETO software

FLORIS is primarily developed with the support from the U.S. Department of Energy and
is part of the [WETO Software Stack](https://natlabrockies.github.io/WETOStack).
For more information and other integrated modeling software, see:

- [Portfolio Overview](https://natlabrockies.github.io/WETOStack/portfolio_analysis/overview.html)
- [Entry Guide](https://natlabrockies.github.io/WETOStack/_static/entry_guide/index.html)
- [Wind Farm Controls Workshop](https://www.youtube.com/watch?v=f-w6whxIBrA&list=PL6ksUtsZI1dwRXeWFCmJT6cEN1xijsHJz)

## Installation

**If upgrading from a previous version, it is recommended to install FLORIS v4 into a new virtual environment**.
If you intend to use [pyOptSparse](https://mdolab-pyoptsparse.readthedocs-hosted.com/en/latest/) with FLORIS,
it is recommended to install that package first before installing FLORIS.

FLORIS can be installed by downloading the source code or via the PyPI
package manager with `pip`.

The simplest method is with `pip` by using this command:

```bash
pip install floris
```

Developers and anyone who intends to inspect the source code
can install FLORIS by downloading the git repository
from GitHub with ``git`` and use ``pip`` to locally install it.
It is highly recommended to use a Python virtual environment manager
such as [conda](https://docs.conda.io/en/latest/miniconda.html)
in order to maintain a clean and sandboxed environment. The following
commands in a terminal or shell will download and install FLORIS.

```bash
    # Download the source code from the `main` branch
    git clone -b main https://github.com/NatLabRockies/floris.git

    # If using conda, be sure to activate your environment prior to installing
    # conda activate <env name>

    # If using pyOptSpare, install it first
    conda install -c conda-forge pyoptsparse

    # Install FLORIS
    pip install -e floris
```

With both methods, the installation can be verified by opening a Python interpreter
and importing FLORIS:

```python
>>> import floris
>>> help(floris)

Help on package floris:

NAME
    floris

PACKAGE CONTENTS
    convert_floris_input_v3_to_v4
    convert_turbine_v3_to_v4
    core (package)
    cut_plane
    floris_model
    flow_visualization
    layout_visualization
    logging_manager
    optimization (package)
    parallel_floris_model
    turbine_library (package)
    type_dec
    uncertain_floris_model
    utilities
    version
    wind_data

VERSION
    4.6.2

FILE
    ~/floris/floris/__init__.py
```

It is important to regularly check for new updates and releases as new
features, improvements, and bug fixes will be issued on an ongoing basis.

## Quick Start

FLORIS is a Python package run on the command line typically by providing
an input file with an initial configuration. It can be installed with
```pip install floris``` (see [installation](https://natlabrockies.github.io/floris/installation.html)).
The typical entry point is
[FlorisModel](https://natlabrockies.github.io/floris/_autosummary/floris.floris_model.html)
which accepts the path to the input file as an argument. From there,
changes can be made to the initial configuration through the
[FlorisModel.set](https://natlabrockies.github.io/floris/_autosummary/floris.floris_model.html#floris.floris_model.FlorisModel.set)
routine, and the simulation is executed with
[FlorisModel.run](https://natlabrockies.github.io/floris/_autosummary/floris.floris_model.html#floris.floris_model.FlorisModel.run).

```python
from floris import FlorisModel
fmodel = FlorisModel("path/to/input.yaml")
fmodel.set(
    wind_directions=[i for i in range(10)],
    wind_speeds=[8.0]*10,
    turbulence_intensities=[0.06]*10
)
fmodel.run()
```

Finally, results can be analyzed via post-processing functions available within
[FlorisModel](https://natlabrockies.github.io/floris/_autosummary/floris.floris_model.html#floris.floris_model.FlorisModel)
such as
- [FlorisModel.get_turbine_layout](https://natlabrockies.github.io/floris/_autosummary/floris.floris_model.html#floris.floris_model.FlorisModel.get_turbine_layout)
- [FlorisModel.get_turbine_powers](https://natlabrockies.github.io/floris/_autosummary/floris.floris_model.html#floris.floris_model.FlorisModel.get_turbine_powers)
- [FlorisModel.get_farm_AEP](https://natlabrockies.github.io/floris/_autosummary/floris.floris_model.html#floris.floris_model.FlorisModel.get_farm_AEP)

and in two visualization packages: [layoutviz](https://natlabrockies.github.io/floris/_autosummary/floris.layout_visualization.html) and [flowviz](https://natlabrockies.github.io/floris/_autosummary/floris.flow_visualization.html).
A collection of examples describing the creation of simulations as well as
analysis and post processing are included in the
[repository](https://github.com/NatLabRockies/floris/tree/main/examples). Examples are also listed
in the [online documentation](https://natlabrockies.github.io/floris/examples/001_opening_floris_computing_power.html).

## Engaging on GitHub

FLORIS leverages the following GitHub features to coordinate support and development efforts:

- [Discussions](https://github.com/NatLabRockies/floris/discussions): Collaborate to develop ideas for new use cases, features, and software designs, and get support for usage questions
- [Issues](https://github.com/NatLabRockies/floris/issues): Report potential bugs and well-developed feature requests
- [Projects](https://github.com/orgs/NREL/projects/96): Include current and future work on a timeline and assign a person to "own" it

Generally, the first entry point for the community will be within one of the
categories in Discussions.
[Ideas](https://github.com/NatLabRockies/floris/discussions/categories/ideas) is a great spot to develop the
details for a feature request. [Q&A](https://github.com/NatLabRockies/floris/discussions/categories/q-a)
is where to get usage support.
[Show and tell](https://github.com/NatLabRockies/floris/discussions/categories/show-and-tell) is a free-form
space to show off the things you are doing with FLORIS.


# License

BSD 3-Clause License

Copyright (c) 2025, Alliance for Energy Innovation LLC, All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted
provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions
and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of
conditions and the following disclaimer in the documentation and/or other materials provided
with the distribution.

* Neither the name of the copyright holder nor the names of its contributors may be used to
endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER
OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
