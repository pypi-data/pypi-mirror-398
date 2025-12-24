import pytest

from collections import defaultdict
import random
import re

import kep_solver.generation as generation
import kep_solver.published_generators as published_gens
from kep_solver.entities import BloodGroup, Instance

# Seed for RNG for reproducible tests
SEED = 12345


def assertEqualWithMargin(one, two, margin, delta):
    assert one <= two * (1 + margin) + delta
    assert one >= two * (1 - margin) - delta


def test_bg_gen_one() -> None:
    dist = {
        BloodGroup.O: 0.25,
        BloodGroup.A: 0.25,
        BloodGroup.B: 0.25,
        BloodGroup.AB: 0.25,
    }
    gen = generation.BloodGroupGenerator(dist)
    # With the forced seed, I test 7 generations just to ensure that each blood
    # group does appear.
    random.seed(SEED)
    bg = gen.draw()
    assert bg == BloodGroup.A
    bg = gen.draw()
    assert bg == BloodGroup.O
    bg = gen.draw()
    assert bg == BloodGroup.AB
    bg = gen.draw()
    assert bg == BloodGroup.A
    bg = gen.draw()
    assert bg == BloodGroup.A
    bg = gen.draw()
    assert bg == BloodGroup.O
    bg = gen.draw()
    assert bg == BloodGroup.B


def test_bg_gen_from_json() -> None:
    dist = {"O": 0.25, "A": 0.25, "B": 0.25, "AB": 0.25}
    gen = generation.BloodGroupGenerator.from_json(dist)
    # With the forced seed, I test 7 generations just to ensure that each blood
    # group does appear.
    random.seed(SEED)
    bg = gen.draw()
    assert bg == BloodGroup.A
    bg = gen.draw()
    assert bg == BloodGroup.O
    bg = gen.draw()
    assert bg == BloodGroup.AB
    bg = gen.draw()
    assert bg == BloodGroup.A
    bg = gen.draw()
    assert bg == BloodGroup.A
    bg = gen.draw()
    assert bg == BloodGroup.O
    bg = gen.draw()
    assert bg == BloodGroup.B


def test_bg_gen_to_config() -> None:
    dist = {
        BloodGroup.O: 0.25,
        BloodGroup.A: 0.25,
        BloodGroup.B: 0.25,
        BloodGroup.AB: 0.25,
    }
    gen = generation.BloodGroupGenerator(dist)
    assert gen.config() == {"O": 0.25, "A": 0.25, "B": 0.25, "AB": 0.25}


def test_bg_gen_bad_dist() -> None:
    dist = {
        BloodGroup.O: 0.25,
        BloodGroup.A: 0.25,
        BloodGroup.B: 0.5,
        BloodGroup.AB: 0.5,
    }
    with pytest.raises(
        Exception, match=re.escape("Blood group distribution does not sum to one (1.5)")
    ):
        gen = generation.BloodGroupGenerator(dist)


def test_bg_gen() -> None:
    dist = {
        BloodGroup.O: 0.45,
        BloodGroup.A: 0.35,
        BloodGroup.B: 0.05,
        BloodGroup.AB: 0.15,
    }
    # Now we pull a proper random seed.
    random.seed()
    gen = generation.BloodGroupGenerator(dist)
    counts = {BloodGroup.O: 0, BloodGroup.A: 0, BloodGroup.B: 0, BloodGroup.AB: 0}
    # Note that the number of samples and margins allowed for assertions are
    # related, changing one without changing the other may result in errors
    samples = 25000
    for _ in range(samples):
        counts[gen.draw()] += 1
    for group in dist.keys():
        assert counts[group] > 0.9 * samples * dist[group]
        assert counts[group] < 1.1 * samples * dist[group]


def test_donor_count_gen_one() -> None:
    dist = {1: 0.67, 2: 0.22, 3: 0.10, 4: 0.01}
    gen = generation.DonorCountGenerator(dist)
    # With the forced seed, we test a bunch of draws until we at least see a 3.
    random.seed(SEED)
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 2
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 3


def test_donor_count_gen_from_json() -> None:
    dist = {"1": 0.67, "2": 0.22, "3": 0.10, "4": 0.01}
    gen = generation.DonorCountGenerator.from_json(dist)
    # With the forced seed, we test a bunch of draws until we at least see a 3.
    random.seed(SEED)
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 2
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 1
    numDonors = gen.draw()
    assert numDonors == 3


