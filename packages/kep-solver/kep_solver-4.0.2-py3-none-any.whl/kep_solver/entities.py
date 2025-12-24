"""This module contains entities (such as Donors, Recipients) within
a KEP, as well as the encapsulating Instance objects
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import ValuesView
from dataclasses import dataclass, field
from enum import Enum
import json
import lzma
from typing import Optional, Union, Any, MutableMapping, TextIO, TypeVar

# Note: In this file we need to write XML, so we cannot used defusedxml. Do not
# attempt to read any XML in this file, as defusedxml is not loaded
import xml.etree.ElementTree as ET  # type: ignore
import pandas  # type: ignore
from ruamel.yaml import YAML

# We need numpy for NaN, as pandas won't allow None as a categorical data type,
# but will allow NaN
import numpy  # type: ignore


class KEPDataValidationException(Exception):
    """An exception that is raised when invalid data requests are made.
    This can happen if properties (such as blood group or cPRA) are
    requested when they are not known, or if changes are attempted on
    such properties.
    """

    pass


class KEPSolveFail(Exception):
    """An exception that is raised when solving fails. This should only really
    be happening if the user sets a solver time limit, and this time limit is
    reached, but this is not guaranteed.
    """

    pass


class BloodGroup(Enum):
    """The :ref:`Blood group` of a participant in a KEP."""

    O = 0  # noqa: E741
    A = 1
    B = 2
    AB = 3

    @staticmethod
    def all() -> ValuesView["BloodGroup"]:
        return _BLOODGROUPS.values()

    @staticmethod
    def from_str(bloodGroupText: str) -> "BloodGroup":
        """Given a blood group as text, return the corresponding
        BloodGroup object.

        :param bloodGroupText: the text
        :return: the BloodGroup
        """
        if bloodGroupText not in _BLOODGROUPS:
            raise Exception(f"Unknown blood group: {bloodGroupText}")
        return _BLOODGROUPS[bloodGroupText]

    def __str__(self):
        return _BG_TO_STR[self]


_BLOODGROUPS = {
    "O": BloodGroup.O,
    "A": BloodGroup.A,
    "B": BloodGroup.B,
    "AB": BloodGroup.AB,
}


_BG_TO_STR = {
    BloodGroup.O: "O",
    BloodGroup.A: "A",
    BloodGroup.B: "B",
    BloodGroup.AB: "AB",
}


class Status(Enum):
    """A status indicator for either a donor or a recipient."""

    InPool = "In Pool"
    Left = "Left"
    TemporarilyLeft = "TemporarilyLeft"
    Selected = "Selected"
    NotYetArrived = "Not Yet Arrived"
    Transplanted = "Transplanted"


class Recipient:
    """A recipient in a KEP instance."""

    def __init__(self, id: str):
        self._id: str = id
        self._age: Optional[float] = None
        self._cPRA: Optional[float] = None
        self._bloodGroup: Optional[BloodGroup] = None
        self._donors: list[Donor] = []
        self._compatibilityChance: Optional[float] = None
        self.status: Status = Status.InPool
        """The status of this recipient."""

        self.property: dict[str, Any] = {}
        """A dictionary that can store arbitrary properties related to this recipient.
        """

    def __str__(self):
        return f"R_{self._id}"

    def __repr__(self):
        return str(self)

    def longstr(self) -> str:
        """A longer string representation.

        :return: a string representation
        """
        return f"Recipient {self._id}"

    def __hash__(self):
        return hash(f"R{self._id}")

    @property
    def id(self) -> str:
        """Return the ID of this recipient."""
        return self._id

    @property
    def age(self) -> float:
        """The age of this recipient (in years), fractions allowed."""
        if self._age is None:
            raise KEPDataValidationException(f"Age of {str(self)} not known")
        return self._age

    @age.setter
    def age(self, age: float) -> None:
        if self._age is not None and self._age != age:
            raise KEPDataValidationException(f"Trying to change age of {str(self)}")
        self._age = age

    @property
    def cPRA(self) -> float:
        """The :ref:`cPRA` of this recipient, as a value between 0 and 1.

        You may have to divide by 100 if you are used to working with values from 1 to 100 inclusive.
        """
        if self._cPRA is None:
            raise KEPDataValidationException(f"cPRA of {str(self)} not known")
        return self._cPRA

    @cPRA.setter
    def cPRA(self, cPRA: float) -> None:
        if self._cPRA is not None and self._cPRA != cPRA:
            raise KEPDataValidationException(f"Trying to change cPRA of {str(self)}")
        if cPRA > 1 or cPRA < 0:
            raise KEPDataValidationException(
                f"Trying to set the cPRA of {str(self)} to an invalid value."
            )
        self._cPRA = cPRA

    @property
    def bloodGroup(self) -> BloodGroup:
        """The :ref:`Blood group` of this recipient."""
        if self._bloodGroup is None:
            raise KEPDataValidationException(f"Blood group of {str(self)} not known")
        return self._bloodGroup

    @bloodGroup.setter
    def bloodGroup(self, bloodGroup: Union[str, BloodGroup]) -> None:
        if isinstance(bloodGroup, str):
            group = BloodGroup.from_str(bloodGroup)
        else:
            group = bloodGroup
        if self._bloodGroup is not None and self._bloodGroup != group:
            raise KEPDataValidationException(
                f"Trying to change blood group of {str(self)}"
            )
        self._bloodGroup = group

    @property
    def compatibilityChance(self) -> float:
        """The :ref:`compatibility chance` of this Recipient. In other words, what is
        the likelihood that this recipient will be transplant-compatible with
        an arbitrary donor who is ABO compatible."""
        if self._compatibilityChance is None:
            raise KEPDataValidationException(
                f"compatibilityChance of {str(self)} not known"
            )
        return self._compatibilityChance

    @compatibilityChance.setter
    def compatibilityChance(self, new: float) -> None:
        if self._compatibilityChance is not None and self._compatibilityChance != new:
            raise KEPDataValidationException(
                f"Trying to change compatibilityChance of {str(self)}"
            )
        if new > 1 or new < 0:
            raise KEPDataValidationException(
                f"Trying to set the compatibilityChance of {str(self)} to an invalid value."
            )
        self._compatibilityChance = new

    def inPool(self) -> bool:
        """Return True if and only if this recipient is in this pool. This is
        true if this recipient has a status of InPool and at least one of their
        donors has this status too.
        """
        return self.status == Status.InPool and any(
            d.status == Status.InPool for d in self.donors()
        )

    def addDonor(self, donor: Donor) -> None:
        """Add a paired donor for this recipient.

        :param donor: The donor to add
        """
        self._donors.append(donor)

    def donors(self) -> list[Donor]:
        """The list of donors paired with this recipient

        :return: the list of donors
        """
        return self._donors

    def hasBloodCompatibleDonor(self) -> bool:
        """Return true if the recipient is paired with at least one
        donor who is blood-group compatible with this recipient.

        :return: true if the recipient has a blood-group compatible
            donor
        """
        for donor in self.donors():
            if donor.bloodGroupCompatible(self):
                return True
        return False

    def pairedWith(self, donor: Donor) -> bool:
        """Return true if the given donor is paired with this recipient.

        :param donor: The donor in question
        :return: true if the donor is paired with this recipient
        """
        return donor in self.donors()


class Donor:
    """A donor (directed or non-directed) in an instance."""

    def __init__(self, id: str):
        """Construct a Donor object. These are assumed to be
        directed, this can be changed with the NDD instance variable.

        :param id: An identifier for this donor.
        """
        self._id: str = id
        self._recip: Optional[Recipient] = None
        self.NDD: bool = False
        self._age: Optional[float] = None
        self._bloodGroup: Optional[BloodGroup] = None
        self._outgoingTransplants: list["Transplant"] = []
        self.status = Status.InPool
        """The status of this donor."""

        self.property: dict[str, Any] = {}
        """A dictionary that can store arbitrary properties related to this donor.
        """

    def __eq__(self, other):
        # An instance can only have one donor of each ID.
        return self.id == other.id

    def __str__(self):
        if self.NDD:
            return f"NDD_{self._id}"
        return f"D_{self._id}"

    def __repr__(self):
        return str(self)

    def longstr(self):
        """A longer string representation.

        :return: a string representation
        """
        if self.NDD:
            return f"Non-directed donor {self._id}"
        return f"Donor {self._id}"

    def __hash__(self):
        return hash(f"D{self._id}")

    @property
    def id(self) -> str:
        """Return the ID of this donor."""
        return self._id

    @property
    def age(self) -> float:
        """The age of the donor (in years), fractions allowed."""
        if self._age is None:
            raise KEPDataValidationException(f"Age of donor {self.id} not known")
        return self._age

    @age.setter
    def age(self, age: float) -> None:
        if self._age is not None and self._age != age:
            raise KEPDataValidationException(f"Trying to change age of donor {self.id}")
        self._age = age

    @property
    def bloodGroup(self) -> BloodGroup:
        """The donor's :ref:`Blood group`"""
        if self._bloodGroup is None:
            raise KEPDataValidationException(f"Blood group of {str(self)} not known")
        return self._bloodGroup

    @bloodGroup.setter
    def bloodGroup(self, bloodGroup: Union[str, BloodGroup]) -> None:
        if isinstance(bloodGroup, str):
            group = BloodGroup.from_str(bloodGroup)
        else:
            group = bloodGroup
        if self._bloodGroup is not None and self._bloodGroup != group:
            raise KEPDataValidationException(
                f"Trying to change blood group of {str(self)}"
            )
        self._bloodGroup = group

    @property
    def recipient(self) -> Recipient:
        """The recipient paired with this donor."""
        if self.NDD:
            raise KEPDataValidationException(
                f"Tried to get recipient of non-directed donor {str(self)}."
            )
        if not self._recip:
            raise KEPDataValidationException(
                f"Donor {str(self)} is directed but has no recipient."
            )
        return self._recip

    @recipient.setter
    def recipient(self, new_recip: Recipient) -> None:
        if self._recip is not None:
            raise KEPDataValidationException(
                f"Tried to set a second recipient on donor {str(self)}"
            )
        if self.NDD:
            raise KEPDataValidationException(
                f"Tried to set recipient of non-directed donor {str(self)}."
            )
        self._recip = new_recip

    def inPool(self) -> bool:
        """Return True if and only if this donor is in this pool. This is
        true if this donor has a status of InPool and their recipient has
        this status too.
        """
        return self.status == Status.InPool and (
            self.NDD or self.recipient.status == Status.InPool
        )

    def bloodGroupCompatible(self, recipient: Recipient) -> bool:
        """Is this donor blood-group compatible with the given
        recipient.

        :param recipient: the recipient in question
        :return: True if the donor is blood-group compatible with the
            given recipient
        """
        if self.bloodGroup == BloodGroup.O:
            return True
        if recipient.bloodGroup == BloodGroup.AB:
            return True
        return recipient.bloodGroup == self.bloodGroup

    def addTransplant(self, transplant: "Transplant") -> None:
        """Add a potential transplant from this donor.

        :param transplant: the transplant object
        """
        self._outgoingTransplants.append(transplant)

    def getTransplantTo(self, recipient: Recipient) -> Transplant:
        """Return the transplant from this donor to the given recipient.

        :param recipient: The recipient in question.
        :return: The transplant in question.
        """
        for t in self._outgoingTransplants:
            if t.recipient == recipient:
                return t
        raise KEPDataValidationException(
            f"Transplant from {self} to {recipient} not found"
        )

    def transplants(self) -> list[Transplant]:
        """Return the list of transplants associated with this Donor.

        :return: A list of transplants
        """
        return self._outgoingTransplants


