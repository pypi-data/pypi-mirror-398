import pytest

import xmldiff.main as xmldiff  # type: ignore
import unicodedata  # Needed for xmldiff
import json
from ruamel.yaml import YAML

import random
import numpy as np

# Seed for RNG for reproducible tests
SEED = 12345


from unittest.mock import mock_open, patch

import kep_solver.fileio as fileio
from kep_solver.entities import BloodGroup, DynamicInstance
from kep_solver.generation import DynamicGenerator


@pytest.fixture(
    params=[
        ("JSON", fileio.read_file("tests/test_instances/test1.json")),
        ("XML", fileio.read_xml("tests/test_instances/test1.xml")),
        ("YAML", fileio.read_file("tests/test_instances/test1.yaml")),
    ]
)
def test_one(request):
    yield request.param


def test_instance_one(test_one) -> None:
    instance = test_one[1]
    assert len(instance.donors) == 4
    assert len(instance.transplants) == 5
    firstDonor = instance.donor("1")
    assert firstDonor.age == 50
    assert firstDonor.recipient.id == "1"
    assert firstDonor.bloodGroup == BloodGroup.O
    assert len(firstDonor.transplants()) == 1
    assert instance.recipient("1").pairedWith(firstDonor)
    assert not instance.recipient("2").pairedWith(firstDonor)
    transplant = firstDonor.transplants()[0]
    assert transplant.donor.id == "1"
    assert transplant.recipient.id == "2"
    assert transplant.weight == 1
    secondDonor = instance.donor("2")
    assert secondDonor.age == 50
    assert secondDonor.recipient.id == "2"
    assert secondDonor.bloodGroup == BloodGroup.A
    assert len(secondDonor.transplants()) == 2
    thirdDonor = instance.donor("3")
    assert thirdDonor.age == 60
    assert thirdDonor.recipient.id == "3"
    assert thirdDonor.bloodGroup == BloodGroup.AB
    assert len(thirdDonor.transplants()) == 1
    # Only JSON and YAML can store patient information
    if test_one[0] in ["JSON", "YAML"]:
        assert firstDonor.recipient.bloodGroup == BloodGroup.O
        assert firstDonor.recipient.cPRA == 0.25
        assert secondDonor.recipient.bloodGroup == BloodGroup.B
        assert secondDonor.recipient.cPRA == 0
        assert thirdDonor.recipient.bloodGroup == BloodGroup.O
        assert thirdDonor.recipient.cPRA == 0.98
        fourthDonor = instance.donor("4")
        assert fourthDonor.recipient.bloodGroup == BloodGroup.AB
        assert fourthDonor.recipient.cPRA == 0.10
        assert instance.recipient("1").hasBloodCompatibleDonor()
        assert not instance.recipient("3").hasBloodCompatibleDonor()


def test_one_write_json(test_one) -> None:
    # We only test against JSON in this function
    if test_one[0] != "JSON":
        return
    instance = test_one[1]
    filename = "test-output.json"
    with open("tests/test_instances/test1.json", "r") as infile:
        real_instance_json = json.load(infile)
        with patch("builtins.open", mock_open()) as mo:
            instance.writeFileJson(filename, write_recipients=True, compressed=False)
            mo.assert_called_once_with(filename, "w")
            handle = mo()
            written = " ".join(call.args[0] for call in handle.write.call_args_list)
            written_json = json.loads(written)
            assert written_json == real_instance_json


def test_one_write_json_v2(test_one) -> None:
    # We only test against JSON in this function
    if test_one[0] != "JSON":
        return
    instance = test_one[1]
    filename = "test-output.json"
    with open("tests/test_instances/test1.v2.json", "r") as infile:
        real_instance_json = json.load(infile)
        with patch("builtins.open", mock_open()) as mo:
            instance.writeFileJsonv2(filename, compressed=False)
            mo.assert_called_once_with(filename, "w")
            handle = mo()
            written = " ".join(call.args[0] for call in handle.write.call_args_list)
            written_json = json.loads(written)
            assert written_json == real_instance_json


def test_one_read_json_v2() -> None:
    instance = fileio.read_file("tests/test_instances/test1.v2.json")


