"""This module contains file IO functions."""

import json
import lzma
import pathlib
import typing
from defusedxml import ElementTree as ET  # type: ignore
from xml.etree import ElementTree as UnsafeET
from ruamel.yaml import YAML

from kep_solver.entities import Instance, DynamicInstance, Donor, Transplant
from kep_solver.model import Model, UK_age_score
from kep_solver.programme import Programme, Solution
from kep_solver.graph import Exchange


def read_json(filename: str) -> Instance:
    """Read an instance in JSON format from the given file

    :param filename: The name of the file containing the JSON instance
    :return: the corresponding Instance
    """
    with open(filename, "r") as infile:
        return parse_json(infile.read())


def parse_json(jsonstring: str) -> Instance | DynamicInstance:
    """Read an instance in JSON format from the given string

    :param jsonstring: A string holding a JSON representation of
        the instance
    :return: the corresponding Instance
    """
    json_obj = json.loads(jsonstring)
    if "schema" in json_obj and json_obj["schema"] >= 2:
        return parse_json_v2(json_obj)
    return parse_json_v1(json_obj)


def parse_json_v1(json_obj) -> Instance | DynamicInstance:
    """Read an instance in JSON v1 format from the given string

    :param jsonstring: A string holding a JSON representation of
        the instance
    :return: the corresponding Instance
    """
    instance: Instance
    if "recipients" in json_obj and any(
        ["arrival" in recip_info for recip_info in json_obj["recipients"].values()]
    ):
        instance = DynamicInstance()
    else:
        instance = Instance()
    data = json_obj["data"]
    for donor_id, donor_data in data.items():
        donor = Donor(donor_id)
        if "dage" in donor_data:
            donor.age = float(donor_data["dage"])
        if "bloodtype" in donor_data:
            donor.bloodGroup = donor_data["bloodtype"]
        if "bloodgroup" in donor_data:
            donor.bloodGroup = donor_data["bloodgroup"]
        if "sources" not in donor_data:
            donor.NDD = True
        elif len(donor_data["sources"]) == 0:
            donor.NDD = True
        elif len(donor_data["sources"]) != 1:
            raise Exception("Donor with more than one recipient detected")
        else:
            recip = instance.recipient(str(donor_data["sources"][0]))
            donor.recipient = recip
            recip.addDonor(donor)
        if donor.NDD and isinstance(instance, DynamicInstance):
            try:
                instance.ndd_arrivals[donor.id] = donor_data["arrival"]
                instance.ndd_departures[donor.id] = donor_data["departure"]
                instance.ndd_temporary_departures[donor.id] = donor_data[
                    "temporary_departures"
                ]
            except KeyError:
                # This particular recipient never arrives, so won't have any of these
                pass

        instance.addDonor(donor)
        if "matches" in donor_data:
            for arc in donor_data["matches"]:
                recip = instance.recipient(str(arc["recipient"]))
                t = Transplant(donor, recip, float(arc["score"]))
                instance.addTransplant(t)
    if "recipients" in json_obj:
        recips = json_obj["recipients"]
        for rid, info in recips.items():
            recip = instance.recipient(str(rid))
            if "pra" in info:
                recip.cPRA = float(info["pra"])
            if "cPRA" in info:
                recip.cPRA = float(info["cPRA"])
            if "bloodgroup" in info:
                recip.bloodGroup = info["bloodgroup"]
            if "bloodtype" in info:
                recip.bloodGroup = info["bloodtype"]
            if isinstance(instance, DynamicInstance):
                try:
                    instance.recipient_arrivals[recip.id] = info["arrival"]
                    instance.recipient_departures[recip.id] = info["departure"]
                    instance.recipient_temporary_departures[recip.id] = info[
                        "temporary_departures"
                    ]
                except KeyError:
                    # This particular recipient never arrives, so won't have any of these
                    pass
    if isinstance(instance, DynamicInstance):
        instance.failing_transplants = [
            instance.donor(transplant["donor"]).getTransplantTo(
                instance.recipient(transplant["recipient"]),
            )
            for transplant in json_obj["failing_transplants"]
        ]
    return instance


