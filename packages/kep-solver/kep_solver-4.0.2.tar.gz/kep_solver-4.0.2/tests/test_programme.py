import pytest

import pulp  # type: ignore

import kep_solver.model as model
import kep_solver.programme as programme
import kep_solver.fileio as fileio


@pytest.fixture(
    scope="module",
    params=[
        ("CycleAndChainModel", model.CycleAndChainModel),
        ("PICEF", model.PICEF),
    ],
)
def transplant_programme_details(request):
    obj = model.TransplantCount()
    yield (
        request.param[0],
        programme.Programme(
            [obj],
            description="Test Programme",
            maxCycleLength=3,
            maxChainLength=3,
            model=request.param[1],
            full_details=request.param[0] == "CycleAndChainModel",
        ),
    )


def test_transplant_count_test1(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test1.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 3


def test_transplant_count_possible(transplant_programme_details) -> None:
    for testfile in [
        "tests/test_instances/test1.json",
        "tests/test_instances/test2.json",
        "tests/test_instances/test3.json",
        "tests/test_instances/test3b.json",
        "tests/test_instances/test4.json",
        "tests/test_instances/test5.json",
    ]:
        instance = fileio.read_json(testfile)
        solution, _ = transplant_programme_details[1].solve_single(instance)
        for exchange in solution.possible:
            assert len(exchange.exchange) == exchange.values[0]


def test_transplant_count_test2(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test2.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 6


def test_transplant_count_test3(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test3.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 3


def test_transplant_count_test3b(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test3b.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 4


def test_transplant_count_test4(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test4.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 3


def test_transplant_count_test5(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test5.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 4


def test_transplant_count_empty_objective_cf() -> None:
    instance = fileio.read_json("tests/test_instances/test6b.json")
    prog = programme.Programme(
        [model.TransplantCount(), model.BackArcs()],
        description="Test Programme",
        maxCycleLength=3,
        maxChainLength=3,
        build_alt_embed=1,
    )
    solution, _ = prog.solve_single(instance)
    assert solution is not None
    size = sum(len(e) for e in solution.selected)
    assert solution.values[0] == 3
    assert size == 3


def test_transplant_count_empty_objective_picef() -> None:
    instance = fileio.read_json("tests/test_instances/test6a.json")
    prog = programme.Programme(
        [model.TransplantCount(), model.ThreeWay()],
        description="Test Programme",
        maxCycleLength=3,
        maxChainLength=3,
        model=model.PICEF,
        full_details=False,
    )
    solution, _ = prog.solve_single(instance)
    assert solution is not None
    size = sum(len(e) for e in solution.selected)
    assert solution.values[0] == 2
    assert size == 2


def test_picef_no_full_details() -> None:
    with pytest.raises(Exception, match="does not support full details"):
        programme.Programme(
            [model.TransplantCount(), model.ThreeWay()],
            description="Test Programme",
            maxCycleLength=3,
            maxChainLength=3,
            model=model.PICEF,
            full_details=True,
        )


def test_transplant_count_medium1(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/medium-1.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 23


def test_transplant_count_medium2(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/medium-2.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 22


def test_transplant_count_medium3(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/medium-3.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 22


def test_transplant_count_medium4(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/medium-4.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 19


def test_transplant_count_medium5(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/medium-5.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 23


def test_transplant_count_medium6(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/medium-6.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 23


def test_transplant_count_medium7(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/medium-7.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 23


def test_transplant_count_medium8(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/medium-8.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 18


def test_transplant_count_medium9(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/medium-9.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 30


def test_transplant_count_medium10(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/medium-10.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 21


def test_transplant_count_large1(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/large-1.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 146


def test_transplant_count_large2(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/large-2.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 168


def test_transplant_count_large3(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/large-3.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 161


def test_transplant_count_large4(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/large-4.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 149


def test_transplant_count_large5(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/large-5.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 162


def test_transplant_count_large6(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/large-6.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 152


def test_transplant_count_large7(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/large-7.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 154


def test_transplant_count_large8(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/large-8.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 176


def test_transplant_count_large9(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/large-9.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 174


def test_transplant_count_large10(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/large-10.json")
    solution, _ = transplant_programme_details[1].solve_single(instance)
    assert solution.values[0] == 158


def test_transplant_count_medium1_solver(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/medium-1.json")
    solvingOptions = model.SolvingOptions(
        solver=pulp.HiGHS(msg=False),
        useRCVF=False,
    )
    solution, _ = transplant_programme_details[1].solve_single(
        instance,
        solvingOptions=solvingOptions,
    )
    assert solution.values[0] == 23


def test_transplant_count_medium1_rcvf(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/medium-1.json")
    solvingOptions = model.SolvingOptions(
        useRCVF=True,
    )
    solution, _ = transplant_programme_details[1].solve_single(
        instance,
        solvingOptions=solvingOptions,
    )
    assert solution.values[0] == 23


def test_transplant_count_large1_rcvf(transplant_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/large-1.json")
    solvingOptions = model.SolvingOptions(
        useRCVF=True,
    )
    solution, _ = transplant_programme_details[1].solve_single(
        instance,
        solvingOptions=solvingOptions,
    )
    print(transplant_programme_details[0])
    print(solution.times)
    assert solution.values[0] == 146


@pytest.fixture(
    scope="module",
    params=[
        ("CycleAndChainModel", model.CycleAndChainModel),
        # ("PICEF", model.PICEF),  Cannot optimise this objective
    ],
)
def twoway_programme_details(request):
    obj = model.EffectiveTwoWay()
    yield (
        request.param[0],
        programme.Programme(
            [obj],
            description="Test Programme",
            maxCycleLength=3,
            maxChainLength=3,
            model=request.param[1],
            build_alt_embed=1,
        ),
    )


def test_effective_twoway_count_test1(twoway_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test1.json")
    solution, _ = twoway_programme_details[1].solve_single(instance)
    assert solution.values[0] == 1


def test_effective_twoway_count_test2(twoway_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test2.json")
    solution, _ = twoway_programme_details[1].solve_single(instance)
    assert solution.values[0] == 3


def test_effective_twoway_count_test3(twoway_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test3.json")
    solution, _ = twoway_programme_details[1].solve_single(instance)
    assert solution.values[0] == 1


def test_effective_twoway_count_test3b(twoway_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test3b.json")
    solution, _ = twoway_programme_details[1].solve_single(instance)
    assert solution.values[0] == 2


def test_effective_twoway_count_test4(twoway_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test4.json")
    solution, _ = twoway_programme_details[1].solve_single(instance)
    assert solution.values[0] == 1


def test_effective_twoway_count_test5(twoway_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test5.json")
    solution, _ = twoway_programme_details[1].solve_single(instance)
    assert solution.values[0] == 2


@pytest.fixture(
    scope="module",
    params=[
        ("CycleAndChainModel", model.CycleAndChainModel),
        # ("PICEF", model.PICEF),  # Cannot optimise this objective
    ],
)
def backarc_programme_details(request):
    obj = model.BackArcs()
    yield (
        request.param[0],
        programme.Programme(
            [obj],
            description="Test Programme",
            maxCycleLength=3,
            maxChainLength=3,
            build_alt_embed=1,
            model=request.param[1],
        ),
    )


def test_backarcs_test3(backarc_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test3b.json")
    solution, _ = backarc_programme_details[1].solve_single(instance)
    assert solution.values[0] == 3


def test_backarcs_test5(backarc_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test5.json")
    solution, _ = backarc_programme_details[1].solve_single(instance)
    assert solution.values[0] == 2


@pytest.fixture(
    scope="module",
    params=[
        ("CycleAndChainModel", model.CycleAndChainModel),
        # ("PICEF", model.PICEF),  Cannot optimise this objective
    ],
)
def threeway_programme_details(request):
    obj = model.ThreeWay()
    yield (
        request.param[0],
        programme.Programme(
            [obj],
            description="Test Programme",
            maxCycleLength=3,
            maxChainLength=3,
            build_alt_embed=1,
            model=request.param[1],
        ),
    )


def test_threeway_count_test1(threeway_programme_details) -> None:
    instance = fileio.read_json("tests/test_instances/test1.json")
    solution, _ = threeway_programme_details[1].solve_single(instance)
    assert solution.values[0] == 0


@pytest.mark.parametrize(
    "maxCycleLength, maxChainLength, threeWayLimit, nTransplants, nThreeWays",
    [
        (3, 3, None, 22, 5),
        (3, 3, 2, 19, 2),
        (4, 4, 2, 22, 0),
    ],
)
def test_threeway_extra_constraint_test1(
    maxCycleLength: int,
    maxChainLength: int,
    threeWayLimit: int | None,
    nTransplants: int,
    nThreeWays: int,
) -> None:
    instance = fileio.read_json("tests/test_instances/medium-3.json")
    extra_cons: list[tuple[model.Objective, int]]
    if threeWayLimit is not None:
        extra_cons = [(model.ThreeWay(), threeWayLimit)]
    else:
        extra_cons = []
    this_model = model.CycleAndChainModel(
        instance,
        [model.TransplantCount()],
        maxChainLength=maxChainLength,
        maxCycleLength=maxCycleLength,
        extra_constraints=extra_cons,
    )
    solution, stats, numSols = this_model.solve()
    ntrans = sum(len(s) for s in solution)
    nthrees = len(list(e for e in solution if len(e.vertices) == 3))
    assert ntrans == nTransplants
    assert nthrees == nThreeWays