def test_one_write_yaml(test_one) -> None:
    # We only test against yaml in this function
    if test_one[0] != "YAML":
        return
    instance = test_one[1]
    filename = "test-output.json"
    with open("tests/test_instances/test1.yaml", "r") as infile:
        yaml = YAML()
        real_yaml = yaml.load(infile)
        with patch("builtins.open", mock_open()) as mo:
            instance.writeFileYaml(filename, compressed=False)
            mo.assert_called_once_with(filename, "w")
            handle = mo()
            written = "".join(call.args[0] for call in handle.write.call_args_list)
            written_yaml = yaml.load(written)
            assert written_yaml == real_yaml


def test_one_write_xml(test_one) -> None:
    if test_one[0] != "XML":
        return
    instance = test_one[1]
    filename = "test-output.xml"
    with open("tests/test_instances/test1.xml", "r") as real_instance:
        real_xml = real_instance.read()
    with patch("builtins.open", mock_open()) as mo:
        instance.writeFileXml(filename, compressed=False)
        mo.assert_called_once_with(filename, "w")
        handle = mo()
        written = "".join(str(call.args[0]) for call in handle.write.call_args_list)
        diff = xmldiff.diff_texts(
            unicodedata.normalize("NFKD", real_xml).encode("ascii", "ignore"),
            unicodedata.normalize("NFKD", written).encode("ascii", "ignore"),
        )
        assert not diff


# A bit less stringent checking on these instances


@pytest.fixture(
    params=[
        ("JSON", fileio.read_file("tests/test_instances/test2.json")),
        ("XML", fileio.read_xml("tests/test_instances/test2.xml")),
        ("YAML", fileio.read_file("tests/test_instances/test2.yaml")),
    ]
)
def test_two(request):
    yield request.param


def test_instance_two(test_two) -> None:
    instance = test_two[1]
    assert len(instance.donors) == 6
    assert len(instance.transplants) == 10
    assert len(instance.donor("5").transplants()) == 2


def test_two_write(test_two) -> None:
    # We can only write JSON, so no point testing for the XML input
    if test_two[0] != "JSON":
        return
    instance = test_two[1]
    filename = "test-output.json"
    with open("tests/test_instances/test2.json", "r") as infile:
        real_instance_json = json.load(infile)
        with patch("builtins.open", mock_open()) as mo:
            # No bloodgroup info, so don't write recipients
            instance.writeFileJson(filename, write_recipients=False, compressed=False)
            mo.assert_called_once_with(filename, "w")
            handle = mo()
            written = " ".join(call.args[0] for call in handle.write.call_args_list)
            written_json = json.loads(written)
            assert written_json == real_instance_json


@pytest.fixture(
    params=[
        ("JSON", fileio.read_file("tests/test_instances/test3.json")),
        ("JSON.xz", fileio.read_file("tests/test_instances/test3.json.xz")),
        ("XML", fileio.read_file("tests/test_instances/test3.xml")),
        ("YAML", fileio.read_file("tests/test_instances/test3.yaml")),
    ]
)
def test_three(request):
    yield request.param


def test_instance_three(test_three) -> None:
    instance = test_three[1]
    assert len(instance.donors) == 3
    assert len(instance.transplants) == 4
    assert len(instance.donor("1").transplants()) == 2


@pytest.fixture(
    params=[
        ("JSON", fileio.read_file("tests/test_instances/test3b.json")),
        ("XML", fileio.read_xml("tests/test_instances/test3b.xml")),
        ("YAML", fileio.read_file("tests/test_instances/test3b.yaml")),
    ]
)
def test_threeb(request):
    yield request.param


def test_instance_threeb(test_threeb) -> None:
    instance = test_threeb[1]
    assert len(instance.donors) == 4
    assert len(instance.transplants) == 9
    assert len(instance.donor("1").transplants()) == 3


@pytest.fixture(
    params=[
        ("JSON", fileio.read_file("tests/test_instances/test4.json")),
        ("XML", fileio.read_xml("tests/test_instances/test4.xml")),
        ("YAML", fileio.read_file("tests/test_instances/test4.yaml")),
    ]
)
def test_four(request):
    yield request.param


def test_instance_four(test_four) -> None:
    instance = test_four[1]
    assert len(instance.donors) == 4
    assert len(instance.transplants) == 6
    assert len(instance.donor("4").transplants()) == 2
    assert instance.transplants[0].weight == 4


