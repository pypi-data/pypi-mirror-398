import pytest

import kep_solver.fileio as fileio
from kep_solver.graph import CompatibilityGraph, build_alternates_and_embeds
from kep_solver.entities import Status


@pytest.fixture(
    params=[
        ("JSON", fileio.read_json("tests/test_instances/test1.json")),
        ("XML", fileio.read_xml("tests/test_instances/test1.xml")),
    ]
)
def test_one(request):
    yield request.param


def test_instance_one_read(test_one) -> None:
    instance = test_one[1]
    graph = CompatibilityGraph(instance)
    assert graph.size == 4
    assert len(graph.edges()) == len(instance.transplants)


def test_instance_one_cycles(test_one) -> None:
    instance = test_one[1]
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    assert len(cycles) == 2
    cycle_indices = [[v.index for v in cycle] for cycle in cycles]
    assert [0, 1] in cycle_indices
    assert [1, 2, 3] in cycle_indices

    cycles = graph.findCycles(2)
    cycle_indices = [[v.index for v in cycle] for cycle in cycles]
    assert [0, 1] in cycle_indices
    assert len(cycles) == 1


def test_instance_one_donor_not_in_pool(test_one) -> None:
    instance = test_one[1]
    instance.donor("1").status = Status.Left
    graph = CompatibilityGraph(instance)
    assert graph.size == 3
    # Donor 1 is in 1 transplant, and recipient 1 is in 1 transplant
    assert len(graph.edges()) == len(instance.transplants) - 2
    instance.donor("2").status = Status.Left
    graph = CompatibilityGraph(instance)
    assert graph.size == 2
    # Donor 2 is in 2 transplants, and recipient 2 is in 2, but there are
    # two overlaps with transplants to/from donor 1/recipient 1
    assert len(graph.edges()) == len(instance.transplants) - 4
    instance.donor("1").status = Status.InPool
    graph = CompatibilityGraph(instance)
    assert graph.size == 3
    # Donor 2 is in 2 transplants, and recipient 2 is in 2.
    assert len(graph.edges()) == len(instance.transplants) - 4
    # Ensure the instance is set back the way it was
    instance.donor("2").status = Status.InPool


def test_instance_one_recipient_not_in_pool(test_one) -> None:
    instance = test_one[1]
    instance.recipient("1").status = Status.Left
    graph = CompatibilityGraph(instance)
    print(graph.vertices)
    assert graph.size == 3
    # Donor 1 is in 1 transplant, and recipient 1 is in 1 transplant
    assert len(graph.edges()) == len(instance.transplants) - 2
    instance.recipient("2").status = Status.Left
    graph = CompatibilityGraph(instance)
    assert graph.size == 2
    # Donor 2 is in 2 transplants, and recipient 2 is in 2, but there are
    # two overlaps with transplants to/from donor 1/recipient 1
    assert len(graph.edges()) == len(instance.transplants) - 4
    instance.recipient("1").status = Status.InPool
    graph = CompatibilityGraph(instance)
    assert graph.size == 3
    # Donor 2 is in 2 transplants, and recipient 2 is in 2.
    assert len(graph.edges()) == len(instance.transplants) - 4


@pytest.fixture(
    params=[
        ("JSON", fileio.read_json("tests/test_instances/test2.json")),
        ("XML", fileio.read_xml("tests/test_instances/test2.xml")),
    ]
)
def test_two(request):
    yield request.param


def test_instance_two_read(test_two) -> None:
    instance = test_two[1]
    graph = CompatibilityGraph(instance)
    assert graph.size == 6
    assert len(graph.edges()) == len(instance.transplants)


def test_instance_two_cycles(test_two) -> None:
    instance = test_two[1]
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    build_alternates_and_embeds(cycles)
    assert len(cycles) == 5
    cycle_indices = [[int(v.donor.id) for v in cycle] for cycle in cycles]
    assert [1, 2] in cycle_indices
    assert [3, 4] in cycle_indices
    assert [5, 6] in cycle_indices
    assert [1, 4, 2] in cycle_indices
    assert [3, 6, 5] in cycle_indices
    for cycle in cycles:
        if [1, 4, 2] == [int(v.donor.id) for v in cycle]:
            assert len(cycle.embedded) == 1
            # Check 0,1 is embedded
            assert [int(v.donor.id) for v in cycle.embedded[0]] == [1, 2]
        if [3, 6, 5] == [int(v.donor.id) for v in cycle]:
            assert len(cycle.embedded) == 1

    cycles = graph.findCycles(2)
    assert len(cycles) == 3
    cycle_indices = [[int(v.donor.id) for v in cycle] for cycle in cycles]
    assert [1, 2] in cycle_indices
    assert [3, 4] in cycle_indices
    assert [5, 6] in cycle_indices


