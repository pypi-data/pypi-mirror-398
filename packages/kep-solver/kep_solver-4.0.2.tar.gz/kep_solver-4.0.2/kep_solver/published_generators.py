"""A collection of published data generators."""

from kep_solver.entities import BloodGroup
from kep_solver.generation import (
    BloodGroupGenerator,
    DonorCountGenerator,
    DonorGenerator,
    RecipientGenerator,
    InstanceGenerator,
    CPRAGenerator,
    FloatGenerator,
    CompatibilityChanceGenerator,
)


def make_compat_gen(compat: str) -> CompatibilityChanceGenerator:
    prazero = FloatGenerator(
        bands={
            (0.00, 0.00): 0.1890660592255102,
            (0.00, 0.01): 0.0683371298405470,
            (0.01, 0.02): 0.0774487471526198,
            (0.02, 0.03): 0.0387243735763102,
            (0.03, 0.04): 0.0205011389521642,
            (0.04, 0.10): 0.0546697038724377,
            (0.10, 0.25): 0.0592255125284742,
            (0.25, 0.50): 0.0911161731207292,
            (0.50, 0.75): 0.1412300683371303,
            (0.75, 1.01): 0.2596810933940773,
        }
    )

    match compat:
        case "Band-PRA0":
            return CompatibilityChanceGenerator(
                dists=[
                    (0, 0.01, prazero),
                    (0.01, 0.50, lambda cpra: -0.33012 * cpra + 0.5651),
                    (0.50, 0.95, lambda cpra: -0.64194 * cpra + 0.6578),
                    (0.95, 0.96, lambda cpra: 0.058),
                    (0.96, 0.97, lambda cpra: 0.053),
                    (0.97, 0.98, lambda cpra: 0.025),
                    (0.98, 0.99, lambda cpra: 0.015),
                    (0.99, 1.00, lambda cpra: 0.015),
                    (1.00, 1.01, lambda cpra: 0.012),
                ]
            )
        case "Band":
            return CompatibilityChanceGenerator(
                dists=[
                    (0.00, 0.50, lambda cpra: -0.33012 * cpra + 0.5651),
                    (0.50, 0.95, lambda cpra: -0.64194 * cpra + 0.6578),
                    (0.95, 0.96, lambda cpra: 0.058),
                    (0.96, 0.97, lambda cpra: 0.053),
                    (0.97, 0.98, lambda cpra: 0.025),
                    (0.98, 0.99, lambda cpra: 0.015),
                    (0.99, 1.00, lambda cpra: 0.015),
                    (1.00, 1.01, lambda cpra: 0.012),
                ]
            )
        case "Tweak-PRA0":
            return CompatibilityChanceGenerator(
                dists=[
                    (0, 0.01, prazero),
                    (0.01, 1.01, lambda cpra: -0.55 * cpra + 0.55),
                ]
            )
        case "Tweak":
            return CompatibilityChanceGenerator(
                dists=[
                    (0.00, 1.01, lambda cpra: -0.55 * cpra + 0.55),
                ]
            )
        case "Calc":
            return CompatibilityChanceGenerator(
                dists=[
                    (0.00, 1.01, lambda cpra: -0.55 * cpra + 0.58),
                ]
            )
    raise Exception(f"Unknown compatibility rule: {compat}")