@pytest.fixture(
    params=[
        ("JSON", fileio.read_file("tests/test_instances/test5.json")),
        ("XML", fileio.read_xml("tests/test_instances/test5.xml")),
        ("YAML", fileio.read_file("tests/test_instances/test5.yaml")),
    ]
)
def test_five(request):
    yield request.param


def test_instance_five(test_five) -> None:
    instance = test_five[1]
    assert len(instance.donors) == 4
    assert len(instance.transplants) == 4
    ndd = instance.donor("1")
    assert ndd.NDD
    with pytest.raises(Exception):
        ndd.recipient()
    directed = instance.donor("2")
    assert not directed.NDD
    recip = directed.recipient
    assert not recip.pairedWith(ndd)
    assert recip.pairedWith(directed)
    assert recip.id == "2"


@pytest.fixture(
    params=[
        ("JSON", fileio.read_file("tests/test_instances/test7.json")),
        ("YAML", fileio.read_file("tests/test_instances/test7.yaml")),
    ]
)
def test_seven(request):
    yield request.param


def test_seven_write(test_seven) -> None:
    instance = test_seven[1]
    filename = "test-output.json"
    with open("tests/test_instances/test7.json", "r") as infile:
        real_instance_json = json.load(infile)
        with patch("builtins.open", mock_open()) as mo:
            # No bloodgroup info, so don't write recipients
            instance.writeFileJson(filename, write_recipients=False, compressed=False)
            mo.assert_called_once_with(filename, "w")
            handle = mo()
            written = " ".join(call.args[0] for call in handle.write.call_args_list)
            written_json = json.loads(written)
            assert written_json == real_instance_json


def test_medium_reads_compressed() -> None:
    normal = fileio.read_file("tests/test_instances/medium-5.json")
    compressed = fileio.read_file("tests/test_instances/medium-5.json.xz")
    assert len(normal.donors) == len(compressed.donors)
    assert len(normal.transplants) == len(compressed.transplants)
    assert len(normal.donor("5").transplants()) == len(
        compressed.donor("5").transplants()
    )


def test_large_reads_compressed() -> None:
    normal = fileio.read_file("tests/test_instances/large-6.json")
    compressed = fileio.read_file("tests/test_instances/large-6.json.xz")
    assert len(normal.donors) == len(compressed.donors)
    assert len(normal.transplants) == len(compressed.transplants)
    assert len(normal.donor("5").transplants()) == len(
        compressed.donor("5").transplants()
    )


def test_dyn_write_one() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    gen = DynamicGenerator(
        recipient_arrival_function=lambda x: [100] * 25,
        recipient_attrition_function=lambda r: 0,
        recipient_temporary_departure_function=lambda r, l: 0,
        recipient_positive_crossmatch_function=lambda r, d: False,
        ndd_arrival_function=lambda x: [0] * 25,
        ndd_attrition_function=lambda d: 0,
        ndd_temporary_departure_function=lambda d, l: 0,
    )
    instance = fileio.read_file("tests/test_instances/test3.json")
    dyn_instance = gen.generate(instance=instance, periods=25)
    filename = "dummy.json"
    with patch("builtins.open", mock_open()) as mo:
        # No bloodgroup info, so don't write recipients
        dyn_instance.writeFileJson(filename, write_recipients=True, compressed=False)
        mo.assert_called_once_with(filename, "w")
        handle = mo()
        written = " ".join(call.args[0] for call in handle.write.call_args_list)
        written_json = json.loads(written)
        assert written_json["recipients"]["1"]["arrival"] == 0
        assert written_json["recipients"]["1"]["departure"] == 26
        assert written_json["recipients"]["1"]["temporary_departures"] == []
        assert written_json["recipients"]["2"]["arrival"] == 0
        assert written_json["recipients"]["2"]["departure"] == 26
        assert written_json["recipients"]["2"]["temporary_departures"] == []
        assert written_json["recipients"]["3"]["arrival"] == 0
        assert written_json["recipients"]["3"]["departure"] == 26
        assert written_json["recipients"]["3"]["temporary_departures"] == []