def test_instance_two_embedded(test_two) -> None:
    instance = test_two[1]
    graph = CompatibilityGraph(instance)
    cycles = graph.findCycles(3)
    build_alternates_and_embeds(cycles)

    for cycle in cycles:
        vert_ids = [int(v.donor.id) for v in cycle]
        if vert_ids == [0, 3, 1]:
            assert len(cycle.embedded) == 1
            emb = cycle.embedded[0]
            emb_ids = [int(v.donor.id) for v in emb]
            assert emb_ids == [0, 1]
        elif vert_ids == [2, 5, 4]:
            assert len(cycle.embedded) == 1
            emb = cycle.embedded[0]
            emb_ids = [int(v.donor.id) for v in emb]
            assert emb_ids == [4, 5]
        elif len(cycle) == 2:
            assert len(cycle.embedded) == 0


@pytest.fixture(
    params=[
        ("JSON", fileio.read_json("tests/test_instances/test3b.json")),
        ("XML", fileio.read_xml("tests/test_instances/test3b.xml")),
    ]
)
def test_threeb(request):
    yield request.param


def test_instance_threeb_read(test_threeb) -> None:
    instance = test_threeb[1]
    graph = CompatibilityGraph(instance)
    assert graph.size == 4
    assert len(graph.edges()) == len(instance.transplants)


def test_instance_threeb_cycles(test_threeb) -> None:
    instance = test_threeb[1]
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    build_alternates_and_embeds(cycles)
    assert len(cycles) == 7
    checked = 0
    for cycle in cycles:
        indices = [int(v.donor.id) for v in cycle]
        if [1, 2] == indices:
            checked += 1
        if [1, 2, 3] == indices:
            checked += 1
            assert cycle.num_backarcs_uk() == 2
        if [1, 3] == indices:
            checked += 1
        if [1, 3, 4] == indices:
            assert cycle.num_backarcs_uk() == 3
            checked += 1
        if [1, 4] == indices:
            checked += 1
        if [1, 4, 3] == indices:
            assert cycle.num_backarcs_uk() == 3
            checked += 1
        if [3, 4] == indices:
            checked += 1
    assert checked == 7

    cycles = graph.findCycles(2)
    assert len(cycles) == 4
    cycle_indices = [[int(v.donor.id) for v in cycle] for cycle in cycles]
    assert [1, 2] in cycle_indices
    assert [1, 3] in cycle_indices
    assert [1, 4] in cycle_indices
    assert [3, 4] in cycle_indices


@pytest.fixture(
    params=[
        ("JSON", fileio.read_json("tests/test_instances/test5.json")),
        ("XML", fileio.read_xml("tests/test_instances/test5.xml")),
    ]
)
def test_five(request):
    yield request.param


def test_instance_five_read(test_five) -> None:
    instance = test_five[1]
    graph = CompatibilityGraph(instance)
    assert graph.size == 4
    assert len(graph.edges()) == len(instance.transplants)


def test_instance_five_chains(test_five) -> None:
    instance = test_five[1]
    graph = CompatibilityGraph(instance)
    chains = graph.findChains(2)
    assert len(chains) == 3
    chain_indices = [[int(v.donor.id) for v in chain] for chain in chains]
    assert [1] in chain_indices
    assert [1, 2] in chain_indices
    assert [1, 3] in chain_indices

    chains = graph.findChains(3)
    assert len(chains) == 4
    chain_indices = [[int(v.donor.id) for v in chain] for chain in chains]
    assert [1] in chain_indices
    assert [1, 2] in chain_indices
    assert [1, 3] in chain_indices
    assert [1, 3, 4] in chain_indices