class Transplant:
    """A potential transplant."""

    def __init__(self, donor: Donor, recipient: Recipient, weight: float):
        self._donor: Donor = donor
        self._recipient: Recipient = recipient
        self._weight: float = weight
        self.known_to_fail = False

    def __str__(self):
        """Return a string representation of this transplant."""
        return f"Transplant({str(self.donor)}, {str(self.recipient)}, {self.weight})"

    def __repr__(self):
        return str(self)

    @property
    def donor(self) -> Donor:
        return self._donor

    @property
    def recipient(self) -> Recipient:
        return self._recipient

    @property
    def weight(self) -> float:
        return self._weight


class OutputFormat(Enum):
    JSON = 1
    XML = 2
    YAML = 3


def _getOutFile(filename: str, compressed: bool) -> TextIO:
    """Get an output file object based on filename, and compression.

    :param filename: The name of the file to open.
    :param compressed: Should the file be opened for compression?
    :return: A file-like object
    """
    if compressed:
        if not filename[-3:] == ".xz":
            filename += ".xz"
        return lzma.open(filename, "wt")
    return open(filename, "w")


@dataclass
class Instance:
    """A KEP instance."""

    donors: MutableMapping[str, Donor] = field(default_factory=dict)
    """A mapping (dictionary) from donor IDs to the donors in this instance."""
    recipients: MutableMapping[str, Recipient] = field(default_factory=dict)
    """A mapping (dictionary) from recipient IDs to the recipients in this instance."""

    @property
    def transplants(self) -> list[Transplant]:
        """Return all transplants relevant for this instance."""
        result: list[Transplant] = []
        for d in self.donors.values():
            result.extend(d.transplants())
        return result

    def activeTransplants(self) -> list[Transplant]:
        """Return all transplants relevant for this instance."""
        result: list[Transplant] = []
        for d in self.donors.values():
            if not d.inPool():
                continue
            result.extend(
                t
                for t in d.transplants()
                if t.recipient.id in self.recipients and t.recipient.inPool()
            )
        return result

    def addDonor(self, donor: Donor) -> None:
        """Add a donor to the instance.

        :param donor: The Donor being added
        """
        if donor.id in self.donors:
            raise KEPDataValidationException(
                f"Trying to replace Donor {donor.id} in instance"
            )
        self.donors[donor.id] = donor

    def recipient(self, id: str, create: bool = True) -> Recipient:
        """Get a recipient from the instance by ID. If the recipient
        does not exist, create one with no details.

        :param id: the ID of the recipient
        :param create: If True, will create recipient if it doesn't
            exist. If False, and the recipient does not exist, will
            raise an exception.
        :return: the recipient
        """
        if id in self.recipients:
            return self.recipients[id]
        if not create:
            raise KEPDataValidationException(f"Recipient with ID '{id}' not found")
        recip = Recipient(id)
        self.recipients[id] = recip
        return recip

    def addRecipient(self, recipient: Recipient) -> None:
        """Adds an already-constructed Recipient to this instance. If a
        recipient with the same ID already exists, this will throw an
        exception. This will also add the paired donors of the recipient to
        this instance.

        :param recipient: The recipient to add.
        """
        if recipient.id in self.recipients:
            raise KEPDataValidationException(
                f"Tried to add a Recipient with ID '{id}' but one already exists"
            )
        self.recipients[recipient.id] = recipient
        for donor in recipient.donors():
            self.addDonor(donor)

    def allRecipients(self) -> ValuesView[Recipient]:
        """Return a list of all recipients.

        :return: a list of recipients
        """
        return self.recipients.values()

    def activeRecipients(self) -> list[Recipient]:
        """Return a list of the recipients in the instance. These recipients
        must have the status InPool and so must at least one of their donors.

        :return: a list of donors
        """
        return [r for r in self.recipients.values() if r.inPool()]

    def hasRecipient(self, recipient: Recipient) -> bool:
        """Return True if the given Recipient is in this instance.

        :param recipient: The recipient in question.
        :return: True if and only if the recipient is in this instance.
        """
        return recipient.id in self.recipients.keys()

    def addTransplant(self, transplant: Transplant) -> None:
        """Add a potential transplant to this instance.

        :param transplant: The transplant
        """
        transplant.donor.addTransplant(transplant)

    def allDonors(self) -> ValuesView[Donor]:
        """Return a generator object that can iterate through donors
        in a list-like fashion. Note that this list cannot itself be
        modified.

        :return: a list of donors
        """
        return self.donors.values()

    def allNDDs(self) -> list[Donor]:
        """Return an iterable over all non-directed donors in this instance.

        :return: An iterable of non-directed donors
        """
        return [d for d in self.allDonors() if d.NDD]

    def activeDonors(self) -> list[Donor]:
        """Return a list of the donors who are in the pool (according to their
        status, and possibly the status of their paired recipient if they are a
        directed donor.

        :return: a list of donors
        """
        return [d for d in self.donors.values() if d.inPool()]

    def hasDonor(self, donor: Donor) -> bool:
        """Return True if the given Donor is in this instance.

        :param donor: The donor in question.
        :return: True if and only if the donor is in this instance.
        """
        return donor.id in self.donors.keys()

    def donor(self, id: str) -> Donor:
        """Return a donor by ID:

        :param id: a donor ID
        :return: the donor
        """
        return self.donors[id]

    def writeFile(
        self, filename: str, file_format: OutputFormat, compressed: bool = True
    ) -> None:
        """Write the instance to a file of the given format.

        :param filename: The name of the file to write
        :param file_format: The file format to use. Currenly only JSON is
            supported
        :param compressed: Should the file saved as a compressed file (using
            LZMA compression as a .xz file)
        """
        if file_format == OutputFormat.JSON:
            self.writeFileJson(filename, compressed=compressed)
        elif file_format == OutputFormat.XML:
            self.writeFileXml(filename, compressed)
        elif file_format == OutputFormat.YAML:
            self.writeFileYaml(filename, compressed)

    def writeFileXml(self, filename: str, compressed: bool) -> None:
        """Write the instance to an XML file

        :param filename: The name of the file to write
        :param compressed: Should the file saved as a compressed file (using
            LZMA compression as a .xz file)
        """

        data = ET.Element("data")

        def mkdonor(donor: Donor):
            entry = ET.SubElement(data, "entry")
            entry.attrib["donor_id"] = str(int(donor.id))
            try:
                if not donor.age.is_integer():
                    raise KEPDataValidationException(
                        f"Error: Trying to write XML with non-integral age for {donor}"
                    )
                age_text = str(int(donor.age))
                age = ET.SubElement(entry, "dage")
                age.text = age_text
            except KEPDataValidationException:
                pass  # No known age
            try:
                bg_text = str(donor.bloodGroup)
                bg = ET.SubElement(entry, "bloodgroup")
                bg.text = bg_text
            except KEPDataValidationException:
                pass  # No known blood group
            if donor.NDD:
                altruistic = ET.SubElement(entry, "altruistic")
                altruistic.text = "true"
            else:
                sources = ET.SubElement(entry, "sources")
                source = ET.SubElement(sources, "source")
                source.text = donor.recipient.id

            if donor.transplants():
                matches = ET.SubElement(entry, "matches")
                for t in donor.transplants():
                    amatch = ET.SubElement(matches, "match")
                    recip = ET.SubElement(amatch, "recipient")
                    recip.text = t.recipient.id
                    score = ET.SubElement(amatch, "score")
                    # Print integers as actual integers
                    if t.weight.is_integer():
                        score.text = str(int(t.weight))
                    else:
                        score.text = str(t.weight)

        for donor in self.allDonors():
            mkdonor(donor)

        with _getOutFile(filename, compressed) as outfile:
            ET.ElementTree(data).write(outfile, encoding="unicode")

    def writeFileJson(
        self,
        filename: str,
        write_recipients: bool = False,
        compressed: bool = True,
        version: int = 1,
    ) -> None:
        if version == 1:
            return self.writeFileJsonv1(filename, write_recipients, compressed)
        return self.writeFileJsonv2(filename, compressed)

    def writeFileJsonv1(
        self, filename: str, write_recipients: bool = False, compressed: bool = True
    ) -> None:
        """Write the instance to a JSON file, where recipient data (e.g., blood
        types and cPRA of recipients) are included only if the parameter
        write_recipients is True

        :param filename: The name of the file to write
        :param write_recipients: If True, also write the recipient data to the file
        :param compressed: Should the file saved as a compressed file (using
            LZMA compression as a .xz file)
        """

        def mkdonor(donor: Donor):
            result = {
                "dage": donor.age,
                "matches": [
                    {"recipient": int(t.recipient.id), "score": t.weight}
                    for t in donor.transplants()
                ],
            }
            if donor.NDD:
                result["altruistic"] = True
            else:
                result["sources"] = [int(donor.recipient.id)]
            try:
                result["bloodtype"] = str(donor.bloodGroup)
            except KEPDataValidationException:
                # If blood group is not known, don't try to write it
                pass
            if (
                donor.NDD
                and isinstance(self, DynamicInstance)
                and donor.id in self.ndd_arrivals
            ):
                result["arrival"] = self.ndd_arrivals[donor.id]
                result["departure"] = self.ndd_departures[donor.id]
                result["temporary_departures"] = self.ndd_temporary_departures[donor.id]
            return result

        data: dict[str, Any] = {
            str(donor.id): mkdonor(donor) for donor in self.allDonors()
        }
        output: dict[str, Any] = {"data": data}

        def mkrecipient(recipient: Recipient):
            result: dict[str, Union[str, float, list[int]]] = {}
            try:
                result["pra"] = recipient.cPRA
            except KEPDataValidationException:
                # If cPRA is not known, don't try to write it
                pass
            try:
                result["bloodgroup"] = str(recipient.bloodGroup)
            except KEPDataValidationException:
                # If blood group is not known, don't try to write it
                pass
            if (
                isinstance(self, DynamicInstance)
                and recipient.id in self.recipient_arrivals
            ):
                result["arrival"] = self.recipient_arrivals[recipient.id]
                result["departure"] = self.recipient_departures[recipient.id]
                result["temporary_departures"] = self.recipient_temporary_departures[
                    recipient.id
                ]
            return result

        if write_recipients:
            output["recipients"] = {
                str(recipient.id): mkrecipient(recipient)
                for recipient in self.allRecipients()
            }
        if isinstance(self, DynamicInstance):
            output["failing_transplants"] = [
                {"donor": t.donor.id, "recipient": t.recipient.id}
                for t in self.failing_transplants
            ]
        with _getOutFile(filename, compressed) as outfile:
            json.dump(output, outfile)

    def writeFileJsonv2(self, filename: str, compressed: bool = True) -> None:
        """Write the instance to a JSON file using schema 3

        :param filename: The name of the file to write
        :param compressed: Should the file saved as a compressed file (using
            LZMA compression as a .xz file)
        """

        def mkdonor(donor: Donor):
            result: dict[str, Any] = {
                "id": donor.id,
                "outgoing_transplants": [
                    {"recipient": t.recipient.id, "score": t.weight}
                    for t in donor.transplants()
                ],
            }
            if donor.NDD:
                result["paired_recipients"] = []
            else:
                result["paired_recipients"] = [donor.recipient.id]
            try:
                result["age"] = donor.age
            except KEPDataValidationException:
                # If age is not known, don't try to write it
                pass
            try:
                result["bloodtype"] = str(donor.bloodGroup)
            except KEPDataValidationException:
                # If blood group is not known, don't try to write it
                pass
            if (
                donor.NDD
                and isinstance(self, DynamicInstance)
                and donor.id in self.ndd_arrivals
            ):
                result["arrival"] = self.ndd_arrivals[donor.id]
                result["departure"] = self.ndd_departures[donor.id]
                result["temporary_departures"] = self.ndd_temporary_departures[donor.id]
            if donor.property:
                result["properties"] = {
                    key: value for key, value in donor.property.items()
                }
            return result

        donors: dict[str, Any] = {
            donor.id: mkdonor(donor) for donor in self.allDonors()
        }
        output: dict[str, Any] = {
            "schema": 3,
            "donors": donors,
        }

        def mkrecipient(recipient: Recipient):
            result: dict[str, Any] = {
                "id": recipient.id,
            }
            try:
                result["cPRA"] = recipient.cPRA * 100
            except KEPDataValidationException:
                # If cPRA is not known, don't try to write it
                pass
            try:
                result["bloodtype"] = str(recipient.bloodGroup)
            except KEPDataValidationException:
                # If blood group is not known, don't try to write it
                pass
            if (
                isinstance(self, DynamicInstance)
                and recipient.id in self.recipient_arrivals
            ):
                result["arrival"] = self.recipient_arrivals[recipient.id]
                result["departure"] = self.recipient_departures[recipient.id]
                result["temporary_departures"] = self.recipient_temporary_departures[
                    recipient.id
                ]
            if recipient.property:
                result["properties"] = {
                    key: value for key, value in recipient.property.items()
                }
            return result

        output["recipients"] = {
            recipient.id: mkrecipient(recipient) for recipient in self.allRecipients()
        }
        if isinstance(self, DynamicInstance):
            output["failing_transplants"] = [
                {"donor": t.donor.id, "recipient": t.recipient.id}
                for t in self.failing_transplants
            ]
        with _getOutFile(filename, compressed) as outfile:
            json.dump(output, outfile)

    def writeFileYaml(self, filename: str, compressed: bool) -> None:
        """Write the instance to a YAML file

        :param filename: The name of the file to write
        :param compressed: Should the file saved as a compressed file (using
            LZMA compression as a .xz file)
        """

        def mkdonor(donor: Donor):
            result: dict[str, Any] = {
                "matches": [
                    {"recipient_id": t.recipient.id, "score": t.weight}
                    for t in donor.transplants()
                ],
            }
            try:
                result["age"] = donor.age
            except KEPDataValidationException:
                pass  # If we don't know age, we just don't write it
            if donor.NDD:
                result["altruistic"] = True
            else:
                result["recipients"] = [donor.recipient.id]
            try:
                result["bloodtype"] = str(donor.bloodGroup)
            except KEPDataValidationException:
                # If blood group is not known, don't try to write it
                pass
            if (
                donor.NDD
                and isinstance(self, DynamicInstance)
                and donor.id in self.ndd_arrivals
            ):
                result["arrival"] = self.ndd_arrivals[donor.id]
                result["departure"] = self.ndd_departures[donor.id]
                result["temporary_departures"] = self.ndd_temporary_departures[donor.id]
            return result

        donors = {donor.id: mkdonor(donor) for donor in self.allDonors()}
        output: dict[str, Any] = {"schema": 1, "donors": donors}

        def mkrecipient(recipient: Recipient):
            result: dict[str, Union[str, float, list[int]]] = {}
            try:
                result["pra"] = recipient.cPRA
            except KEPDataValidationException:
                # If cPRA is not known, don't try to write it
                pass
            try:
                result["bloodgroup"] = str(recipient.bloodGroup)
            except KEPDataValidationException:
                # If blood group is not known, don't try to write it
                pass
            if (
                isinstance(self, DynamicInstance)
                and recipient.id in self.recipient_arrivals
            ):
                result["arrival"] = self.recipient_arrivals[recipient.id]
                result["departure"] = self.recipient_departures[recipient.id]
                result["temporary_departures"] = self.recipient_temporary_departures[
                    recipient.id
                ]
            return result

        output["recipients"] = {
            recipient.id: mkrecipient(recipient) for recipient in self.allRecipients()
        }
        if isinstance(self, DynamicInstance):
            output["failing_transplants"] = [
                {"donor": t.donor.id, "recipient": t.recipient.id}
                for t in self.failing_transplants
            ]

        yaml = YAML()
        with _getOutFile(filename, compressed) as outfile:
            yaml.dump(output, outfile)