def test_dyn_write_temporary_departures() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    gen = DynamicGenerator(
        recipient_arrival_function=lambda x: [100] * 25,
        recipient_attrition_function=lambda r: 0,
        recipient_temporary_departure_function=lambda r, l: r.id == "2" and 1 or 0,
        recipient_positive_crossmatch_function=lambda r, d: False,
        ndd_arrival_function=lambda x: [0] * 25,
        ndd_attrition_function=lambda d: 0,
        ndd_temporary_departure_function=lambda d, l: 0,
    )
    instance = fileio.read_file("tests/test_instances/test3.json")
    dyn_instance = gen.generate(instance=instance, periods=25)
    filename = "dummy.json"
    with patch("builtins.open", mock_open()) as mo:
        # No bloodgroup info, so don't write recipients
        dyn_instance.writeFileJson(filename, write_recipients=True, compressed=False)
        mo.assert_called_once_with(filename, "w")
        handle = mo()
        written = " ".join(call.args[0] for call in handle.write.call_args_list)
        written_json = json.loads(written)
        assert written_json["recipients"]["1"]["arrival"] == 0
        assert written_json["recipients"]["1"]["departure"] == 26
        assert written_json["recipients"]["1"]["temporary_departures"] == []
        assert written_json["recipients"]["2"]["arrival"] == 0
        assert written_json["recipients"]["2"]["departure"] == 26
        assert written_json["recipients"]["2"]["temporary_departures"] == [
            p for p in range(1, 25)
        ]
        assert written_json["recipients"]["3"]["arrival"] == 0
        assert written_json["recipients"]["3"]["departure"] == 26
        assert written_json["recipients"]["3"]["temporary_departures"] == []


def test_dyn_write_different() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    gen = DynamicGenerator(
        recipient_arrival_function=lambda x: [1] * 25,
        recipient_attrition_function=lambda r: 0.05,
        recipient_temporary_departure_function=lambda r, l: 0,
        recipient_positive_crossmatch_function=lambda r, d: False,
        ndd_arrival_function=lambda x: [0] * 25,
        ndd_attrition_function=lambda d: 0,
        ndd_temporary_departure_function=lambda d, l: 0,
    )
    instance = fileio.read_file("tests/test_instances/test3.json")
    dyn_instance = gen.generate(instance=instance, periods=25)
    filename = "dummy.json"
    with patch("builtins.open", mock_open()) as mo:
        # No bloodgroup info, so don't write recipients
        dyn_instance.writeFileJson(filename, write_recipients=True, compressed=False)
        mo.assert_called_once_with(filename, "w")
        handle = mo()
        written = " ".join(call.args[0] for call in handle.write.call_args_list)
        written_json = json.loads(written)
        print(dyn_instance.recipient_arrivals)
        print(dyn_instance.recipient_departures)
        print(dyn_instance.recipient_temporary_departures)
        assert written_json["recipients"]["1"]["arrival"] == 0
        assert written_json["recipients"]["1"]["departure"] == 17
        assert written_json["recipients"]["1"]["temporary_departures"] == []
        assert written_json["recipients"]["2"]["arrival"] == 1
        assert written_json["recipients"]["2"]["departure"] == 26
        assert written_json["recipients"]["2"]["temporary_departures"] == []
        assert written_json["recipients"]["3"]["arrival"] == 2
        assert written_json["recipients"]["3"]["departure"] == 12
        assert written_json["recipients"]["3"]["temporary_departures"] == []