def test_instance_five_embeds(test_five) -> None:
    instance = test_five[1]
    graph = CompatibilityGraph(instance)
    exchanges = graph.findCycles(3) + graph.findChains(3)
    build_alternates_and_embeds(exchanges)
    # Find the long chain
    for e in exchanges:
        if len(e) == 3:
            # Long chain
            assert len(e.alternates) == 0
            for c in e.embedded:
                print(f"{c=}")
            assert len(e.embedded) == 2


@pytest.fixture(
    params=[
        ("JSON", fileio.read_json("tests/test_instances/test6a.json")),
        ("XML", fileio.read_xml("tests/test_instances/test6a.xml")),
    ]
)
def test_sixa(request):
    yield request.param


def test_instance_sixa_alternates(test_sixa) -> None:
    instance = test_sixa[1]
    graph = CompatibilityGraph(instance)
    cycles = graph.findCycles(3)
    build_alternates_and_embeds(cycles)
    assert graph.size == 4
    assert len(instance.transplants) == 5
    assert len(graph.edges()) == 7
    assert len(cycles) == 3
    for cycle in cycles:
        vert_ids = [int(v.donor.id) for v in cycle]
        if vert_ids == [2, 3]:
            assert len(cycle.embedded) == 0
            assert len(cycle.alternates) == 1
            alt = cycle.alternates[0]
            alt_ids = [int(v.donor.id) for v in alt]
            assert alt_ids == [1, 2]
        if vert_ids == [1, 2]:
            assert len(cycle.embedded) == 0
            assert len(cycle.alternates) == 1
            alt = cycle.alternates[0]
            alt_ids = [int(v.donor.id) for v in alt]
            assert alt_ids == [2, 3]


@pytest.fixture(
    params=[
        ("JSON", fileio.read_json("tests/test_instances/test6b.json")),
        ("XML", fileio.read_xml("tests/test_instances/test6b.xml")),
    ]
)
def test_sixb(request):
    yield request.param


def test_instance_sixb_alternates(test_sixb) -> None:
    instance = test_sixb[1]
    graph = CompatibilityGraph(instance)
    cycles = graph.findCycles(3)
    build_alternates_and_embeds(cycles)
    assert graph.size == 4
    assert len(instance.transplants) == 4
    assert len(graph.edges()) == 5
    assert len(cycles) == 2
    for cycle in cycles:
        vert_ids = [int(v.donor.id) for v in cycle]
        if vert_ids == [2, 3, 4]:
            assert len(cycle.embedded) == 0
            assert len(cycle.alternates) == 1
            alt = cycle.alternates[0]
            alt_ids = [int(v.donor.id) for v in alt]
            assert alt_ids == [1, 2, 3]
        if vert_ids == [1, 2, 3]:
            assert len(cycle.embedded) == 0
            assert len(cycle.alternates) == 1
            alt = cycle.alternates[0]
            alt_ids = [int(v.donor.id) for v in alt]
            assert alt_ids == [2, 3, 4]


def test_eight_backarcs() -> None:
    instance = fileio.read_json("tests/test_instances/test8.json")
    graph = CompatibilityGraph(instance)
    exchanges = graph.findCycles(3) + graph.findChains(3)
    print(exchanges)
    build_alternates_and_embeds(exchanges)
    checked = 0
    for exchange in exchanges:
        vert_ids = [int(v.donor.id) for v in exchange]
        if vert_ids == [1, 2, 3]:
            assert exchange.num_backarcs_uk() == 1
            checked += 1
    assert checked == 1


def test_instance_eightb_alt_embed() -> None:
    instance = fileio.read_json("tests/test_instances/test8b.json")
    graph = CompatibilityGraph(instance)
    cycles = graph.findCycles(3)
    build_alternates_and_embeds(cycles)
    assert len(cycles) == 9
    checked = 0
    for cycle in cycles:
        indices = [int(v.donor.id) for v in cycle]
        if [1, 2] == indices:
            checked += 1
        if [1, 3] == indices:
            checked += 1
        if [1, 3, 4] == indices:
            assert len(cycle.alternates) == 3
            assert len(cycle.embedded) == 5
            checked += 1
        if [1, 4] == indices:
            checked += 1
        if [1, 4, 3] == indices:
            assert len(cycle.alternates) == 3
            assert len(cycle.embedded) == 5
            checked += 1
        if [3, 4] == indices:
            checked += 1
    assert checked == 6