def parse_json_v2(json_obj) -> Instance | DynamicInstance:
    """Read an instance in JSON v2 format from the given string

    :param jsonstring: A string holding a JSON representation of
        the instance
    :return: the corresponding Instance
    """
    instance: Instance
    if "recipients" in json_obj and any(
        ["arrival" in recip_info for recip_info in json_obj["recipients"]]
    ):
        instance = DynamicInstance()
    else:
        instance = Instance()
    donors = json_obj["donors"]
    for donor_data in donors:
        # If donor_data is a string, then donors is a dictionary mapping IDs to
        # donors, so extract the appropriate donor data
        if isinstance(donor_data, str):
            donor_data = donors[donor_data]
        donor = Donor(donor_data["id"])
        if "age" in donor_data:
            donor.age = float(donor_data["age"])
        if "bloodtype" in donor_data:
            donor.bloodGroup = donor_data["bloodtype"]
        if len(donor_data["paired_recipients"]) == 0:
            donor.NDD = True
        elif len(donor_data["paired_recipients"]) != 1:
            raise Exception("Donor with more than one recipient detected")
        else:
            recip = instance.recipient(str(donor_data["paired_recipients"][0]))
            donor.recipient = recip
            recip.addDonor(donor)
        if donor.NDD and isinstance(instance, DynamicInstance):
            try:
                instance.ndd_arrivals[donor.id] = donor_data["arrival"]
                instance.ndd_departures[donor.id] = donor_data["departure"]
                instance.ndd_temporary_departures[donor.id] = donor_data[
                    "temporary_departures"
                ]
            except KeyError:
                # This particular NDD never arrives, so won't have any of these
                pass
        if "properties" in donor_data:
            donor.property = {
                key: value for key, value in donor_data["properties"].items()
            }
        instance.addDonor(donor)
        for arc in donor_data["outgoing_transplants"]:
            recip = instance.recipient(str(arc["recipient"]))
            t = Transplant(donor, recip, float(arc["score"]))
            instance.addTransplant(t)
    for recip_data in json_obj["recipients"]:
        # If recip_data is a string, then recipients is a dictionary mapping
        # IDs to recipients, so extract the appropriate recipient data
        if isinstance(recip_data, str):
            recip_data = json_obj["recipients"][recip_data]
        recip = instance.recipient(str(recip_data["id"]))
        if "cPRA" in recip_data:
            # Divide by 100 as kep_solver works with the range [0-1]
            recip.cPRA = float(recip_data["cPRA"]) / 100
        if "bloodtype" in recip_data:
            recip.bloodGroup = recip_data["bloodtype"]
        if "properties" in recip_data:
            recip.property = {
                key: value for key, value in recip_data["properties"].items()
            }
        if isinstance(instance, DynamicInstance):
            try:
                instance.recipient_arrivals[recip.id] = recip_data["arrival"]
                instance.recipient_departures[recip.id] = recip_data["departure"]
                instance.recipient_temporary_departures[recip.id] = recip_data[
                    "temporary_departures"
                ]
            except KeyError:
                # This particular recipient never arrives, so won't have any of these
                pass
    if isinstance(instance, DynamicInstance):
        instance.failing_transplants = [
            instance.donor(transplant["donor"]).getTransplantTo(
                instance.recipient(transplant["recipient"]),
            )
            for transplant in json_obj["failing_transplants"]
        ]
    return instance


def read_xml(filename: str) -> Instance:
    """Read an instance in XML format from the given file

    :param filename: The name of the file containing the XML instance
    :return: the corresponding Instance
    """
    with open(filename, "r") as infile:
        return parse_xml(infile.read())


