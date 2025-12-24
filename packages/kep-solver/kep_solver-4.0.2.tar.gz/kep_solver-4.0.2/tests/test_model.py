import pytest

import kep_solver.model as model
import kep_solver.graph as graphing
import kep_solver.fileio as fileio


@pytest.fixture(scope="module")
def test1_graph():
    instance = fileio.read_json("tests/test_instances/test1.json")
    graph = graphing.CompatibilityGraph(instance)
    return graph


@pytest.fixture(scope="module")
def test3b_graph():
    instance = fileio.read_json("tests/test_instances/test3b.json")
    graph = graphing.CompatibilityGraph(instance)
    return graph


@pytest.fixture(scope="module")
def test4_graph():
    instance = fileio.read_json("tests/test_instances/test4.json")
    graph = graphing.CompatibilityGraph(instance)
    return graph


@pytest.fixture(scope="module")
def test5_graph():
    instance = fileio.read_json("tests/test_instances/test5.json")
    graph = graphing.CompatibilityGraph(instance)
    return graph


@pytest.fixture(scope="module")
def test7_graph():
    instance = fileio.read_json("tests/test_instances/test7.json")
    graph = graphing.CompatibilityGraph(instance)
    return graph


@pytest.fixture(scope="module")
def test_simple_chains_graph():
    instance = fileio.read_json("tests/test_instances/test_simple_chains.json")
    graph = graphing.CompatibilityGraph(instance)
    return graph


def test_model_build_1() -> None:
    obj = model.TransplantCount()
    instance = fileio.read_json("tests/test_instances/test1.json")
    mod = model.CycleAndChainModel(instance, [obj], maxCycleLength=3, maxChainLength=3)
    mod.build_model()
    assert len(mod.cycles) == 2
    assert len(mod.chains) == 0


def test_model_build_1_no_cycles() -> None:
    obj = model.TransplantCount()
    instance = fileio.read_json("tests/test_instances/test1.json")
    mod = model.CycleAndChainModel(instance, [obj], maxCycleLength=0, maxChainLength=3)
    mod.build_model()
    assert len(mod.cycles) == 0
    assert len(mod.chains) == 0


def test_transplant_count_test1(test1_graph) -> None:
    obj = model.TransplantCount()
    cycles = test1_graph.findCycles(3)
    for cycle in cycles:
        indices = [int(v.donor.id) for v in cycle]
        if indices == [1, 2]:
            assert obj.value(test1_graph, cycle) == 2
        if indices == [1, 2, 3]:
            assert obj.value(test1_graph, cycle) == 3


def test_transplant_count_test5(test5_graph) -> None:
    obj = model.TransplantCount()
    chains = test5_graph.findChains(3)
    for chain in chains:
        indices = [int(v.donor.id) for v in chain]
        if indices == [1, 2]:
            assert obj.value(test5_graph, chain) == 2
        if indices == [1, 3, 4]:
            assert obj.value(test5_graph, chain) == 3


def test_model_build_5() -> None:
    obj = model.TransplantCount()
    instance = fileio.read_json("tests/test_instances/test5.json")
    mod = model.CycleAndChainModel(instance, [obj], maxCycleLength=3, maxChainLength=3)
    mod.build_model()
    assert len(mod.cycles) == 1
    assert len(mod.chains) == 4


def test_model_build_5b() -> None:
    obj = model.TransplantCount()
    instance = fileio.read_json("tests/test_instances/test5b.json")
    mod = model.CycleAndChainModel(instance, [obj], maxCycleLength=3, maxChainLength=3)
    mod.build_model()
    assert len(mod.cycles) == 1
    assert len(mod.chains) == 3
    # Make sure all exchanges have different IDs
    all_ids = set()
    for e in mod.cycles:
        assert e.id not in all_ids
        all_ids.add(e.id)
    for e in mod.chains:
        assert e.id not in all_ids
        all_ids.add(e.id)