def test_donor_count_gen_to_config() -> None:
    dist = {1: 0.67, 2: 0.22, 3: 0.10, 4: 0.01}
    gen = generation.DonorCountGenerator(dist)
    assert gen.config() == dist


def test_donor_count_gen_bad_dist() -> None:
    dist = {1: 0.25, 2: 0.25, 3: 0.5, 4: 0.5}
    with pytest.raises(
        Exception, match=re.escape("Distribution does not sum to one (1.5)")
    ):
        gen = generation.DonorCountGenerator(dist)


def test_donor_gen_single() -> None:
    bg_dist = {
        BloodGroup.O: 0.25,
        BloodGroup.A: 0.25,
        BloodGroup.B: 0.25,
        BloodGroup.AB: 0.25,
    }
    bgen = generation.BloodGroupGenerator(bg_dist)
    dgen = generation.DonorGenerator(bgen)
    donor = dgen.draw("id1")
    assert donor.id == "id1"
    assert donor.bloodGroup in [BloodGroup.O, BloodGroup.A, BloodGroup.B, BloodGroup.AB]


def test_donor_gen_single_from_json() -> None:
    json = {"Generic": {"O": 0.25, "A": 0.25, "B": 0.25, "AB": 0.25}}
    dgen = generation.DonorGenerator.from_json(json)
    donor = dgen.draw("id1")
    assert donor.id == "id1"
    assert donor.bloodGroup in [BloodGroup.O, BloodGroup.A, BloodGroup.B, BloodGroup.AB]


def test_donor_gen_all() -> None:
    bg_dist = {
        BloodGroup.O: 0.25,
        BloodGroup.A: 0.25,
        BloodGroup.B: 0.25,
        BloodGroup.AB: 0.25,
    }
    bgen = generation.BloodGroupGenerator(bg_dist)
    bg_dist_o = {
        BloodGroup.O: 0.0,
        BloodGroup.A: 0.0,
        BloodGroup.B: 0.0,
        BloodGroup.AB: 1.0,
    }
    bgen_o = generation.BloodGroupGenerator(bg_dist_o)
    bg_dist_a = {
        BloodGroup.O: 0.0,
        BloodGroup.A: 0.0,
        BloodGroup.B: 1.0,
        BloodGroup.AB: 0.0,
    }
    bgen_a = generation.BloodGroupGenerator(bg_dist_a)
    bg_dist_b = {
        BloodGroup.O: 0.0,
        BloodGroup.A: 1.0,
        BloodGroup.B: 0.0,
        BloodGroup.AB: 0.0,
    }
    bgen_b = generation.BloodGroupGenerator(bg_dist_b)
    bg_dist_ab = {
        BloodGroup.O: 1.0,
        BloodGroup.A: 0.0,
        BloodGroup.B: 0.0,
        BloodGroup.AB: 0.0,
    }
    bgen_ab = generation.BloodGroupGenerator(bg_dist_ab)
    dgen = generation.DonorGenerator(
        bgen,
        recipient_o_generator=bgen_o,
        recipient_a_generator=bgen_a,
        recipient_b_generator=bgen_b,
        recipient_ab_generator=bgen_ab,
    )
    donor = dgen.draw("id1", BloodGroup.O)
    assert donor.bloodGroup == BloodGroup.AB
    donor = dgen.draw("id1", BloodGroup.A)
    assert donor.bloodGroup == BloodGroup.B
    donor = dgen.draw("id1", BloodGroup.B)
    assert donor.bloodGroup == BloodGroup.A
    donor = dgen.draw("id1", BloodGroup.AB)
    assert donor.bloodGroup == BloodGroup.O


def test_donor_gen_all_from_json() -> None:
    bg_dist = {"O": 0.25, "A": 0.25, "B": 0.25, "AB": 0.25}
    bg_dist_o = {"O": 0.0, "A": 0.0, "B": 0.0, "AB": 1.0}
    bg_dist_a = {"O": 0.0, "A": 0.0, "B": 1.0, "AB": 0.0}
    bg_dist_b = {"O": 0.0, "A": 1.0, "B": 0.0, "AB": 0.0}
    bg_dist_ab = {"O": 1.0, "A": 0.0, "B": 0.0, "AB": 0.0}
    dgen = generation.DonorGenerator.from_json(
        {
            "Generic": bg_dist,
            "O": bg_dist_o,
            "A": bg_dist_a,
            "B": bg_dist_b,
            "AB": bg_dist_ab,
        }
    )
    donor = dgen.draw("id1", BloodGroup.O)
    assert donor.bloodGroup == BloodGroup.AB
    donor = dgen.draw("id1", BloodGroup.A)
    assert donor.bloodGroup == BloodGroup.B
    donor = dgen.draw("id1", BloodGroup.B)
    assert donor.bloodGroup == BloodGroup.A
    donor = dgen.draw("id1", BloodGroup.AB)
    assert donor.bloodGroup == BloodGroup.O