def parse_xml(xmlstring: str) -> Instance:
    """Read an instance in XML format from the given string

    :param xmlstring: A string holding a XML representation of
        the instance
    :return: the corresponding Instance
    """
    xml = ET.fromstring(xmlstring)
    instance = Instance()
    for donor_xml in xml:
        donor = Donor(donor_xml.attrib["donor_id"])
        age_xml = donor_xml.find("dage")
        if age_xml is not None:
            donor.age = float(age_xml.text)
        bloodgroup_xml = donor_xml.find("bloodgroup")
        if bloodgroup_xml is not None:
            donor.bloodGroup = bloodgroup_xml.text
        sources = donor_xml.find("sources")
        if sources is not None:
            if len(sources) == 0:
                donor.NDD = True
            elif len(sources) != 1:
                raise Exception("Donor with more than one recipient detected")
            recip = instance.recipient(str(sources[0].text))
            donor.recipient = recip
            recip.addDonor(donor)
        else:
            donor.NDD = True
        instance.addDonor(donor)
        matches = donor_xml.find("matches")
        if matches is not None:
            for match in matches:
                recip = instance.recipient(str(match.find("recipient").text))
                score = float(match.find("score").text)
                t = Transplant(donor, recip, score)
                instance.addTransplant(t)
    return instance


def read_yaml(filename: str) -> Instance:
    """Read an instance in YAML format from the given file

    :param filename: The name of the file containing the YAML instance
    :return: the corresponding Instance
    """
    with open(filename, "r") as infile:
        return parse_yaml(infile.read())


def parse_yaml(yamlstring: str) -> Instance | DynamicInstance:
    """Read an instance in YAML format from the given string

    :param xmlstring: A string holding a YAML representation of
        the instance
    :return: the corresponding Instance
    """
    yaml = YAML(typ="safe")
    yml_obj = yaml.load(yamlstring)
    if yml_obj["schema"] != 1:
        raise Exception("Unknown schema version in YAML")
    instance = Instance()
    if "recipients" in yml_obj and any(
        ["arrival" in recip_info for recip_info in yml_obj["recipients"].values()]
    ):
        instance = DynamicInstance()
    else:
        instance = Instance()
    for donor_id, donor_dict in yml_obj["donors"].items():
        donor = Donor(donor_id)
        if "age" in donor_dict:
            donor.age = donor_dict["age"]
        if "bloodtype" in donor_dict:
            donor.bloodGroup = donor_dict["bloodtype"]
        if "bloodgroup" in donor_dict:
            donor.bloodGroup = donor_dict["bloodgroup"]
        if "recipients" not in donor_dict:
            donor.NDD = True
        elif len(donor_dict["recipients"]) == 0:
            donor.NDD = True
        elif len(donor_dict["recipients"]) != 1:
            raise Exception("Donor with more than one recipient detected")
        else:
            recip = instance.recipient(donor_dict["recipients"][0])
            donor.recipient = recip
            recip.addDonor(donor)
        if donor.NDD and isinstance(instance, DynamicInstance):
            try:
                instance.ndd_arrivals[donor.id] = donor_dict["arrival"]
                instance.ndd_departures[donor.id] = donor_dict["departure"]
                instance.ndd_temporary_departures[donor.id] = donor_dict[
                    "temporary_departures"
                ]
            except KeyError:
                # This particular NDD never arrives, so won't have any of these
                pass
        instance.addDonor(donor)
        if "matches" in donor_dict:
            for arc in donor_dict["matches"]:
                recip = instance.recipient((arc["recipient_id"]))
                t = Transplant(donor, recip, arc["score"])
                instance.addTransplant(t)
    if "recipients" in yml_obj:
        for recip_id, recip_dict in yml_obj["recipients"].items():
            recip = instance.recipient(recip_id)
            for cpra in ["pra", "cPRA", "cPra"]:
                if cpra in recip_dict:
                    recip.cPRA = recip_dict[cpra]
                    break
            for bloodgroup in ["bloodgroup", "bloodtype"]:
                if bloodgroup in recip_dict:
                    recip.bloodGroup = recip_dict[bloodgroup]
            if isinstance(instance, DynamicInstance):
                try:
                    instance.recipient_arrivals[recip.id] = recip_dict["arrival"]
                    instance.recipient_departures[recip.id] = recip_dict["departure"]
                    instance.recipient_temporary_departures[recip.id] = recip_dict[
                        "temporary_departures"
                    ]
                except KeyError:
                    # This particular recipient never arrives, so won't have any of these
                    pass
    if isinstance(instance, DynamicInstance):
        instance.failing_transplants = [
            instance.donor(transplant["donor"]).getTransplantTo(
                instance.recipient(transplant["recipient"]),
            )
            for transplant in yml_obj["failing_transplants"]
        ]
    return instance