def test_model_build_8b() -> None:
    obj = model.TransplantCount()
    instance = fileio.read_json("tests/test_instances/test8b.json")
    mod = model.CycleAndChainModel(instance, [obj], maxCycleLength=3, maxChainLength=3)
    mod.build_model()
    assert len(mod.cycles) == 9
    assert len(mod.chains) == 0


def test_model_alt_embed_required() -> None:
    instance = fileio.read_json("tests/test_instances/test1.json")
    assert model.EffectiveTwoWay().need_alt_embed == True
    assert model.TransplantCount().need_alt_embed == False
    with pytest.raises(Exception, match="needs alternates and embeddeds built"):
        model.CycleAndChainModel(
            instance,
            [model.EffectiveTwoWay()],
            maxChainLength=3,
            maxCycleLength=3,
        )
    model.CycleAndChainModel(
        instance,
        [model.TransplantCount()],
        maxChainLength=3,
        maxCycleLength=3,
    )


def test_effective_twoway_count_test1(test1_graph) -> None:
    obj = model.EffectiveTwoWay()
    cycles = test1_graph.findCycles(3)
    for cycle in cycles:
        indices = [int(v.donor.id) for v in cycle]
        if indices == [1, 2]:
            assert obj.value(test1_graph, cycle) == 1
        if indices == [1, 2, 3]:
            assert obj.value(test1_graph, cycle) == 0


def test_effective_twoway_count_test4(test4_graph) -> None:
    obj = model.EffectiveTwoWay()
    cycles = test4_graph.findCycles(3)
    graphing.build_alternates_and_embeds(cycles)
    for cycle in cycles:
        indices = [int(v.donor.id) for v in cycle]
        if indices == [1, 2]:
            assert obj.value(test4_graph, cycle) == 1
        if indices == [1, 2, 4]:
            assert obj.value(test4_graph, cycle) == 1
        if indices == [2, 4, 3]:
            assert obj.value(test4_graph, cycle) == 0


def test_effective_twoway_count_chains(test_simple_chains_graph) -> None:
    obj = model.EffectiveTwoWay()
    cycles = test_simple_chains_graph.findCycles(3)
    chains = test_simple_chains_graph.findChains(3)
    graphing.build_alternates_and_embeds(cycles + chains)
    for chain in chains:
        indices = [int(v.donor.id) for v in chain]
        if indices == [1]:
            assert obj.value(test_simple_chains_graph, chain) == 0
        if indices == [2]:
            assert obj.value(test_simple_chains_graph, chain) == 0
        if indices == [2, 3]:
            assert obj.value(test_simple_chains_graph, chain) == 1


def test_backarcs_test3b(test3b_graph) -> None:
    obj = model.BackArcs()
    cycles = test3b_graph.findCycles(3)
    graphing.build_alternates_and_embeds(cycles)
    for cycle in cycles:
        indices = [int(v.donor.id) for v in cycle]
        if indices == [1, 2]:
            assert obj.value(test3b_graph, cycle) == 0
        if indices == [1, 2, 3]:
            assert obj.value(test3b_graph, cycle) == 2
        if indices == [1, 3]:
            assert obj.value(test3b_graph, cycle) == 0
        if indices == [1, 3, 4]:
            assert obj.value(test3b_graph, cycle) == 3
        if indices == [1, 4]:
            assert obj.value(test3b_graph, cycle) == 0
        if indices == [1, 4, 3]:
            assert obj.value(test3b_graph, cycle) == 3
        if indices == [3, 4]:
            assert obj.value(test3b_graph, cycle) == 0


def test_backarcs_test5(test5_graph) -> None:
    obj = model.BackArcs()
    chains = test5_graph.findChains(3)
    cycles = test5_graph.findCycles(3)
    graphing.build_alternates_and_embeds(chains + cycles)
    checked = 0
    for chain in chains:
        indices = [int(v.donor.id) for v in chain]
        if indices == [1, 2]:
            assert obj.value(test5_graph, chain) == 0
            checked += 1
        if indices == [1, 3, 4]:
            assert obj.value(test5_graph, chain) == 2
            checked += 1
    assert checked == 2