def test_donor_gen_all_to_config() -> None:
    bg_dist = {
        BloodGroup.O: 0.25,
        BloodGroup.A: 0.25,
        BloodGroup.B: 0.25,
        BloodGroup.AB: 0.25,
    }
    bgen = generation.BloodGroupGenerator(bg_dist)
    bg_dist_o = {
        BloodGroup.O: 0.0,
        BloodGroup.A: 0.0,
        BloodGroup.B: 0.0,
        BloodGroup.AB: 1.0,
    }
    bgen_o = generation.BloodGroupGenerator(bg_dist_o)
    bg_dist_a = {
        BloodGroup.O: 0.0,
        BloodGroup.A: 0.0,
        BloodGroup.B: 1.0,
        BloodGroup.AB: 0.0,
    }
    bgen_a = generation.BloodGroupGenerator(bg_dist_a)
    bg_dist_b = {
        BloodGroup.O: 0.0,
        BloodGroup.A: 1.0,
        BloodGroup.B: 0.0,
        BloodGroup.AB: 0.0,
    }
    bgen_b = generation.BloodGroupGenerator(bg_dist_b)
    bg_dist_ab = {
        BloodGroup.O: 1.0,
        BloodGroup.A: 0.0,
        BloodGroup.B: 0.0,
        BloodGroup.AB: 0.0,
    }
    bgen_ab = generation.BloodGroupGenerator(bg_dist_ab)
    dgen = generation.DonorGenerator(
        bgen,
        recipient_o_generator=bgen_o,
        recipient_a_generator=bgen_a,
        recipient_b_generator=bgen_b,
        recipient_ab_generator=bgen_ab,
    )
    json = {
        "Generic": {"O": 0.25, "A": 0.25, "B": 0.25, "AB": 0.25},
        "O": {"O": 0.0, "A": 0.0, "B": 0.0, "AB": 1.0},
        "A": {"O": 0.0, "A": 0.0, "B": 1.0, "AB": 0.0},
        "B": {"O": 0.0, "A": 1.0, "B": 0.0, "AB": 0.0},
        "AB": {"O": 1.0, "A": 0.0, "B": 0.0, "AB": 0.0},
    }
    assert dgen.config() == json


def test_parse_bandString() -> None:
    in_string = "0.1 0\n0.1 0.01 0.1\n0.5 0.1 0.9\n0.3 0.9 1\n"
    bands = generation._parseBandString(in_string)
    assert len(bands) == 4
    assert bands[(0, 0)] == 0.1
    assert bands[(0.01, 0.1)] == 0.1
    assert bands[(0.1, 0.9)] == 0.5
    assert bands[(0.9, 1)] == 0.3
    in_string = "0.0434637245068539 0\n0.00635239050484788 0.01 0.1\n0.00267469073888332 0.1 0.2\n0.00601805416248746 0.2 0.3\n0.00835840855901037 0.3 0.4\n0.0106987629555333 0.4 0.5\n0.0217318622534269 0.5 0.6\n0.0290872617853561 0.6 0.7\n0.0391173520561685 0.7 0.8\n0.0257438983617519 0.8 0.85\n0.0307589434971581 0.85 0.9\n0.0113674356402541 0.9\n0.0106987629555333 0.91\n0.0157138080909395 0.92\n0.0317619525242394 0.93\n0.0190571715145436 0.94\n0.0197258441992645 0.95\n0.0240722166499498 0.96\n0.0534938147776663 0.97\n0.0929455031761953 0.98\n0.180207288532263 0.99\n0.316950852557673 1\n"
    bands = generation._parseBandString(in_string)
    assert len(bands) == 22