def read_compressed(filename: str) -> Instance:
    """Read a compressed file containing a KEP instance. Will attempt to detect
    the correct file format if possible.

    :param filename: The name of the file containing the instance
    :return: the corresponding Instance
    """
    suffixes = pathlib.Path(filename).suffixes
    if suffixes[-1] != ".xz":
        raise Exception("kep_solver can only read .xz compressed files")
    with lzma.open(filename, "rt") as infile:
        match suffixes[-2]:
            case ".json":
                return parse_json(infile.read())
            case ".yaml":
                return parse_yaml(infile.read())
            case ".xml":
                return parse_xml(infile.read())
    raise Exception(f"Unknown file format: {filename}")


def read_file(filename: str) -> Instance | DynamicInstance:
    """Read a file containing a KEP instance. Will attempt to detect the
    correct file format if possible.

    :param filename: The name of the file containing the instance
    :return: the corresponding Instance
    """
    match pathlib.Path(filename).suffix:
        case ".xz":
            return read_compressed(filename)
        case ".xml":
            return read_xml(filename)
        case ".json":
            return read_json(filename)
        case ".yaml":
            return read_yaml(filename)
    raise Exception(f"Unknown filetype: {filename}")


# The UK output format needs "two_way", "three_way" and so-on.
_NUM_TO_WORDS = {
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
}