def test_nwayexchanges_test5(test5_graph) -> None:
    obj1 = model.nWayExchanges(1)
    obj2 = model.nWayExchanges(2)
    obj3 = model.nWayExchanges(3)
    chains = test5_graph.findChains(3)
    cycles = test5_graph.findCycles(3)
    graphing.build_alternates_and_embeds(chains + cycles)
    checked = 0
    for chain in chains:
        indices = [int(v.donor.id) for v in chain]
        print(indices)
        if indices == [1]:
            assert obj1.value(test5_graph, chain) == 1
            assert obj2.value(test5_graph, chain) == 0
            assert obj3.value(test5_graph, chain) == 0
            checked += 1
        if indices == [1, 2]:
            assert obj1.value(test5_graph, chain) == 0
            assert obj2.value(test5_graph, chain) == 1
            assert obj3.value(test5_graph, chain) == 0
            checked += 1
        if indices == [1, 3]:
            assert obj1.value(test5_graph, chain) == 0
            assert obj2.value(test5_graph, chain) == 1
            assert obj3.value(test5_graph, chain) == 0
            checked += 1
        if indices == [1, 3, 4]:
            assert obj1.value(test5_graph, chain) == 0
            assert obj2.value(test5_graph, chain) == 0
            assert obj3.value(test5_graph, chain) == 1
            checked += 1
    assert checked == 4


def test_backarcs_test7(test7_graph) -> None:
    obj = model.BackArcs()
    chains = test7_graph.findChains(3)
    cycles = test7_graph.findCycles(3)
    graphing.build_alternates_and_embeds(chains + cycles)
    checked = 0
    for exchange in chains + cycles:
        indices = [int(v.donor.id) for v in exchange]
        if indices == [125, 24, 11]:
            assert obj.value(test7_graph, exchange) == 2
            checked += 1
        if indices == [122, 83, 54]:
            assert obj.value(test7_graph, exchange) == 2
            checked += 1
        if indices == [27, 60, 46]:
            assert obj.value(test7_graph, exchange) == 1
            checked += 1
        if indices == [3, 102, 45]:
            assert obj.value(test7_graph, exchange) == 1
            checked += 1
        if indices == [123, 104, 43]:
            assert obj.value(test7_graph, exchange) == 2
            checked += 1
        if indices == [16, 44, 20]:
            assert obj.value(test7_graph, exchange) == 1
            checked += 1
        if indices == [121, 87, 34]:
            assert obj.value(test7_graph, exchange) == 2
            checked += 1
    assert checked == 7


def test_threeway_count_test1(test1_graph) -> None:
    obj = model.ThreeWay()
    cycles = test1_graph.findCycles(3)
    checked = 0
    for cycle in cycles:
        indices = [int(v.donor.id) for v in cycle]
        if indices == [1, 2]:
            assert obj.value(test1_graph, cycle) == 0
            checked += 1
        if indices == [2, 3, 4]:
            assert obj.value(test1_graph, cycle) == 1
            checked += 1
    assert checked == 2


def test_threeway_count_test3b(test3b_graph) -> None:
    obj = model.ThreeWay()
    cycles = test3b_graph.findCycles(3)
    graphing.build_alternates_and_embeds(cycles)
    checked = 0
    for cycle in cycles:
        indices = [int(v.donor.id) for v in cycle]
        if indices == [1, 2]:
            assert obj.value(test3b_graph, cycle) == 0
            checked += 1
        if indices == [1, 2, 3]:
            assert obj.value(test3b_graph, cycle) == 1
            checked += 1
        if indices == [1, 3]:
            assert obj.value(test3b_graph, cycle) == 0
            checked += 1
        if indices == [1, 3, 4]:
            assert obj.value(test3b_graph, cycle) == 1
            checked += 1
        if indices == [1, 4]:
            assert obj.value(test3b_graph, cycle) == 0
            checked += 1
        if indices == [1, 4, 3]:
            assert obj.value(test3b_graph, cycle) == 1
            checked += 1
        if indices == [3, 4]:
            assert obj.value(test3b_graph, cycle) == 0
            checked += 1
    assert checked == 7