def test_float_band_gen() -> None:
    in_string = "0.25 0\n0.25 0.5\n0.25 0.9\n0.25 1\n"
    float_bands = generation.FloatGenerator(bandString=in_string)
    # With the forced seed, we test a bunch of draws until we see all 4 values.
    random.seed(SEED)
    assert float_bands.draw() == 0.5
    assert float_bands.draw() == 1.0
    assert float_bands.draw() == 0.5
    assert float_bands.draw() == 0.9
    assert float_bands.draw() == 0.0


def test_float_band_gen_from_json() -> None:
    json = [
        [[0, 0], 0.25],
        [[0.5, 0.5], 0.25],
        [[0.9, 0.9], 0.25],
        [[1.0, 1.0], 0.25],
    ]
    float_bands = generation.FloatGenerator.from_json(json)
    # With the forced seed, we test a bunch of draws until we see all 4 values.
    random.seed(SEED)
    assert float_bands.draw() == 0.5
    assert float_bands.draw() == 1.0
    assert float_bands.draw() == 0.5
    assert float_bands.draw() == 0.9
    assert float_bands.draw() == 0.0


def test_float_band_gen_from_json_single_value() -> None:
    json = [
        [0, 0.25],
        [0.5, 0.25],
        [0.9, 0.25],
        [1.0, 0.25],
    ]
    float_bands = generation.FloatGenerator.from_json(json)
    # With the forced seed, we test a bunch of draws until we see all 4 values.
    random.seed(SEED)
    assert float_bands.draw() == 0.5
    assert float_bands.draw() == 1.0
    assert float_bands.draw() == 0.5
    assert float_bands.draw() == 0.9
    assert float_bands.draw() == 0.0


def test_float_band_gen_config() -> None:
    in_string = "0.25 0\n0.25 0.5\n0.25 0.9\n0.25 1\n"
    float_bands = generation.FloatGenerator(bandString=in_string)
    json = [
        [[0, 0], 0.25],
        [[0.5, 0.5], 0.25],
        [[0.9, 0.9], 0.25],
        [[1.0, 1.0], 0.25],
    ]
    assert float_bands.config() == json


def test_float_band_gen_bad_dist() -> None:
    in_string = "0.1 0\n0.51 0.01 0.1\n0.5 0.1 0.9\n0.3 0.9 1\n"
    with pytest.raises(
        Exception,
        match=re.escape("FloatGenerator probabilities (1.41) do not sum to 1.0"),
    ):
        float_bands = generation.FloatGenerator(bandString=in_string)


def test_float_band_gen_bad_call() -> None:
    in_string = "0.1 0\n0.51 0.01 0.1\n0.5 0.1 0.9\n0.3 0.9 1\n"
    bands = generation._parseBandString(in_string)
    with pytest.raises(
        Exception,
        match="Exactly one of bandString or bands must be given to a FloatGenerator constructor",
    ):
        float_bands = generation.FloatGenerator(bands=bands, bandString=in_string)


def test_cpra_generator_wrong_calls() -> None:
    in_string = "0.25 0\n0.25 0.5\n0.25 0.9\n0.25 1\n"
    bands = generation.FloatGenerator(bandString=in_string)
    with pytest.raises(
        Exception,
        match="A cPRA generator needs at least one distribution of cPRA values to function.",
    ):
        cpra_gen = generation.CPRAGenerator()
    with pytest.raises(
        Exception,
        match="If generic is given, then neither of compatible_generator nor incompatible_generator can be given",
    ):
        cpra_gen = generation.CPRAGenerator(generic=bands, compatible_generator=bands)
    with pytest.raises(
        Exception,
        match="If generic is not given, then both of compatible_generator and incompatible_generator must be given",
    ):
        cpra_gen = generation.CPRAGenerator(compatible_generator=bands)
    with pytest.raises(
        Exception,
        match="If generic is not given, then both of compatible_generator and incompatible_generator must be given",
    ):
        cpra_gen = generation.CPRAGenerator(incompatible_generator=bands)
    cpra_gen = generation.CPRAGenerator(
        compatible_generator=bands, incompatible_generator=bands
    )
    with pytest.raises(
        Exception,
        match="Tried to draw cPRA without either specifying ABO compatible donor or giving generic distribution",
    ):
        cpra_gen.draw()


def test_cpra_generator_all_dist() -> None:
    in_string = "0.25 0\n0.25 0.5\n0.25 0.9\n0.25 1\n"
    bands = generation.FloatGenerator(bandString=in_string)
    cpra_gen = generation.CPRAGenerator(generic=bands)
    # We've already checked FloatGenerator objects, so just check that something is
    # returned
    random.seed(SEED)
    assert cpra_gen.draw() == 0.5