class UKJson:
    """A class for outputing JSON-formatted results in the style prescribed by
    the UK KEP and NHSBT.
    """

    def __init__(self, model: Model, programme: Programme, solution: Solution):
        self._programme: Programme = programme
        self._model: Model = model
        self._solution: Solution = solution

    def _cycle(self, exchange: Exchange):
        """Create the appropriate JSON object for an exchange."""
        cycles = []
        total_weight = 0
        for ind, vertex in enumerate(exchange):
            donor = vertex.donor
            inner_obj = {"d": donor.id}
            if donor.NDD:
                inner_obj["a"] = True
            else:
                inner_obj["p"] = donor.recipient.id
            target_v = exchange[(ind + 1) % len(exchange)]
            if target_v.donor.NDD:
                inner_obj["tb"] = 0
                inner_obj["dif"] = 0
                inner_obj["s"] = 0
                desired = set([donor.recipient])
            else:
                recipient = target_v.donor.recipient
                bonus, tb = UK_age_score(donor, target_v.donor)
                transplants = [
                    t for t in donor.transplants() if t.recipient == recipient
                ]
                assert len(transplants) == 1
                transplant = transplants[0]
                inner_obj["tb"] = tb
                inner_obj["dif"] = bonus
                inner_obj["s"] = transplant.weight
                total_weight += tb + bonus + transplant.weight
                if donor.NDD:
                    desired = set([recipient])
                else:
                    desired = set([donor.recipient, recipient])
            if len(exchange) == 3:
                # Search for a backarc only in exchanges with 3 vertices
                best_score: float = -1
                # If there are multiple potential backarcs, we want the one
                # with the best score
                for backarc in exchange.backarc_exchanges_uk():
                    if set(backarc.allRecipients()) == desired:
                        if len(backarc) == 2:  # 2 vertices in the "backarc exchange"
                            new_score = self._model.exchange_values(backarc)[-1]
                            if new_score > best_score:
                                inner_obj["b"] = backarc.id
                                best_score = new_score
            cycles.append(inner_obj)
        obj = {
            "cycle": cycles,
            "backarcs": exchange.num_backarcs_uk(),
            "weight": round(total_weight, 5),
            "alt": [alternate.id for alternate in exchange.alternates],
        }
        return obj

    def to_string(self) -> str:
        """Return a string representing the solution as a JSON object.

        :return: A string representing the JSON.
        """
        obj: dict[str, typing.Any] = {"algorithm": self._programme.description}
        obj["output"] = {
            "all_cycles": {
                modelled.exchange.id: self._cycle(modelled.exchange)
                for modelled in self._solution.possible
                if len(modelled.exchange) >= 2
            }
        }
        obj["exchange_data"] = [
            {
                "description": self._programme.description,
                "exchanges": [
                    modelled.exchange.id for modelled in self._solution.selected
                ],
                "weight": round(self._solution.values[-1], 5),
                "total_transplants": self._solution.values[1],
            }
        ]
        for i in range(
            2, max(self._programme.maxCycleLength, self._programme.maxChainLength) + 1
        ):
            name = f"{_NUM_TO_WORDS[i]}_way_exchanges"
            count = len([c for c in self._solution.selected if len(c.exchange) == i])
            obj["exchange_data"][0][name] = count
        return json.dumps(obj)

    def write(self, output: typing.TextIO):
        """Write the details to a JSON file, or file-like object.

        :param output: A file-like object where output will be written.
        """
        output.write(self.to_string())