class InstanceSet:
    """A set of instances that can be analysed for statistical properties."""

    def __init__(self, instances: list[Instance]):
        """Constructor for InstanceSet.

        :param instances: The set of instances.
        """
        self._instances = instances

    def donor_details(self) -> pandas.DataFrame:
        """Extract a table of donor properties from this set.

        :return: A pandas DataFrame with the following table headers.
            donor_id
            donor_bloodgroup
            paired_recipient_bloodgroup
            is_ndd
        """
        donor_table = {}
        for instance in self._instances:
            for donor in instance.allDonors():
                donor_table[donor.id] = {
                    "donor_id": donor.id,
                    "donor_bloodgroup": donor.bloodGroup,
                }
                if donor.NDD:
                    donor_table[donor.id].update(
                        {
                            "NDD": True,
                            "paired_recipient_bloodgroup": numpy.nan,
                        }
                    )
                else:
                    donor_table[donor.id].update(
                        {
                            "NDD": False,
                            "paired_recipient_bloodgroup": donor.recipient.bloodGroup,
                        }
                    )
        # Make BloodGroup columns categories, so even if a blood group is not
        # present in a population, it still appears with a count of zero in
        # summary statistics
        bg_category = pandas.CategoricalDtype(
            categories=BloodGroup.all(), ordered=False
        )
        df = pandas.DataFrame(donor_table.values())
        df["donor_bloodgroup"] = df["donor_bloodgroup"].astype(bg_category)
        df["paired_recipient_bloodgroup"] = df["paired_recipient_bloodgroup"].astype(
            bg_category
        )
        return df

    def _calculate_compatibilities(self) -> None:
        """Calculate compatibility chance for each recipient. This generally
        only makes sense if you want to perform statistical analysis on the
        results.
        """
        donors = defaultdict(set)
        compats = defaultdict(set)
        for instance in self._instances:
            for recipient in instance.allRecipients():
                for donor in instance.allDonors():
                    # Don't count paired donors
                    if recipient.pairedWith(donor):
                        continue
                    # Skip ABO incompatible
                    if not donor.bloodGroupCompatible(recipient):
                        continue
                    # This donor appears in the same instance at least once
                    donors[recipient.id].add(donor.id)
                    # Get recipients compatible with this donor, see if current
                    # recipient appears in this list
                    if recipient in [t.recipient for t in donor.transplants()]:
                        compats[recipient.id].add(donor.id)
        for instance in self._instances:
            for recipient in instance.allRecipients():
                if recipient.id not in compats:
                    recipient.compatibilityChance = 0
                else:
                    recipient.compatibilityChance = len(compats[recipient.id]) / len(
                        donors[recipient.id]
                    )

    def recipient_details(self, calculate_compatibility=True) -> pandas.DataFrame:
        """Extract a table of donor properties from this set.

        :param calculate_compatibiltiy: If True (default), this function will
            calculate the compatibility chance for each recipient. Otherwise, each
            recipient must have compatibility chance already determined.
        :return: A pandas DataFrame with the following table headers.
            * recipient_id
            * recipient_bloodgroup
            * cPRA
            * compatibility_chance
            * num_donors
            * has_abo_compatible_donor
        """
        if calculate_compatibility:
            self._calculate_compatibilities()
        recipient_table = {}
        for instance in self._instances:
            for recipient in instance.allRecipients():
                recipient_table[recipient.id] = {
                    "recipient_id": recipient.id,
                    "recipient_bloodgroup": recipient.bloodGroup,
                    "cPRA": recipient.cPRA,
                    "compatibility_chance": recipient.compatibilityChance,
                    "num_donors": len(recipient.donors()),
                    "has_abo_compatible_donor": recipient.hasBloodCompatibleDonor(),
                }
        return pandas.DataFrame(recipient_table.values())

    def __iter__(self):
        return self._instances.__iter__()


