"""Testing various statistical calculations."""

from kep_solver.entities import InstanceSet, Instance
from kep_solver.fileio import read_json

# Test the way we calculate compatibility chance.


def test_compat_chance_calculation_one() -> None:
    # These instances are not realistic, so don't read anything into the
    # distribution of compatibility chance.
    expected = {
        "1": 0.5,
        "4": 1.0,
        "42": 0.5,
        "53": 1.0,
        "5": 1.0,
        "6": 0.0,
        "10": 1.0,
        "17": 1.0,
        "18": 10 / 21,
        "23": 1.0,
        "25": 1.0,
        "28": 5 / 52,
        "35": 13 / 53,
        "36": 1.0,
        "41": 9 / 21,
        "56": 1.0,
        "63": 1.0,
        "64": 1.0,
        "7": 0.0,
        "30": 26 / 53,
        "8": 2 / 26,
        "45": 3 / 20,
        "11": 0.0,
        "12": 3 / 62,
        "50": 2 / 21,
        "13": 0.0,
        "14": 0.0,
        "15": 1 / 52,
        "16": 1 / 52,
        "62": 5 / 53,
        "20": 0.0,
        "21": 2 / 51,
        "27": 0.0,
        "40": 3 / 52,
        "29": 0.0,
        "32": 0.0,
        "33": 0.0,
        "34": 0.0,
        "59": 2 / 52,
        "43": 0.0,
        "46": 0.0,
        "47": 0.0,
        "54": 1 / 52,
        "49": 0.0,
        "52": 0.0,
        "55": 0.0,
        "57": 2 / 52,
        "58": 0.0,
        "61": 0.0,
        "68": 0.0,
        "69": 0.0,
    }
    filenames = ["medium-1.json"]
    instances = [
        read_json("tests/test_instances/" + filename) for filename in filenames
    ]
    instanceset = InstanceSet(instances)
    instanceset._calculate_compatibilities()
    for instance in instanceset:
        for recipient in instance.allRecipients():
            assert recipient.compatibilityChance == expected[recipient.id]


def test_compat_chance_calculation_many() -> None:
    # These instances are not realistic, so don't read anything into the
    # distribution of compatibility chance.
    expected = {
        "1": 55 / 95,
        "4": 22 / 58,
        "42": 40 / 88,
        "53": 66 / 89,
        "5": 53 / 87,
        "6": 62 / 92,
        "10": 72 / 95,
        "17": 46 / 66,
        "18": 43 / 89,
        "23": 49 / 90,
        "25": 50 / 92,
        "28": 26 / 92,
        "35": 74 / 92,
        "36": 46 / 86,
        "41": 42 / 88,
        "56": 23 / 90,
        "63": 55 / 79,
        "64": 45 / 88,
        "7": 5 / 78,
        "30": 41 / 90,
        "8": 55 / 90,
        "45": 23 / 84,
        "11": 53 / 88,
        "12": 35 / 86,
        "50": 15 / 88,
        "13": 47 / 82,
        "14": 16 / 86,
        "15": 50 / 91,
        "16": 52 / 95,
        "62": 5 / 74,
        "20": 63 / 88,
        "21": 30 / 89,
        "27": 11 / 85,
        "40": 5 / 86,
        "29": 75 / 89,
        "32": 2 / 88,
        "33": 0.0,
        "34": 19 / 79,
        "59": 25 / 91,
        "43": 56 / 86,
        "46": 28 / 85,
        "47": 7 / 94,
        "54": 36 / 94,
        "49": 89 / 96,
        "52": 68 / 93,
        "55": 21 / 78,
        "57": 40 / 90,
        "58": 48 / 86,
        "61": 21 / 70,
        "68": 66 / 83,
        "69": 2 / 83,
        "24": 25 / 84,
        "37": 65 / 83,
        "38": 35 / 89,
        "48": 29 / 92,
        "66": 45 / 80,
        "71": 35 / 78,
        "74": 29 / 71,
        "31": 43 / 94,
        "9": 42 / 90,
        "77": 2 / 19,
        "67": 7 / 93,
        "44": 30 / 89,
        "19": 64 / 91,
        "73": 15 / 67,
        "26": 21 / 85,
        "70": 15 / 88,
        "39": 17 / 94,
        "0": 8 / 86,
        "51": 35 / 84,
        "22": 36 / 84,
        "65": 25 / 92,
        "75": 17 / 35,
        "60": 34 / 84,
        "2": 47 / 85,
        "3": 1 / 93,
        "79": 0.0,
    }
    filenames = [f"medium-{i}.json" for i in range(1, 11)]
    instances = [
        read_json("tests/test_instances/" + filename) for filename in filenames
    ]
    instanceset = InstanceSet(instances)
    instanceset._calculate_compatibilities()
    for instance in instanceset:
        for recipient in instance.allRecipients():
            assert recipient.compatibilityChance == expected[recipient.id]