class UKXML:
    """A class for outputing XML-formatted results in the style prescribed by
    the UK KEP and NHSBT.
    """

    def __init__(self, model: Model, programme: Programme, solution: Solution):
        if len(programme.objectives) != 5:
            raise Exception("UKXML format only works with the NHS objectives")
        self._programme: Programme = programme
        self._model: Model = model
        self._solution: Solution = solution

    def _add_cycle(self, et: UnsafeET.Element, exchange: Exchange):
        """Create the appropriate XML object for an exchange."""
        cycle = []
        total_weight = 0
        for ind, vertex in enumerate(exchange):
            donor = vertex.donor
            inner_obj = {"d": donor.id}
            if donor.NDD:
                inner_obj["a"] = True
            else:
                inner_obj["p"] = donor.recipient.id
            target_v = exchange[(ind + 1) % len(exchange)]
            if target_v.donor.NDD:
                inner_obj["tb"] = 0
                inner_obj["dif"] = 0
                inner_obj["s"] = 0
                desired = set([donor.recipient])
            else:
                recipient = target_v.donor.recipient
                bonus, tb = UK_age_score(donor, target_v.donor)
                transplants = [
                    t for t in donor.transplants() if t.recipient == recipient
                ]
                assert len(transplants) == 1
                transplant = transplants[0]
                inner_obj["tb"] = tb
                inner_obj["dif"] = bonus
                inner_obj["s"] = int(transplant.weight)
                total_weight += tb + bonus + transplant.weight
                if donor.NDD:
                    desired = set([recipient])
                else:
                    desired = set([donor.recipient, recipient])
            if len(exchange) == 3:
                # Search for a backarc only in exchanges with 3 vertices
                best_score: float = -1
                # If there are multiple potential backarcs, we want the one
                # with the best score
                for backarc in exchange.backarc_exchanges_uk():
                    if set(backarc.allRecipients()) == desired:
                        if len(backarc) == 2:  # 2 vertices in the "backarc exchange"
                            new_score = self._model.exchange_values(backarc)[-1]
                            if new_score > best_score:
                                inner_obj["b"] = backarc.id
                                best_score = new_score
            cycle.append(inner_obj)
        cycle_e = UnsafeET.SubElement(
            et,
            "cycle",
            attrib={
                "id": exchange.id,
                "backarcs": str(exchange.num_backarcs_uk()),
                "weight": str(round(total_weight, 5)),
                "alt": ",".join(
                    [str(alternate.id) for alternate in exchange.alternates]
                ),
            },
        )
        for pair in cycle:
            inner = UnsafeET.SubElement(cycle_e, "pair")
            for key, value in pair.items():
                UnsafeET.SubElement(inner, key).text = str(value)
        return

    def to_string(self) -> str:
        """Return a string representing the solution as a JSON object.

        :return: A string representing the JSON.
        """
        root = UnsafeET.Element("data")
        UnsafeET.SubElement(root, "algorithm").text = self._programme.description
        output = UnsafeET.SubElement(root, "output")
        all_cycles = UnsafeET.SubElement(output, "all_cycles")
        for modelled in self._solution.possible:
            if len(modelled.exchange) >= 2:
                self._add_cycle(all_cycles, modelled.exchange)
        ed_e = UnsafeET.SubElement(output, "exchange_data")
        entry_attribs: dict[str, str] = {
            "weight": str(round(self._solution.values[-1], 5)),
            "total_transplants": str(int(self._solution.values[1])),
        }
        for i in range(
            2, max(self._programme.maxCycleLength, self._programme.maxChainLength) + 1
        ):
            name = f"{_NUM_TO_WORDS[i]}_way_exchanges"
            count = len([c for c in self._solution.selected if len(c.exchange) == i])
            entry_attribs[name] = str(count)
        entry_e = UnsafeET.SubElement(ed_e, "entry", attrib=entry_attribs)
        UnsafeET.SubElement(entry_e, "description").text = self._programme.description
        exchanges_e = UnsafeET.SubElement(entry_e, "exchanges")
        for modelled in self._solution.selected:
            UnsafeET.SubElement(exchanges_e, "cycle").text = str(modelled.exchange.id)
        return UnsafeET.tostring(root, encoding="unicode")

    def write(self, output: typing.TextIO):
        """Write the details to a XML file, or file-like object.

        :param output: A file-like object where output will be written.
        """
        output.write(self.to_string())


def write_dynamic_results(
    matchruns: list[tuple[int, Instance, Model, Solution]],
    exchanged: dict[int, list[Exchange]],
    outfile: str,
) -> None:
    """Save the results of a dynamic simulation to a JSON file.

    :param matchruns: A list of the match runs performed. Each entry is a tuple
        containing the period in which the match run occured, the input
        Instance, the Model used to solve the problem, and the Solution.
    :param exchanged: A dictionary mapping each period to the list of exchanges
        performed in that period.
    """
    match_runs: list[dict[str, int | list[str | list[str]] | dict[str, float]]] = []
    for period, instance, model, solution in matchruns:
        times = {step.description: step.time for step in solution.times}

        def vert_id(vertex):
            if vertex.isNdd():
                return vertex.donor.id
            return vertex.donor.recipient.id

        match_runs.append(
            {
                "period": period,
                "in_match_run": [
                    recipient.id for recipient in instance.allRecipients()
                ],
                "selected": [
                    [vert_id(vertex) for vertex in modelled.exchange.vertices]
                    for modelled in solution.selected
                ],
                "times": times,
            }
        )
    transplanted: dict[int, list[list[str]]] = {}
    for period, performed in exchanged.items():
        transplanted_in_this_period: list[list[str]] = []
        for exchange in performed:
            for donor, recipient in exchange.transplantPairs():
                transplanted_in_this_period.append([donor.id, recipient.id])
        transplanted[period] = transplanted_in_this_period
    with open(outfile, "w") as output:
        json.dump(
            {
                "matchruns": match_runs,
                "performed": transplanted,
            },
            output,
        )