Participant = Donor | Recipient
ParticipantType = TypeVar("ParticipantType", Donor, Recipient)


@dataclass
class DynamicInstance(Instance):
    """A dynamic KEP instance, that includes when participants arrive, depart,
    or are ill, as well as which transplants will pass a virtual crossmatch but
    fail a laboratory-based crossmatch.

    :param recipients: The recipients in the instance.
    :param donors: The non-directed donors in the instance.
    :param recipient_arrivals: A mapping from recipient IDs to the period in
        which they arrive
    :param recipient_departures: A mapping from recipient IDs to the period in
        which they depart
    :param recipient_temporary_departures: A mapping from recipient IDs to a list of periods
        in which said recipient is ill.
    :param ndd_arrivals: A mapping from non-directed donor IDs to the period in
        which they arrive
    :param ndd_departures: A mapping from non-directed donor IDs to the period in
        which they depart
    :param ndd_temporary_departures: A mapping from non-directed donor IDs to a list of periods
        in which said donor is ill.
    :param failing_transplants: A list of the transplants which will fail a
        laboratory crossmatch.
    """

    recipient_arrivals: MutableMapping[str, int] = field(default_factory=dict)
    """A mapping from recipient IDs to the period in which they arrive."""
    recipient_departures: MutableMapping[str, int] = field(default_factory=dict)
    """A mapping from recipient IDs to the period in which they depart."""
    recipient_temporary_departures: MutableMapping[str, list[int]] = field(
        default_factory=dict
    )
    """A mapping from recipient IDs to a list of periods in which said
    recipient is ill."""
    ndd_arrivals: MutableMapping[str, int] = field(default_factory=dict)
    """A mapping from non-directed donor IDs to the period in which they
    arrive."""
    ndd_departures: MutableMapping[str, int] = field(default_factory=dict)
    """A mapping from non-directed donor IDs to the period in which they depart."""
    ndd_temporary_departures: MutableMapping[str, list[int]] = field(
        default_factory=dict
    )
    """A mapping from non-directed donor IDs to a list of periods in which said
    donor is ill."""
    failing_transplants: list[Transplant] = field(default_factory=list)
    """A list of the transplants which will fail a laboratory crossmatch."""

    def is_available(self, participant: Donor | Recipient, period: int) -> str:
        """Return either an empty string if the participant is available, or a
        string containing the reason why the participant is not available if
        they are not available.

        :param participant: The participant in question#
        :param period: The period in which we are querying.
        """
        if participant.status == Status.Left:
            return "Left pool"
        if (
            isinstance(participant, Recipient)
            and participant.id in self.recipient_temporary_departures
            and period in self.recipient_temporary_departures[participant.id]
        ):
            return "Temporary departure"
        if (
            isinstance(participant, Donor)
            and participant.id in self.ndd_temporary_departures
            and period in self.ndd_temporary_departures[participant.id]
        ):
            return "Temporary departure"
        return ""