def test_threeway_count_test5(test5_graph) -> None:
    obj = model.ThreeWay()
    cycles = test5_graph.findCycles(3)
    chains = test5_graph.findChains(3)
    checked = 0
    for exchange in chains + cycles:
        indices = [int(v.donor.id) for v in exchange]
        if indices == [1, 2]:
            assert obj.value(test5_graph, exchange) == 0
            checked += 1
        if indices == [3, 4]:
            assert obj.value(test5_graph, exchange) == 0
            checked += 1
        if indices == [1, 3]:
            assert obj.value(test5_graph, exchange) == 0
            checked += 1
        if indices == [1, 3, 4]:
            assert obj.value(test5_graph, exchange) == 1
            checked += 1
    assert checked == 4


@pytest.mark.parametrize(
    "maxCycleLength, maxChainLength, length, count",
    [
        (3, 3, 3, 1),
        (3, 3, 4, 0),
        (4, 4, 4, 0),
    ],
)
def test_nway_count_test1(
    test5_graph,
    maxCycleLength,
    maxChainLength,
    length,
    count,
) -> None:
    obj = model.nWayCycles(length=length)
    cycles = test5_graph.findCycles(maxCycleLength)
    chains = test5_graph.findChains(maxChainLength)
    checked = 0
    for exchange in cycles:
        indices = [int(v.donor.id) for v in exchange]
        if len(indices) == length:
            assert obj.value(test5_graph, exchange) == 1
            checked += 1
    for exchange in chains:
        indices = [int(v.donor.id) for v in exchange]
        if len(indices) == length:
            assert obj.value(test5_graph, exchange) == 0
            checked += 1
    assert checked == count


@pytest.mark.parametrize(
    "maxCycleLength, maxChainLength, length, count",
    [
        (3, 3, 3, 191),
        (3, 3, 4, 0),
        (4, 4, 4, 562),
    ],
)
def test_nway_count_test2(
    maxCycleLength,
    maxChainLength,
    length,
    count,
) -> None:
    instance = fileio.read_json("tests/test_instances/medium-1.json")
    graph = graphing.CompatibilityGraph(instance)
    obj = model.nWayCycles(length=length)
    cycles = graph.findCycles(maxCycleLength)
    chains = graph.findChains(maxChainLength)
    checked = 0
    for exchange in cycles:
        indices = [int(v.donor.id) for v in exchange]
        if len(indices) == length:
            assert obj.value(graph, exchange) == 1
            checked += 1
    for exchange in chains:
        indices = [int(v.donor.id) for v in exchange]
        if len(indices) == length:
            assert obj.value(graph, exchange) == 0
            checked += 1
    assert checked == count


def test_ukscore_test1(test1_graph) -> None:
    obj = model.UKScore()
    cycles = test1_graph.findCycles(3)
    checked = 0
    for cycle in cycles:
        indices = [int(v.donor.id) for v in cycle]
        if indices == [1, 2]:
            assert obj.value(test1_graph, cycle) == 8.098
            checked += 1
        if indices == [2, 3, 4]:
            assert obj.value(test1_graph, cycle) == 12.121
            checked += 1
    assert checked == 2


def test_ukscore_test5(test5_graph) -> None:
    obj = model.UKScore()
    cycles = test5_graph.findCycles(3)
    chains = test5_graph.findChains(3)
    checked = 0
    for exchange in chains + cycles:
        indices = [int(v.donor.id) for v in exchange]
        print(indices)
        if indices == [1, 2]:
            assert obj.value(test5_graph, exchange) == 4.049
            checked += 1
        if indices == [3, 4]:
            assert obj.value(test5_graph, exchange) == 8.072
            checked += 1
        if indices == [1, 3]:
            assert obj.value(test5_graph, exchange) == 4.036
            checked += 1
        if indices == [1, 3, 4]:
            assert obj.value(test5_graph, exchange) == 8.072
            checked += 1
    assert checked == 4
