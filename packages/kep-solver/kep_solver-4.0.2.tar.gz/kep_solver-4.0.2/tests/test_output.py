import pytest

import kep_solver.model as model
import kep_solver.programme as programme
import kep_solver.fileio as fileio


@pytest.fixture(scope="module")
def transplant_programme():
    eff = model.EffectiveTwoWay()
    max_size = model.TransplantCount()
    backarcs = model.BackArcs()
    threes = model.ThreeWay()
    score = model.UKScore()
    objectives = [eff, max_size, threes, backarcs, score]
    return programme.Programme(
        objectives,
        description="UKLKSS Optimal set of exchanges",
        maxCycleLength=3,
        maxChainLength=3,
        build_alt_embed=1,
    )


def test_transplant_count_test1(transplant_programme) -> None:
    instance = fileio.read_json("tests/test_instances/test1.json")
    solution, model = transplant_programme.solve_single(instance)
    json_obj = fileio.UKJson(model, transplant_programme, solution)
    output = json_obj.to_string()
    with open("tests/test_instances/test1_output.json", "r") as infile:
        expected = infile.read().rstrip()
    assert output == expected


def test_transplant_count_test1_xml(transplant_programme) -> None:
    instance = fileio.read_json("tests/test_instances/test1.json")
    solution, model = transplant_programme.solve_single(instance)
    xml_obj = fileio.UKXML(model, transplant_programme, solution)
    output = xml_obj.to_string()
    with open("tests/test_instances/test1_output.xml", "r") as infile:
        expected = infile.read().rstrip()
    assert output == expected


def test_transplant_count_test9(transplant_programme) -> None:
    instance = fileio.read_json("tests/test_instances/test9.json")
    solution, model = transplant_programme.solve_single(instance)
    json_obj = fileio.UKJson(model, transplant_programme, solution)
    output = json_obj.to_string()
    with open("tests/test_instances/test9_output.json", "r") as infile:
        expected = infile.read().rstrip()
    assert output == expected


def test_transplant_count_test9_xml(transplant_programme) -> None:
    instance = fileio.read_json("tests/test_instances/test9.json")
    solution, model = transplant_programme.solve_single(instance)
    xml_obj = fileio.UKXML(model, transplant_programme, solution)
    output = xml_obj.to_string()
    with open("tests/test_instances/test9_output.xml", "r") as infile:
        expected = infile.read().rstrip()
    assert output == expected


def test_transplant_count_test10(transplant_programme) -> None:
    instance = fileio.read_json("tests/test_instances/test10.json")
    solution, model = transplant_programme.solve_single(instance)
    json_obj = fileio.UKJson(model, transplant_programme, solution)
    output = json_obj.to_string()
    with open("tests/test_instances/test10_output.json", "r") as infile:
        expected = infile.read().rstrip()
    assert output == expected


def test_transplant_count_test10_xml(transplant_programme) -> None:
    instance = fileio.read_json("tests/test_instances/test10.json")
    solution, model = transplant_programme.solve_single(instance)
    xml_obj = fileio.UKXML(model, transplant_programme, solution)
    output = xml_obj.to_string()
    with open("tests/test_instances/test10_output.xml", "r") as infile:
        expected = infile.read().rstrip()
    assert output == expected