def test_dyn_write_failing_transplants() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    gen = DynamicGenerator(
        recipient_arrival_function=lambda x: [1] * 25,
        recipient_attrition_function=lambda r: 0.05,
        recipient_temporary_departure_function=lambda r, l: 0,
        recipient_positive_crossmatch_function=lambda r, d: random.random() < 0.25,
        ndd_arrival_function=lambda x: [0] * 25,
        ndd_attrition_function=lambda d: 0,
        ndd_temporary_departure_function=lambda d, l: 0,
    )
    instance = fileio.read_file("tests/test_instances/test3.json")
    dyn_instance = gen.generate(instance=instance, periods=25)
    filename = "dummy.json"
    with patch("builtins.open", mock_open()) as mo:
        # No bloodgroup info, so don't write recipients
        dyn_instance.writeFileJson(filename, write_recipients=True, compressed=False)
        mo.assert_called_once_with(filename, "w")
        handle = mo()
        written = " ".join(call.args[0] for call in handle.write.call_args_list)
        written_json = json.loads(written)
        print(dyn_instance.recipient_arrivals)
        print(dyn_instance.recipient_departures)
        print(dyn_instance.recipient_temporary_departures)
        print(dyn_instance.failing_transplants)
        assert written_json["recipients"]["1"]["arrival"] == 0
        assert written_json["recipients"]["1"]["departure"] == 17
        assert written_json["recipients"]["1"]["temporary_departures"] == []
        assert written_json["recipients"]["2"]["arrival"] == 1
        assert written_json["recipients"]["2"]["departure"] == 26
        assert written_json["recipients"]["2"]["temporary_departures"] == []
        assert written_json["recipients"]["3"]["arrival"] == 2
        assert written_json["recipients"]["3"]["departure"] == 12
        assert written_json["recipients"]["3"]["temporary_departures"] == []
        assert len(written_json["failing_transplants"]) == 1
        assert written_json["failing_transplants"][0]["donor"] == "1"
        assert written_json["failing_transplants"][0]["recipient"] == "3"


def test_dyn_write_yaml() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    gen = DynamicGenerator(
        recipient_arrival_function=lambda x: [1] * 25,
        recipient_attrition_function=lambda r: 0.05,
        recipient_temporary_departure_function=lambda r, l: 0,
        recipient_positive_crossmatch_function=lambda r, d: random.random() < 0.25,
        ndd_arrival_function=lambda x: [0] * 25,
        ndd_attrition_function=lambda d: 0,
        ndd_temporary_departure_function=lambda d, l: 0,
    )
    instance = fileio.read_file("tests/test_instances/test3.json")
    dyn_instance = gen.generate(instance=instance, periods=25)
    filename = "dummy.yaml"
    with patch("builtins.open", mock_open()) as mo:
        dyn_instance.writeFileYaml(filename, compressed=False)
        mo.assert_called_once_with(filename, "w")
        handle = mo()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        yaml = YAML(typ="safe")
        written_yaml = yaml.load(written)
        assert written_yaml["recipients"]["1"]["arrival"] == 0
        assert written_yaml["recipients"]["1"]["departure"] == 17
        assert written_yaml["recipients"]["1"]["temporary_departures"] == []
        assert written_yaml["recipients"]["2"]["arrival"] == 1
        assert written_yaml["recipients"]["2"]["departure"] == 26
        assert written_yaml["recipients"]["2"]["temporary_departures"] == []
        assert written_yaml["recipients"]["3"]["arrival"] == 2
        assert written_yaml["recipients"]["3"]["departure"] == 12
        assert written_yaml["recipients"]["3"]["temporary_departures"] == []
        assert len(written_yaml["failing_transplants"]) == 1
        assert written_yaml["failing_transplants"][0]["donor"] == "1"
        assert written_yaml["failing_transplants"][0]["recipient"] == "3"


def test_dyn_write_ndds() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    gen = DynamicGenerator(
        recipient_arrival_function=lambda x: [5] * 25,
        recipient_attrition_function=lambda r: 0,
        recipient_temporary_departure_function=lambda r, l: 0,
        recipient_positive_crossmatch_function=lambda r, d: False,
        ndd_arrival_function=lambda x: [1] * 25,
        ndd_attrition_function=lambda d: 0.08,
        ndd_temporary_departure_function=lambda d, l: 0.45,
    )
    instance = fileio.read_file("tests/test_instances/test5.json")
    dyn_instance = gen.generate(instance=instance, periods=25)
    filename = "dummy.json"
    with patch("builtins.open", mock_open()) as mo:
        # No bloodgroup info, so don't write recipients
        dyn_instance.writeFileJson(filename, write_recipients=True, compressed=False)
        mo.assert_called_once_with(filename, "w")
        handle = mo()
        written = " ".join(call.args[0] for call in handle.write.call_args_list)
        written_json = json.loads(written)
        print(f"{dyn_instance.ndd_temporary_departures=}")
        print(f"{dyn_instance.ndd_departures=}")
        assert written_json["data"]["1"]["arrival"] == 0
        assert written_json["data"]["1"]["departure"] == 5
        assert written_json["data"]["1"]["temporary_departures"] == [1, 2, 5]