def uk_nhs_generator2022(
    compatibility_rule: str = "Band-PRA0",
) -> InstanceGenerator:
    """Create an InstanceGenerator using parameters published in M. Delorme, S.
    García, J. Gondzio, J. Kalcsics, D. Manlove, W. Pettersson, J. Trimble
    Improved instance generation for kidney exchange programmes; Computers &
    Operations Research 2022; doi: 10.1016/j.cor.2022.105707.

    :param compatibility_rule: One of "Band-PRA0", "Band", "Tweak-PRA0",
        "Tweak", or "Calc", as defined in the above paper.
    :return: An instance generator using the published parameters.
    """
    recip_bg_dist = {
        BloodGroup.O: 0.6293,
        BloodGroup.A: 0.2325,
        BloodGroup.B: 0.1119,
        BloodGroup.AB: 0.0263,
    }
    bgen = BloodGroupGenerator(recip_bg_dist)
    ndd_bg_dist = {
        BloodGroup.O: 0.493,
        BloodGroup.A: 0.399,
        BloodGroup.B: 0.0939,
        BloodGroup.AB: 0.0141,
    }
    ndd_bgen = BloodGroupGenerator(ndd_bg_dist)
    dc_dist = {1: 0.9112, 2: 0.0769, 3: 0.0105, 4: 0.0014}
    dcgen = DonorCountGenerator(dc_dist)
    recip_o_bgen = BloodGroupGenerator(
        {
            BloodGroup.O: 0.3721,
            BloodGroup.A: 0.4899,
            BloodGroup.B: 0.1219,
            BloodGroup.AB: 0.0161,
        }
    )
    recip_a_bgen = BloodGroupGenerator(
        {
            BloodGroup.O: 0.2783,
            BloodGroup.A: 0.6039,
            BloodGroup.B: 0.0907,
            BloodGroup.AB: 0.0271,
        }
    )
    recip_b_bgen = BloodGroupGenerator(
        {
            BloodGroup.O: 0.2910,
            BloodGroup.A: 0.2719,
            BloodGroup.B: 0.3689,
            BloodGroup.AB: 0.0682,
        }
    )
    recip_ab_bgen = BloodGroupGenerator(
        {
            BloodGroup.O: 0.3166,
            BloodGroup.A: 0.4271,
            BloodGroup.B: 0.1910,
            BloodGroup.AB: 0.0653,
        }
    )
    dgen = DonorGenerator(
        ndd_bgen,
        recipient_o_generator=recip_o_bgen,
        recipient_a_generator=recip_a_bgen,
        recipient_b_generator=recip_b_bgen,
        recipient_ab_generator=recip_ab_bgen,
    )
    compatible_bands = FloatGenerator(
        bands={
            (0, 0): 0.0434637245068539,
            (0.01, 0.1): 0.0063523905048479,
            (0.1, 0.2): 0.0026746907388833,
            (0.2, 0.3): 0.0060180541624875,
            (0.3, 0.4): 0.0083584085590104,
            (0.4, 0.5): 0.0106987629555333,
            (0.5, 0.6): 0.0217318622534269,
            (0.6, 0.7): 0.0290872617853561,
            (0.7, 0.8): 0.0391173520561685,
            (0.8, 0.85): 0.0257438983617519,
            (0.85, 0.9): 0.0307589434971581,
            (0.9, 0.9): 0.0113674356402541,
            (0.91, 0.91): 0.0106987629555333,
            (0.92, 0.92): 0.0157138080909395,
            (0.93, 0.93): 0.0317619525242394,
            (0.94, 0.94): 0.0190571715145436,
            (0.95, 0.95): 0.0197258441992645,
            (0.96, 0.96): 0.0240722166499498,
            (0.97, 0.97): 0.0534938147776663,
            (0.98, 0.98): 0.0929455031761953,
            (0.99, 0.99): 0.1802072885322634,
            (1, 1): 0.316950852557673,
        }
    )
    incompatible_bands = FloatGenerator(
        bands={
            (0, 0): 0.356760886172651,
            (0.01, 0.1): 0.038961038961039,
            (0.1, 0.2): 0.0133689839572193,
            (0.2, 0.3): 0.0106951871657754,
            (0.3, 0.4): 0.0210084033613445,
            (0.4, 0.5): 0.0244461420932009,
            (0.5, 0.6): 0.0336134453781513,
            (0.6, 0.7): 0.0305576776165011,
            (0.7, 0.8): 0.0427807486631016,
            (0.8, 0.85): 0.0355233002291826,
            (0.85, 0.9): 0.0458365164247517,
            (0.9, 0.9): 0.0064935064935064,
            (0.91, 0.91): 0.0126050420168067,
            (0.92, 0.92): 0.0286478227654698,
            (0.93, 0.93): 0.0064935064935064,
            (0.94, 0.94): 0.0076394194041252,
            (0.95, 0.95): 0.0156608097784568,
            (0.96, 0.96): 0.0236822001527884,
            (0.97, 0.97): 0.0152788388082506,
            (0.98, 0.98): 0.0252100840336134,
            (0.99, 0.99): 0.0966386554621849,
            (1, 1): 0.108097784568373,
        }
    )
    cpra_gen = CPRAGenerator(
        compatible_generator=compatible_bands, incompatible_generator=incompatible_bands
    )
    compat_gen = make_compat_gen(compatibility_rule)
    recip_gen = RecipientGenerator(bgen, dcgen, dgen, cpra_gen, compat_gen)
    instance_gen = InstanceGenerator(recip_gen, ndd_bgen)
    return instance_gen