def test_cpra_generator_diff_dists() -> None:
    compat_string = "0.5 0.9\n0.5 1\n"
    incompat_string = "0.5 0.0\n0.5 0.1\n"
    compat_bands = generation.FloatGenerator(bandString=compat_string)
    incompat_bands = generation.FloatGenerator(bandString=incompat_string)
    cpra_gen = generation.CPRAGenerator(
        compatible_generator=compat_bands, incompatible_generator=incompat_bands
    )
    # We've already checked CPRABands objects, so just check that what is
    # returned comes from the right band
    for _ in range(500):
        assert cpra_gen.draw(True) in [0.9, 1.0]
        assert cpra_gen.draw(False) in [0.0, 0.1]


def test_compat_chance_generator_construct() -> None:
    compat_bands_low = generation.FloatGenerator(
        bands={(0.0, 0.1): 0.5, (0.1, 0.2): 0.5}
    )
    compat_bands_high = generation.FloatGenerator(
        bands={(0.5, 0.9): 0.5, (0.9, 1.0): 0.5}
    )
    compat_gen = generation.CompatibilityChanceGenerator(
        dists=[(0, 0.5, compat_bands_low), (0.5, 1.01, compat_bands_high)]
    )
    compat_gen = generation.CompatibilityChanceGenerator(
        dists=[(0, 1.01, lambda x: 1 - x)]
    )


def test_compat_chance_generator_bands() -> None:
    compat_bands_low = generation.FloatGenerator(
        bands={(0.0, 0.1): 0.5, (0.1, 0.2): 0.5}
    )
    compat_bands_high = generation.FloatGenerator(
        bands={(0.5, 0.9): 0.5, (0.9, 1.0): 0.5}
    )
    compat_gen = generation.CompatibilityChanceGenerator(
        dists=[(0, 0.5, compat_bands_low), (0.5, 1.01, compat_bands_high)]
    )
    for _ in range(500):
        c = compat_gen.draw(0.25)
        assert 0.0 <= c < 0.2
        c = compat_gen.draw(0.75)
        assert 0.5 <= c < 1.0


def test_compat_chance_generator_func() -> None:
    compat_gen = generation.CompatibilityChanceGenerator(
        dists=[(0, 1.01, lambda x: 1 - x)]
    )
    for pra in [0, 0.25, 0.50, 0.75, 1.0]:
        assert compat_gen.draw(pra) == 1 - pra


def test_compat_chance_generator_both() -> None:
    compat_bands_low = generation.FloatGenerator(
        bands={(0.0, 0.1): 0.5, (0.1, 0.2): 0.5}
    )
    compat_gen = generation.CompatibilityChanceGenerator(
        dists=[(0, 0.5, compat_bands_low), (0.5, 1.01, lambda x: 1 - x)]
    )
    for pra in [0, 0.1, 0.2, 0.3]:
        assert compat_gen.draw(pra) < 0.2
    for pra in [0.5, 0.75, 1.0]:
        assert compat_gen.draw(pra) == 1 - pra


def test_compat_chance_generator_both_from_json() -> None:
    json = [
        [0, 0.5, [[[0.0, 0.1], 0.5], [[0.1, 0.2], 0.5]]],
        [0.5, 1.01, {"function": {"type": "linear", "offset": 1, "coefficient": -1}}],
    ]
    compat_gen = generation.CompatibilityChanceGenerator.from_json(json)
    for pra in [0, 0.1, 0.2, 0.3]:
        assert compat_gen.draw(pra) < 0.2
    for pra in [0.5, 0.75, 1.0]:
        assert compat_gen.draw(pra) == 1 - pra


