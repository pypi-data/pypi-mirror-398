# kep\_solver

This Python package is devoted to various algorithms, procedures and mechanisms
that are useful when studying kidney exchange programmes in general.  It is
written and maintained by [William Pettersson](mailto:william.pettersson@glasgow.ac.uk).

- [Full documentation](https://kep-solver.readthedocs.io/en/latest/)
- [Pypi link](https://pypi.org/project/kep-solver/)

## Requirements

kep\_solver runs on Python 3.10 or higher. As long as you install via pip, all
other requirements will be handled by pip

## Quick start with notebooks

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gl/wpettersson%2Fkep_solver/HEAD)

This package provides two sample notebooks in the `notebooks` folder. You can
access either of these using [MyBinder](https://mybinder.org/v2/gl/wpettersson%2Fkep_solver/HEAD).

Please note that MyBinder, as a free service, does have limits on its use. For
more intensive use, or where the privacy of the data you use is important, you
can self-install using the following instructions.

## Quick start self-install

Create a virtual environment for kep\_solver

    mkvirtualenv kep_solver

Install kep\_solver

    pip install kep_solver

Download a sample JSON file from
`https://kep-web.optimalmatching.com/static/jsons/sample-1.json`

Run the following Python commands

```python
# Import the required functions
from kep_solver.fileio import read_json
from kep_solver.programme import Programme
from kep_solver.model import TransplantCount

# Read some input
instance = read_json("sample-1.json")

# Create a transplant pool with one objective.
# We will allow cycles to have at most 3 donor/recipient pairs and allow chains
# to have have at most 2 donors (i.e., one non-directed donor and one
# donor/recipient pair).
programme = Programme([TransplantCount()],
                       description="My first KEP",
                       maxCycleLength=3,
                       maxChainLength=2)

# Solve our instance
solution, model = programme.solve_single(instance)

# Print the solution
for selected in solution.selected:
    print(f"Selected {selected}")
```

## Current features

* Reading instance files (json and XML formats)
* Creation of compatibility graphs
* Solving for the following objectives (single, or hierarchical)

    * Maximise the number of transplants
    * Maximise the number of backarcs
    * Maximise the number of effective 2-way exchanges
    * Minimise the number of three-cycles
    * Maximise the score using the UK scoring mechanisms

While the above objectives are exactly those in use by NHSBT when running the
UKLKSS (the UK national KEP), I do intend to add further objectives

## Expected users

I expect this software to be useful to researchers. Depending on what questions
you want answered, you can either test policy changes to determine how they
affect the running of a KEP, or you can implement new models or objectives to
see how they perform

## Documentation

Full documentation for kep\_solver can be found at
[https://kep-solver.readthedocs.io/en/latest/](https://kep-solver.readthedocs.io/en/latest/).

## Interface

This is just a Python module for now, a web-interface that demonstrates a basic
use case is viewable at
[https://kep-web.optimalmatching.com](https://kep-web.optimalmatching.com), and
the source code for said website is online at
[https://gitlab.com/wpettersson/kep\_web](https://gitlab.com/wpettersson/kep_web)

## Future plans

* More objective functions
* Supporting transnational pools
* Implementation of faster models and modelling techniques


## Contributing

I welcome input from others, whether you have ideas for improvements or want to
submit code. Details on contributing can be found in
[CONTRIBUTING.md](https://gitlab.com/wpettersson/kep_solver/-/blob/main/CONTRIBUTING.md). You can also get in touch directly, or
raise an [issue](https://gitlab.com/wpettersson/kep_solver/-/issues)

## Licensing

This software is licensed under the Affero GPL v3 License, as described in
[LICENSE](https://gitlab.com/wpettersson/kep_solver/-/blob/main/LICENSE).

TO THE EXTENT PERMITTED BY LAW, THIS SOFTWARE IS PROVIDED “AS IS”, WITHOUT
WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Acknowledgements

This software has been supported by the Engineering and Physical Sciences
Research Council (EPSRC) grants
[EP/T004878/1](https://gow.epsrc.ukri.org/NGBOViewGrant.aspx?GrantRef=EP/T004878/1)
(Multilayer Algorithmics to Leverage Graph Structure)
and
[EP/X013618/1](https://gow.epsrc.ukri.org/NGBOViewGrant.aspx?GrantRef=EP/X013618/1)
(KidneyAlgo: New Algorithms for UK and International Kidney Exchange).