def test_instance_eightb_alt_embed_nhs() -> None:
    instance = fileio.read_json("tests/test_instances/test8b.json")
    graph = CompatibilityGraph(instance)
    cycles = graph.findCycles(3)
    build_alternates_and_embeds(cycles, uk_variant=1)
    assert len(cycles) == 9
    checked = 0
    for cycle in cycles:
        indices = [int(v.donor.id) for v in cycle]
        if [1, 2] == indices:
            checked += 1
        if [1, 3] == indices:
            checked += 1
        if [1, 3, 4] == indices:
            assert len(cycle.alternates) == 1
            assert len(cycle.embedded) == 5
            checked += 1
        if [1, 4] == indices:
            checked += 1
        if [1, 4, 3] == indices:
            assert len(cycle.alternates) == 1
            assert len(cycle.embedded) == 5
            checked += 1
        if [3, 4] == indices:
            checked += 1
    assert checked == 6


def test_instance_eightb_alt_embed_nhs_two() -> None:
    instance = fileio.read_json("tests/test_instances/test8b.json")
    graph = CompatibilityGraph(instance)
    cycles = graph.findCycles(3)
    build_alternates_and_embeds(cycles, uk_variant=2)
    assert len(cycles) == 9
    checked = 0
    for cycle in cycles:
        indices = [int(v.donor.id) for v in cycle]
        if [1, 2] == indices:
            checked += 1
        if [1, 3] == indices:
            checked += 1
        if [1, 3, 4] == indices:
            assert len(cycle.alternates) == 1
            assert len(cycle.embedded) == 3
            checked += 1
        if [1, 4] == indices:
            checked += 1
        if [1, 4, 3] == indices:
            assert len(cycle.alternates) == 1
            assert len(cycle.embedded) == 3
            checked += 1
        if [3, 4] == indices:
            checked += 1
    assert checked == 6


def test_instance_eightc_alt_embed_nhs() -> None:
    instance = fileio.read_json("tests/test_instances/test8c.json")
    graph = CompatibilityGraph(instance)
    cycles = graph.findCycles(3)
    build_alternates_and_embeds(cycles, uk_variant=1)
    assert len(cycles) == 16
    checked = 0
    for cycle in cycles:
        indices = [int(v.donor.id) for v in cycle]
        if [1, 2] == indices:
            checked += 1
        if [1, 3] == indices:
            checked += 1
        if [1, 3, 4] == indices:
            assert len(cycle.alternates) == 3
            assert len(cycle.embedded) == 8
            checked += 1
        if [1, 4] == indices:
            checked += 1
        if [1, 4, 3] == indices:
            assert len(cycle.alternates) == 3
            assert len(cycle.embedded) == 8
            checked += 1
        if [3, 4] == indices:
            checked += 1
    assert checked == 6


def test_instance_eightc_alt_embed_nhs_two() -> None:
    instance = fileio.read_json("tests/test_instances/test8c.json")
    graph = CompatibilityGraph(instance)
    cycles = graph.findCycles(3)
    build_alternates_and_embeds(cycles, uk_variant=2)
    assert len(cycles) == 16
    checked = 0
    for cycle in cycles:
        indices = [int(v.donor.id) for v in cycle]
        if [1, 2] == indices:
            checked += 1
        if [1, 3] == indices:
            checked += 1
        if [1, 3, 4] == indices:
            assert len(cycle.alternates) == 3
            assert len(cycle.embedded) == 3
            checked += 1
        if [1, 4] == indices:
            checked += 1
        if [1, 4, 3] == indices:
            assert len(cycle.alternates) == 3
            assert len(cycle.embedded) == 3
            checked += 1
        if [3, 4] == indices:
            checked += 1
    assert checked == 6


def test_instance_eightb_backarcs() -> None:
    instance = fileio.read_json("tests/test_instances/test8b.json")
    graph = CompatibilityGraph(instance)
    cycles = graph.findCycles(3)
    build_alternates_and_embeds(cycles)
    assert len(cycles) == 9
    checked = 0
    for cycle in cycles:
        indices = [int(v.donor.id) for v in cycle]
        print(indices)
        if [1, 2] == indices:
            checked += 1
        if [1, 3] == indices:
            checked += 1
        if [1, 3, 4] == indices:
            assert cycle.num_backarcs_uk() == 3
            checked += 1
        if [1, 4] == indices:
            checked += 1
        if [1, 4, 3] == indices:
            assert cycle.num_backarcs_uk() == 3
            checked += 1
        if [3, 4] == indices:
            checked += 1
    assert checked == 6