def test_recip_generator() -> None:
    bg_dist = {
        BloodGroup.O: 0.45,
        BloodGroup.A: 0.25,
        BloodGroup.B: 0.10,
        BloodGroup.AB: 0.20,
    }
    bgen = generation.BloodGroupGenerator(bg_dist)
    dc_dist = {1: 0.67, 2: 0.22, 3: 0.10, 4: 0.01}
    dcgen = generation.DonorCountGenerator(dc_dist)
    donor_bg_dist = {
        BloodGroup.O: 0.10,
        BloodGroup.A: 0.20,
        BloodGroup.B: 0.15,
        BloodGroup.AB: 0.55,
    }
    donor_bgen = generation.BloodGroupGenerator(bg_dist)
    dgen = generation.DonorGenerator(donor_bgen)
    cpra_string = "0.25 0\n0.25 0.5\n0.25 0.9\n0.25 1\n"
    bands = generation.FloatGenerator(
        bands={(0, 0.1): 0.25, (0.1, 0.9): 0.05, (0.9, 1.0): 0.7}
    )
    cpra_gen = generation.CPRAGenerator(generic=bands)
    compat_gen = generation.CompatibilityChanceGenerator(
        dists=[(0, 1.01, lambda x: 1 - x)]
    )
    recip_gen = generation.RecipientGenerator(bgen, dcgen, dgen, cpra_gen, compat_gen)
    random.seed(SEED)
    r = recip_gen.draw("1")
    assert r.id == "1"
    assert len(r.donors()) == 1
    assert r.donors()[0].id == "1_D1"
    assert r.donors()[0].recipient == r
    r = recip_gen.draw("2")
    assert r.id == "2"
    assert len(r.donors()) == 1
    r = recip_gen.draw("3")
    assert r.id == "3"
    assert len(r.donors()) == 1
    r = recip_gen.draw("R4")
    assert r.id == "R4"
    assert len(r.donors()) == 3
    assert r.donors()[0].id == "R4_D1"


def test_instance_generator() -> None:
    bg_dist = {
        BloodGroup.O: 0.45,
        BloodGroup.A: 0.25,
        BloodGroup.B: 0.10,
        BloodGroup.AB: 0.20,
    }
    bgen = generation.BloodGroupGenerator(bg_dist)
    dc_dist = {1: 0.67, 2: 0.22, 3: 0.10, 4: 0.01}
    dcgen = generation.DonorCountGenerator(dc_dist)
    donor_bg_dist = {
        BloodGroup.O: 0.10,
        BloodGroup.A: 0.20,
        BloodGroup.B: 0.15,
        BloodGroup.AB: 0.55,
    }
    donor_bgen = generation.BloodGroupGenerator(bg_dist)
    dgen = generation.DonorGenerator(donor_bgen)
    cpra_string = "0.25 0\n0.25 0.5\n0.25 0.9\n0.25 1\n"
    bands = generation.FloatGenerator(
        bands={(0, 0.1): 0.25, (0.1, 0.9): 0.05, (0.9, 1.0): 0.7}
    )
    cpra_gen = generation.CPRAGenerator(generic=bands)
    compat_gen = generation.CompatibilityChanceGenerator(
        dists=[(0, 1.01, lambda x: 1 - x)]
    )
    recip_gen = generation.RecipientGenerator(bgen, dcgen, dgen, cpra_gen, compat_gen)
    ndd_bg_dist = {
        BloodGroup.O: 0.10,
        BloodGroup.A: 0.20,
        BloodGroup.B: 0.15,
        BloodGroup.AB: 0.55,
    }
    ndd_bgen = generation.BloodGroupGenerator(ndd_bg_dist)
    instance_gen = generation.InstanceGenerator(recip_gen, ndd_bgen)

    random.seed(SEED)
    i: Instance = instance_gen.draw(7)
    assert len(i.recipients) == 7
    ndds = [d for d in i.allDonors() if d.NDD]
    assert len(ndds) == 0
    assert len(i.transplants) == 7
    for t in i.transplants:
        assert t.donor.bloodGroupCompatible(t.recipient)

    i = instance_gen.draw(5, 5)
    assert len(i.recipients) == 5
    ndds = [d for d in i.allDonors() if d.NDD]
    assert len(ndds) == 5
    for t in i.transplants:
        assert t.donor.bloodGroupCompatible(t.recipient)
    assert len(i.transplants) == 13

    i = instance_gen.draw(50, 5)
    assert len(i.recipients) == 50
    ndds = [d for d in i.allDonors() if d.NDD]
    assert len(ndds) == 5
    for t in i.transplants:
        assert t.donor.bloodGroupCompatible(t.recipient)
    assert len(i.transplants) == 920

    i = instance_gen.draw(
        50,
        5,
        recipient_id_function=lambda num: f"RR_{num}",
        donor_id_function=lambda r: f"R={r.id}_donor={len(r.donors())}",
        ndd_id_function=lambda num: f"NDD_number_{num}",
    )
    assert len(i.recipients) == 50
    recip = i.recipient("RR_1")
    assert recip.id == "RR_1"
    print(recip.donors())
    d = recip.donors()[0]
    assert d.id == "R=RR_1_donor=0"
    recip = i.recipient("RR_2")
    assert recip.id == "RR_2"
    d = recip.donors()[1]
    assert d.id == "R=RR_2_donor=1"
    ndds = [d for d in i.allDonors() if d.NDD]
    assert ndds[0].id == "NDD_number_0"