def test_dyn_write_ndds_yaml() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    gen = DynamicGenerator(
        recipient_arrival_function=lambda x: [5] * 25,
        recipient_attrition_function=lambda r: 0,
        recipient_temporary_departure_function=lambda r, l: 0,
        recipient_positive_crossmatch_function=lambda r, d: False,
        ndd_arrival_function=lambda x: [1] * 25,
        ndd_attrition_function=lambda d: 0.08,
        ndd_temporary_departure_function=lambda d, l: 0.45,
    )
    instance = fileio.read_file("tests/test_instances/test5.json")
    dyn_instance = gen.generate(instance=instance, periods=25)
    filename = "dummy.yaml"
    with patch("builtins.open", mock_open()) as mo:
        # No bloodgroup info, so don't write recipients
        dyn_instance.writeFileYaml(filename, compressed=False)
        mo.assert_called_once_with(filename, "w")
        handle = mo()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        yaml = YAML(typ="safe")
        written_yaml = yaml.load(written)
        assert written_yaml["donors"]["1"]["arrival"] == 0
        assert written_yaml["donors"]["1"]["departure"] == 5
        assert written_yaml["donors"]["1"]["temporary_departures"] == [1, 2, 5]


def test_read_dyn() -> None:
    instance = fileio.read_file("tests/test_instances/test3-dynamic.json")
    assert len(instance.donors) == 3
    assert len(instance.transplants) == 4
    assert len(instance.donor("1").transplants()) == 2
    assert isinstance(instance, DynamicInstance)
    assert instance.recipient_arrivals["1"] == 5
    assert instance.recipient_departures["1"] == 15
    assert instance.recipient_temporary_departures["1"] == []
    assert instance.recipient_arrivals["2"] == 7
    assert instance.recipient_departures["2"] == 12
    assert instance.recipient_temporary_departures["2"] == [8, 10]
    assert instance.recipient_arrivals["3"] == 18
    assert instance.recipient_departures["3"] == 24
    assert instance.recipient_temporary_departures["3"] == [20]
    assert len(instance.failing_transplants) == 1
    assert instance.failing_transplants[0].donor.id == "1"
    assert instance.failing_transplants[0].recipient.id == "2"


def test_read_dyn_yaml() -> None:
    instance = fileio.read_file("tests/test_instances/test3-dynamic.yaml")
    assert len(instance.donors) == 3
    assert len(instance.transplants) == 4
    assert len(instance.donor("1").transplants()) == 2
    assert isinstance(instance, DynamicInstance)
    assert instance.recipient_arrivals["1"] == 5
    assert instance.recipient_departures["1"] == 15
    assert instance.recipient_temporary_departures["1"] == []
    assert instance.recipient_arrivals["2"] == 7
    assert instance.recipient_departures["2"] == 12
    assert instance.recipient_temporary_departures["2"] == [8, 10]
    assert instance.recipient_arrivals["3"] == 18
    assert instance.recipient_departures["3"] == 24
    assert instance.recipient_temporary_departures["3"] == [20]
    assert len(instance.failing_transplants) == 1
    assert instance.failing_transplants[0].donor.id == "1"
    assert instance.failing_transplants[0].recipient.id == "2"


def test_read_dyn_compressed() -> None:
    instance = fileio.read_file("tests/test_instances/test3-dynamic.json.xz")
    assert len(instance.donors) == 3
    assert len(instance.transplants) == 4
    assert len(instance.donor("1").transplants()) == 2
    assert isinstance(instance, DynamicInstance)
    assert instance.recipient_arrivals["1"] == 5
    assert instance.recipient_departures["1"] == 15
    assert instance.recipient_temporary_departures["1"] == []
    assert instance.recipient_arrivals["2"] == 7
    assert instance.recipient_departures["2"] == 12
    assert instance.recipient_temporary_departures["2"] == [8, 10]
    assert instance.recipient_arrivals["3"] == 18
    assert instance.recipient_departures["3"] == 24
    assert instance.recipient_temporary_departures["3"] == [20]
    assert len(instance.failing_transplants) == 1
    assert instance.failing_transplants[0].donor.id == "1"
    assert instance.failing_transplants[0].recipient.id == "2"