def test_cycle_finding_medium1() -> None:
    instance = fileio.read_json("tests/test_instances/medium-1.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 66
    assert len([c for c in cycles if len(c) == 3]) == 191


def test_cycle_finding_medium2() -> None:
    instance = fileio.read_json("tests/test_instances/medium-2.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 68
    assert len([c for c in cycles if len(c) == 3]) == 199


def test_cycle_finding_medium3() -> None:
    instance = fileio.read_json("tests/test_instances/medium-3.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 55
    assert len([c for c in cycles if len(c) == 3]) == 180


def test_cycle_finding_medium4() -> None:
    instance = fileio.read_json("tests/test_instances/medium-4.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 28
    assert len([c for c in cycles if len(c) == 3]) == 95


def test_cycle_finding_medium5() -> None:
    instance = fileio.read_json("tests/test_instances/medium-5.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 58
    assert len([c for c in cycles if len(c) == 3]) == 193


def test_cycle_finding_medium6() -> None:
    instance = fileio.read_json("tests/test_instances/medium-6.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 41
    assert len([c for c in cycles if len(c) == 3]) == 142


def test_cycle_finding_medium7() -> None:
    instance = fileio.read_json("tests/test_instances/medium-7.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 48
    assert len([c for c in cycles if len(c) == 3]) == 163


def test_cycle_finding_medium8() -> None:
    instance = fileio.read_json("tests/test_instances/medium-8.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 41
    assert len([c for c in cycles if len(c) == 3]) == 92


def test_cycle_finding_medium9() -> None:
    instance = fileio.read_json("tests/test_instances/medium-9.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 79
    assert len([c for c in cycles if len(c) == 3]) == 373


def test_cycle_finding_medium10() -> None:
    instance = fileio.read_json("tests/test_instances/medium-10.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 56
    assert len([c for c in cycles if len(c) == 3]) == 156


def test_cycle_finding_large1() -> None:
    instance = fileio.read_json("tests/test_instances/large-1.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 696
    assert len([c for c in cycles if len(c) == 3]) == 6837


def test_cycle_finding_large2() -> None:
    instance = fileio.read_json("tests/test_instances/large-2.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 915
    assert len([c for c in cycles if len(c) == 3]) == 12175


def test_cycle_finding_large3() -> None:
    instance = fileio.read_json("tests/test_instances/large-3.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 930
    assert len([c for c in cycles if len(c) == 3]) == 13639


def test_cycle_finding_large4() -> None:
    instance = fileio.read_json("tests/test_instances/large-4.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 857
    assert len([c for c in cycles if len(c) == 3]) == 11761


def test_cycle_finding_large5() -> None:
    instance = fileio.read_json("tests/test_instances/large-5.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 835
    assert len([c for c in cycles if len(c) == 3]) == 12407


def test_cycle_finding_large6() -> None:
    instance = fileio.read_json("tests/test_instances/large-6.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 1070
    assert len([c for c in cycles if len(c) == 3]) == 13766


def test_cycle_finding_large7() -> None:
    instance = fileio.read_json("tests/test_instances/large-7.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 931
    assert len([c for c in cycles if len(c) == 3]) == 11139


def test_cycle_finding_large8() -> None:
    instance = fileio.read_json("tests/test_instances/large-8.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 1202
    assert len([c for c in cycles if len(c) == 3]) == 18319


def test_cycle_finding_large9() -> None:
    instance = fileio.read_json("tests/test_instances/large-9.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 1167
    assert len([c for c in cycles if len(c) == 3]) == 15610


def test_cycle_finding_large10() -> None:
    instance = fileio.read_json("tests/test_instances/large-10.json")
    graph = CompatibilityGraph(instance)

    cycles = graph.findCycles(3)
    cycles += graph.findChains(3)
    assert len([c for c in cycles if len(c) == 2]) == 1013
    assert len([c for c in cycles if len(c) == 3]) == 14655