def test_published_generators() -> None:
    gen = published_gens.uk_nhs_generator2022(compatibility_rule="Band-PRA0")
    num_recips = 2500
    i = gen.draw(numRecipients=num_recips)
    assert len(i.recipients) == num_recips
    bg_count: dict[BloodGroup, int] = defaultdict(int)
    donor_bg_count: dict[BloodGroup, dict[BloodGroup, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for r in i.allRecipients():
        bg_count[r.bloodGroup] += 1
        for d in r.donors():
            donor_bg_count[r.bloodGroup][d.bloodGroup] += 1
    for recip_bg in BloodGroup.all():
        print(
            f"{recip_bg}:\t{bg_count[recip_bg]} ({bg_count[recip_bg] / sum(bg_count.values()):.2f})"
        )
        for donor_bg in BloodGroup.all():
            print(
                f"dbg: {donor_bg}\t{donor_bg_count[recip_bg][donor_bg]} / {sum(donor_bg_count[recip_bg].values())} ({donor_bg_count[recip_bg][donor_bg]/bg_count[recip_bg]:.2f})"
            )
    margin = 0.15
    delta = 7

    assertEqualWithMargin(bg_count[BloodGroup.O], num_recips * 0.6293, margin, delta)
    assertEqualWithMargin(bg_count[BloodGroup.A], num_recips * 0.2325, margin, delta)
    assertEqualWithMargin(bg_count[BloodGroup.B], num_recips * 0.1119, margin, delta)
    assertEqualWithMargin(bg_count[BloodGroup.AB], num_recips * 0.0263, margin, delta)

    count = sum(donor_bg_count[BloodGroup.O].values())
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.O][BloodGroup.O], count * 0.3721, margin, delta
    )
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.O][BloodGroup.A], count * 0.4899, margin, delta
    )
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.O][BloodGroup.B], count * 0.1219, margin, delta
    )
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.O][BloodGroup.AB], count * 0.0161, margin, delta
    )

    count = sum(donor_bg_count[BloodGroup.A].values())
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.A][BloodGroup.O], count * 0.2783, margin, delta
    )
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.A][BloodGroup.A], count * 0.6039, margin, delta
    )
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.A][BloodGroup.B], count * 0.0907, margin, delta
    )
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.A][BloodGroup.AB], count * 0.0270, margin, delta
    )

    count = sum(donor_bg_count[BloodGroup.B].values())
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.B][BloodGroup.O], count * 0.2910, margin, delta
    )
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.B][BloodGroup.A], count * 0.2719, margin, delta
    )
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.B][BloodGroup.B], count * 0.3689, margin, delta
    )
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.B][BloodGroup.AB], count * 0.0683, margin, delta
    )

    count = sum(donor_bg_count[BloodGroup.AB].values())
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.AB][BloodGroup.O], count * 0.3166, margin, delta
    )
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.AB][BloodGroup.A], count * 0.4271, margin, delta
    )
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.AB][BloodGroup.B], count * 0.1910, margin, delta
    )
    assertEqualWithMargin(
        donor_bg_count[BloodGroup.AB][BloodGroup.AB], count * 0.0653, margin, delta
    )

    gen = published_gens.uk_nhs_generator2022(compatibility_rule="Band")
    i = gen.draw(numRecipients=100)
    assert len(i.recipients) == 100
    gen = published_gens.uk_nhs_generator2022(compatibility_rule="Tweak-PRA0")
    i = gen.draw(numRecipients=100)
    assert len(i.recipients) == 100
    gen = published_gens.uk_nhs_generator2022(compatibility_rule="Tweak")
    i = gen.draw(numRecipients=100)
    assert len(i.recipients) == 100
    gen = published_gens.uk_nhs_generator2022(compatibility_rule="Calc")
    i = gen.draw(numRecipients=100)
    assert len(i.recipients) == 100
