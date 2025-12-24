*****
Usage
*****

Who is this for
===============

This particular package is most likely to be useful for people either
developing algorithms for techniques for KEPs, or setting kep_solver for use
within an organisation with specific requirements. A sample web interface is
viewable at https://kep-web.optimalmatching.com, and the code for said
interface is at https://gitlab.com/wpettersson/kep_web.

Installing
==========

This package is available via pip, and requires Python 3.10 at least. To install
it, I recommend using a Python virtual environment (see `virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/>`_ for an easy-to-use introduction) and then running ``pip install kep_solver``

Reading and inspecting instances
================================

File IO functionality is available in the :doc:`kep_solver.fileio` module. The
following code should read in any supported file format.
::

    from kep_solver.fileio import read_file
    instance = read_file("instance.json")

Instances can be analysed for a number of properties, as can the Donor and
Recipient entities they contain. These are documented in :doc:`kep_solver.entities`.
::

    print(f"This instance has {len(instance.recipients)} recipients")

Analysing the compatibility graph
=================================

The underlying compatibility graph can be accessed by creating a
:ref:`compatibility graph` object as follows. Specifics are documented in
:doc:`kep_solver.graph`.
::

    graph = CompatibilityGraph(instance)
    cycles = graph.findCycles(maxCycleLength)
    chains = graph.findChains(maxChainLength)
    print(f"There are {len(cycles)} cycles and {len(chains)} chains")


Using different models
======================

Different IP models can be used for solving KEP instances, and kep\_solver currently supports two such models: the :class:`kep_solver.models.CycleAndChainFormulation` [Abraham07]_ [Roth07]_ and :class:`kep_solver.models.PICEF` [Dickerson16]_. PICEF is currently significantly faster for longer chain lengths, but not all objectives are able to be used with PICEF. As such, the cycle and chain formulation is still the default. An example using PICEF is given below.
::

    from kep_solver.model import PICEF
    model = PICEF(
                  instance,
                  objectives,
                  maxChainLength=chain_length,
                  maxCycleLength=cycle_length,
                 )
    solution, model_times, numSols = model.solve()

You can also create a :class:`kep_solver.programme.Programme` that uses :class:`kep_solver.models.PICEF` by default.
::

    from kep_solver.programme import Programme
    from kep_solver.model import TransplantCount, PICEF
    programme = Programme(
                objectives=[TransplantCount()],
                maxCycleLength=3,
                maxChainLength=6,
                description="My PICEF Programme",
                model=PICEF,
               )
    solution, model = programme.solve_single(instance)


As mentioned above, not all objectives are compatible with PICEF. If you see an exception stating that "Edge value is not defined for this objective", then this indicates that the objective cannot be used with PICEF as the model.


Creating new objectives
=======================

New objectives can be created by inheriting from the :class:`kep_solver.model.Objective` and implementing :func:`kep_solver.model.Objective.value` (as well as a constructor). Note that if you wish to use :class:`kep_solver.model.PICEF` you will also need to implement :func:`kep_solver.model.Objective.edgeValue` which takes as input the compatibility graph, the edge of the compatibility, and also the position of said edge in the chain. An example objective that maximises the number of 4-chains using either PICEF or the cycle formulation is given below. Note that for PICEF, this functions by counting each edge used in 4th position in a chain positively, but subtracting each edge used in 5th position in a chain.

::

    from typing import Optional
    from kep_solver.graph import CompatibilityGraph, Edge, Exchange
    from kep_solver.model import Objective, Sense

    class FourChain(Objective):

        def __init__(self):
            pass

        def edgeValue(
            self, graph: CompatibilityGraph, edge: Edge, position: Optional[int] = None
        ) -> float:
            """What value should the given transplant in the given graph be given,
            if it is at the given position (i.e., position = 1 means this is the
            first edge in a chain)?

            :param graph: The graph containing the exchange
            :param edge: The edge, representing a transplant
            :param position: The position of this edge in an exchange
            :return: The value of this edge in this position
            """
            if position == 4:
                return 1
            if position == 5:
                return -1
            return 0

        def value(self, graph: CompatibilityGraph, exchange: Exchange) -> float:
            """Is the given exchange a 4-chain.

            :param graph: The graph containing the exchange
            :param exchange: A cycle or chain.
            :return: the number of transplants
            """
            if exchange.chain and len(exchange) == 4:
                    return 1
            return 0

        def describe(self) -> str:
            """Describes what this objective optimises.

            :return: the description
            """
            return "Number of 4-chains"

        @property
        def sense(self) -> Sense:
            """This is a maximisation objective."""
            return Sense.MAX
