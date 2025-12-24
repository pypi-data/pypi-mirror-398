from dataclasses import dataclass

import pulp  # type: ignore


@dataclass
class RCVFStep:
    """A dataclass containing information about one step in using reduced cost
    variable fixing to solve an IP.
    """

    target: int
    """The target value for the IP at this step."""
    num_deactivated: int
    """The number of variables deactivated at this step."""
    time: float
    """How long the IP solve took at this particular step."""


@dataclass
class Level:
    """Details on the IP solving at one particular level of the objective
    hierarchy."""

    num_variables: int
    """How many variables are in the problem at this point."""
    num_constraints: int
    """How many constraints are in the problem at this point."""
    linear_value: float | None = None
    """What is the value of the linear relaxation at this point. Note that this
    is only properly calculated if one uses RCVF, otherwise a value of None is
    stored."""
    rcvf_steps: list[RCVFStep] | None = None
    """Contains details on how RCVF performed at each stage. If RCVF was never
    used, this value is just None.
    """


@dataclass
class TimeStep:
    """Details how long one particular step of a process took."""

    description: str
    """A description of the step in question."""
    time: float
    """How long this particular step took."""


@dataclass
class SolvingStatistics:
    """A dataclass containing information relevant to the solving of particular problems."""

    times: list[TimeStep]
    """A list of various steps involving in solving the problem. Each item is a
    TimeStep object.
    """
    levels: list[Level]
    """A list containing details on how each level of the objective hierarchy
    was solved.
    """


@dataclass
class SolvingOptions:
    solver: pulp.LpSolver = pulp.getSolver("PULP_CBC_CMD", msg=False)
    """What solver to use. The creation of the pulp LpSolver object also often
    includes solver-specific options."""
    useRCVF: bool | list[bool] = False
    """Either a single boolean denoting whether or not to use reduced cost
    variable fixing, or a list of booleans, one for each level of the objective
    hierarchy, such that for each level the corresponding boolean denotes
    whether to use reduced cost variable fixing. For more details on reduced
    cost variable fixing, see [Delorme23]_.
    """

    def useRCVFAtLevel(self, level: int) -> bool:
        """Returns True if and only if RCVF should be used at this level.

        :param level: The corresponding lever of the objective hierarchy.
        """
        if isinstance(self.useRCVF, bool):
            return self.useRCVF
        return self.useRCVF[level]
