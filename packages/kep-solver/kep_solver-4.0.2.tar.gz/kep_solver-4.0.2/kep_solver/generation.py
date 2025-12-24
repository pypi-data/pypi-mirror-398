"""Generation of KEP instances."""

from collections.abc import Iterable
import random
from typing import Callable, Optional, Union

import numpy as np
import numpy.typing as npt

from kep_solver.entities import (
    Donor,
    Recipient,
    BloodGroup,
    Instance,
    Transplant,
    ParticipantType,
    DynamicInstance,
)


BloodGroupGeneratorConfig = dict[str, float]


class BloodGroupGenerator:
    """Generates :ref:`Blood groups` based on a given distribution."""

    def __init__(self, dist: dict[BloodGroup, float]):
        """Constructor for BloodGroupGenerator.

        :param dist: A mapping from BloodGroup to the proportion of said blood
          group in a given population. Note that the sum of these proportions,
          across all four blood groups, must equal one.
        """
        self._dist: dict[BloodGroup, float] = dist
        if not abs(sum(self._dist.values()) - 1.0) < 1e-6:
            raise Exception(
                f"Blood group distribution does not sum to one ({sum(dist.values())})"
            )

    def draw(self) -> BloodGroup:
        """Draw a random blood group from the generator.

        :return: A randomly-chosen blood group, chosen with probabilities
          proportional to the distribution given when the generator was
          constructed.
        """
        p = random.random()
        for bt, chance in self._dist.items():
            if p < chance:
                return bt
            p -= chance
        raise Exception("Blood group generation failed")

    def config(self) -> BloodGroupGeneratorConfig:
        """The configuration of this BloodGroupGenerator: a dictionary of
        expected relative proportion of blood group drawn.
        """
        return {str(bg): chance for bg, chance in self._dist.items()}

    @classmethod
    def from_json(cls, json_obj) -> "BloodGroupGenerator":
        """Create a BloodGroupGenerator from a JSON object. The JSON
        object should be a dictionary of key, value pairs where each key is a
        string representing a blood group, and the corresponding value is the
        proportion of people in a given population with that blood group.
        """
        dists: dict[BloodGroup, float]
        try:
            dists = {
                BloodGroup.from_str("O"): json_obj["O"],
                BloodGroup.from_str("A"): json_obj["A"],
                BloodGroup.from_str("B"): json_obj["B"],
                BloodGroup.from_str("AB"): json_obj["AB"],
            }
        except KeyError as e:
            raise Exception(
                f"Parsing JSON for BloodGroupGenerator failed: No blood group {e} proportion given."
            )
        return cls(dists)


DonorCountGeneratorConfig = dict[int, float]


class DonorCountGenerator:
    def __init__(self, dist: dict[int, float]):
        """Constructor for DonorCountGenerator.

        :param dist: A mapping from a potential number of donors, to the
            expected likelihood of a recipient being paired with that many donors.
            Note that the sum of these proportions must equal one.
        """
        if not abs(sum(dist.values()) - 1.0) < 1e-6:
            raise Exception(f"Distribution does not sum to one ({sum(dist.values())})")
        self._dist: dict[int, float] = dist

    def draw(self) -> int:
        """Draw a random random number of donors."""
        p = random.random()
        for num, chance in self._dist.items():
            if p < chance:
                return num
            p -= chance
        raise Exception("Donor count generation failed")

    def config(self) -> DonorCountGeneratorConfig:
        """The configuration of this DonorCountGenerator: a dictionary of
        expected relative proportion of recipients paired with the given number
        of donors.
        """
        return self._dist

    @classmethod
    def from_json(cls, json_obj) -> "DonorCountGenerator":
        """Create a DonorCountGenerator from a JSON object. The JSON
        object should be a dictionary of key, value pairs where each key is a
        is an integer, and the corresponding value is the proportion of recipients
        with that number of donors.
        """
        num = 1
        dists = {}
        while str(num) in json_obj:
            dists[num] = json_obj[str(num)]
            num += 1
        if not dists:
            raise Exception(
                "Parsing JSON for DonorCountGenerator failed: No donor counts found."
            )
        return cls(dists)


DonorGeneratorConfig = dict[str, BloodGroupGeneratorConfig]


class DonorGenerator:
    """Generates Donors. Note that it is possible to configure such a generator
    so that the blood group is drawn from different distributions depending on
    the blood group of a paired recipient."""

    def __init__(
        self,
        bloodgroup_generator: BloodGroupGenerator,
        *,
        recipient_o_generator: Optional[BloodGroupGenerator] = None,
        recipient_a_generator: Optional[BloodGroupGenerator] = None,
        recipient_b_generator: Optional[BloodGroupGenerator] = None,
        recipient_ab_generator: Optional[BloodGroupGenerator] = None,
    ):
        """Construct a DonorGenerator object. Note that the donor distributions
        that depend on the recipient BloodGroup must be specified by parameter
        name to avoid mis-matching."""
        self._bloodgroup_generator = bloodgroup_generator
        self._by_recipient_generators = {
            BloodGroup.O: recipient_o_generator,
            BloodGroup.A: recipient_a_generator,
            BloodGroup.B: recipient_b_generator,
            BloodGroup.AB: recipient_ab_generator,
        }

    def draw(self, name: str, recipient_bg: Optional[BloodGroup] = None) -> Donor:
        """Draw a donor from this generator.

        :param name: A name (or ID) for this donor
        :param recipient_bg: The blood group of the paired recipient. This may
            be used to adapt the distribution of donor blood group based on the
            blood group of the paired recipient.
        """
        d = Donor(id=name)
        if recipient_bg and self._by_recipient_generators[recipient_bg] is not None:
            gen = self._by_recipient_generators[recipient_bg]
            if gen is None:
                raise Exception(
                    f"Tried to draw a donor blood group with recipient blood group {recipient_bg} but no such distribution has been specified for this generator."
                )
            d.bloodGroup = gen.draw()
        else:
            d.bloodGroup = self._bloodgroup_generator.draw()
        return d

    def config(self) -> DonorGeneratorConfig:
        """Returns the configuration of this DonorGenerator.

        :return: a dictionary with keys that are either "Generic", or one of "O",
            "A", "B", or "AB". The entry for each key gives the distribution of
            BloodGroup for donors, across all donors if the key is "Generic" or
            otherwise dependent on the recipient BloodGroup.
        """
        res = {"Generic": self._bloodgroup_generator.config()}
        for bg in BloodGroup.all():
            if bg in self._by_recipient_generators:
                gen = self._by_recipient_generators[bg]
                if gen is not None:
                    res[str(bg)] = gen.config()
        return res

    @classmethod
    def from_json(cls, json_obj) -> "DonorGenerator":
        """Create a DonorGenerator from a JSON object. The JSON
        object should be a dictionary of key, value pairs where each key is a
        a string (one of "Generic", "O", "A", "B", or "AB") and the
        corresponding value is the configuration of a BloodGroupGenerator
        that generates blood groups. The "Generic" blood group is required, but
        the other generators are optional.
        """
        try:
            generic = BloodGroupGenerator.from_json(json_obj["Generic"])
        except KeyError:
            raise Exception(
                "Could not find Generic BloodGroup distribution for DonorGenerator"
            )
        dists: dict[BloodGroup, Optional[BloodGroupGenerator]] = {
            bg: None for bg in BloodGroup.all()
        }
        for bg in BloodGroup.all():
            if str(bg) in json_obj and str(bg) is not None:
                dists[bg] = BloodGroupGenerator.from_json(json_obj[str(bg)])
        return cls(
            generic,
            recipient_o_generator=dists[BloodGroup.O],
            recipient_a_generator=dists[BloodGroup.A],
            recipient_b_generator=dists[BloodGroup.B],
            recipient_ab_generator=dists[BloodGroup.AB],
        )


_bandsType = dict[tuple[float, float], float]
"""_bands represents a distribution of a floating point number."""
FloatGeneratorConfig = list[list[Union[list[float], float]]]


def _parseBandString(string: str) -> _bandsType:
    """Takes a string and turns it into a set of bands representing the
    distribution of a floating point number.

    This function exists for compatibility with other software.
    """
    bands: _bandsType = dict()
    for line in string.split("\n"):
        tokens = line.split()
        if len(tokens) == 2:
            prob = float(tokens[0])
            value = float(tokens[1])
            bands[(value, value)] = prob
        elif len(tokens) == 3:
            prob = float(tokens[0])
            low = float(tokens[1])
            high = float(tokens[2])
            bands[(low, high)] = prob
    return bands


class FloatGenerator:
    """A FloatGenerator generates floating point values in the range [0, 1]
    based on a pre-defined distribution amongst a population. In
    particular, the range [0, 1] is split up into bands, each of which is
    either a singular value or a range of values. Each such band has an
    associated probability of occuring amongst the designated population.

    These can represent either distributions of cPRA amongst recipients, or
    alternatively the distribution of compatibility chance amongst a
    population.
    """

    # Note that we force arguments to be keyworded here, as we are passing in 3
    # similar variables and we really don't want to pass in the wrong one in
    # the wrong position.
    def __init__(
        self, *, bands: Optional[_bandsType] = None, bandString: Optional[str] = None
    ):
        """Construct a FloatGenerator object.

        Note that exactly one of bands or bandStrings must be passed to the
        constructor, and it must be passed by parameter name

        :param bands: A set of bands.
        :param bandString: A string representing a set of bands. This parameter
            exists for compatibility with other software.
        """
        self._bands: _bandsType
        if bands is not None:
            if bandString is not None:
                raise Exception(
                    "Exactly one of bandString or bands must be given to a FloatGenerator constructor"
                )
            self._bands = bands
        else:
            if bandString is None:
                raise Exception(
                    "Exactly one of bandString or bands must be given to a FloatGenerator constructor"
                )
            self._bands = _parseBandString(bandString)
        sum_prob = sum(self._bands.values())
        if not abs(sum_prob - 1.0) < 1e-6:
            raise Exception(
                f"FloatGenerator probabilities ({sum_prob}) do not sum to 1.0"
            )
        # Validate that there is no overlap.
        ranges = [(low, high) for (low, high) in self._bands.keys()]
        ranges.sort(key=lambda x: x[0])
        for index, (low, high) in enumerate(ranges):
            if low > high:
                raise Exception(
                    f"Error creating FloatGenerator: invalid range [{low}, {high}) is empty"
                )
            if index < len(ranges) - 1:
                next_range = ranges[index + 1]
                if high > next_range[0]:
                    raise Exception(
                        f"Error creating FloatGenerator: range overlap with [{low}, {high}) and [{next_range[0]}, {next_range[1]}"
                    )

    def draw(self) -> float:
        """Draw a value from this set of bands. The band is chosen based
        on the probability of each band occuring using a uniform distribution.
        If the band is a singular value, then that value is returned, otherwise
        a value in the band is chosen uniformly at random and returned.

        Note that in particular, the returned value will lie in the range
        [0, 1].

        :return: a floating point value in the range [0, 1]
        """
        p = random.random()
        for entry, chance in self._bands.items():
            if p < chance:
                low, high = entry
                # Since the last band has a strict upper bound, it will be above
                # 1.0 by a small amount, so we cap our value at 1.0
                return min(1.0, low + random.random() * (high - low))
            p -= chance
        raise Exception("FloatBands generation failed")

    def config(self) -> FloatGeneratorConfig:
        """Returns the configuration of this FloatGenerator.

        :return: a list of the bands that define this FloatGenerator. Each
            list must have two elements. The first is a list containing either [low,
            high] values or one exact [value], and the second is the probability,
            such that the chance of the cPRA being either exactly value, or drawn
            uniformly between low and high, is given by said probability.
        """
        res: list[list[Union[list[float], float]]] = []
        for entry, chance in self._bands.items():
            low, high = entry
            res.append([[low, high], chance])
        return res

    @classmethod
    def from_json(cls, json_obj) -> "FloatGenerator":
        """Create a FloatGenerator from a JSON object. The JSON object
        should contain a list of bands, where each band is itself a list
        containing two items. The first of these is another list with either one
        or two items. If it contains only one item, this band only corresponds
        to one floating point value, but if it contains two, it corresponds to
        the range between the first and second item. The second item in each
        band is the probability that this band is selected.
        """
        bands = {}
        for band in json_obj:
            entry, chance = band
            try:
                low, high = entry
            except (
                ValueError,
                TypeError,
            ):  # Only one value in list, must be both low and high value
                low = entry
                high = entry
            bands[(low, high)] = chance
        return cls(bands=bands)


CompatibilityChanceGeneratorConfig = list[tuple[float, float, FloatGeneratorConfig]]


class CompatibilityChanceGenerator:
    """This class represents a generator for :ref:`compatibility chance`.
    The distributions can be distinct for different cPRA values.
    """

    def __init__(
        self,
        *,
        dists: list[
            tuple[float, float, Union[FloatGenerator, Callable[[float], float]]]
        ],
    ):
        """Constructor for CompatibilityChanceGenerator.

        :param dists: A set of distributions of compatibility chance. Each
            distribution is a tuple (low, high, generator) where low and high are
            floating values such that if the cPRA is in the range [low, high)
            (i.e., cPRA >= low and cPRA < high), generator will be used to
            generate compatibility chance. Generator itself is either a
            FloatGenerator object, or a function that takes as input a cPRA
            value and returns a corresponding compatibility chance. Note that
            there must be one, and exactly one, distribution to cover each cPRA
            in the range [0, 1]. In particular, since the upper range of an
            individual distribution has a strict upper bound, it must have an
            upper limit strictly above 1.0.
        """
        # Validate that every number in [0, 1] is included somewhere, and
        # that there is no overlap.
        ranges = [(low, high) for (low, high, _) in dists]
        ranges.sort(key=lambda x: x[0])
        if ranges[0][0] != 0:
            raise Exception(
                "Error creating CompatibilityChanceGenerator: Lowest range does not include 0"
            )
        if ranges[-1][1] <= 1.0:
            raise Exception(
                "Error creating CompatibilityChanceGenerator: Highest range does not include 1 (upper limit must be > 1.0)"
            )
        for index, (low, high) in enumerate(ranges):
            if low > high:
                raise Exception(
                    f"Error creating CompatibilityChanceGenerator: invalid range [{low}, {high}) is empty"
                )
            if index < len(ranges) - 1:
                next_range = ranges[index + 1]
                if high != next_range[0]:
                    raise Exception(
                        f"Error creating CompatibilityChanceGenerator: bands not sequential [{low}, {high}) and [{next_range[0]}, {next_range[1]})"
                    )
        self._dists: list[
            tuple[float, float, Union[FloatGenerator, Callable[[float], float]]]
        ] = dists

    def draw(self, pra) -> float:
        """Draw a compatibility chance."""
        for low, high, gen in self._dists:
            if low <= pra and pra < high:
                if isinstance(gen, FloatGenerator):
                    return gen.draw()
                else:
                    return gen(pra)
        raise Exception("Compatibility chance generation failed")

    def config(self) -> CompatibilityChanceGeneratorConfig:
        """Returns the configuration of this CompatibilityChanceGenerator.

        Note that this will fail if this CompatibilityChanceGenerator uses a
        function.

        :return: a list of [low, high, generator] lists such that if the recipient
            cPRA is between low and high, then generator is a configuration for a
            FloatGenerator that will generate the compatibility chance for this
            recipient.
        """
        res: list[tuple[float, float, FloatGeneratorConfig]] = []
        for low, high, band in self._dists:
            if not isinstance(band, FloatGenerator):
                raise Exception(
                    "Cannot get configuration for a CompatibilityChanceGenerator that uses a function."
                )
            res.append((low, high, band.config()))
        return res

    @classmethod
    def from_json(cls, json_obj) -> "CompatibilityChanceGenerator":
        """Create a CompatibilityChanceGenerator from a JSON object. The JSON
        object should be a list of (low, high, config) tuples such that if the
        recipient cPRA is between low and high, then config is either the
        configuration for a FloatGenerator that will generate the compatibility
        chance for this recipient, or a function that will generate the
        compatibility chance for this recipient.

        Currently, only linear functions can loaded from JSON.
        """
        dists: list[
            tuple[float, float, Union[FloatGenerator, Callable[[float], float]]]
        ] = []
        for low, high, config in json_obj:
            if "function" in config:
                specification = config["function"]
                function_type = specification["type"]
                if function_type == "linear":
                    dists.append(
                        (
                            low,
                            high,
                            lambda x: specification["offset"]
                            + x * specification["coefficient"],
                        )
                    )
                else:
                    # Didn't recognise function type
                    raise Exception(
                        f"Unknown function ({function_type}) specified for function for CompatibilityChanceGenerator"
                    )
            else:
                dists.append((low, high, FloatGenerator.from_json(config)))
        return cls(dists=dists)


CPRAGeneratorConfig = dict[str, FloatGeneratorConfig]


class CPRAGenerator:
    """Generates :ref:`cPRA` values for a recipient based upon the configured
    distribution of cPRA. This can be configured either with one single
    distribution of cPRA for all recipients, or two distinct distributions
    dependent on whether the recipient has a bloodgroup compatible donor."""

    # Note that we force arguments to be keyworded here, as we are passing in 3
    # similar variables and we really don't want to pass in the wrong one in
    # the wrong position.
    def __init__(
        self,
        *,
        generic: Optional[FloatGenerator] = None,
        compatible_generator: Optional[FloatGenerator] = None,
        incompatible_generator: Optional[FloatGenerator] = None,
    ):
        """Construct a generator object from some FloatGenerator objects.
        To construct, either the generic generator (which will be used for all
        requests to draw a CPRA value) must be passed in, or both a
        compatible_generator and an incompatible_generator must be passed in.
        This allows the use of two distinct distributions of cPRA values - one
        for those recipients who do have an ABO compatible donor, and a second
        for those that don't.

        :param generic: A generator of cPRA to be used for all recipients
        :param compatible_generator: A generator of cPRA to be used for
            recipients with an ABO compatible donor
        :param incompatible_generator: A generator of cPRA to be used for
            recipients without an ABO compatible donor
        """
        if (
            generic is None
            and compatible_generator is None
            and incompatible_generator is None
        ):
            raise Exception(
                "A cPRA generator needs at least one distribution of cPRA values to function."
            )
        if generic is None and (
            compatible_generator is None or incompatible_generator is None
        ):
            raise Exception(
                "If generic is not given, then both of compatible_generator and incompatible_generator must be given."
            )
        if generic is not None and (
            compatible_generator is not None or incompatible_generator is not None
        ):
            raise Exception(
                "If generic is given, then neither of compatible_generator nor incompatible_generator can be given."
            )

        self._generic: Optional[FloatGenerator] = generic
        self._compatible_generator: Optional[FloatGenerator] = compatible_generator
        self._incompatible_generator: Optional[FloatGenerator] = incompatible_generator

    def draw(self, hasABOCompatibleDonor: Optional[bool] = None) -> float:
        """Draws a cPRA value for a given recipient, depending on whether the
        recipient has an ABO compatible donor.

        :param hasABOCompatibleDonor: True if and only if the target recipient
            has a ABO-compatible donor. Can only be left as None if a generic cPRA
            band has been provided to the generator in the initialiser.
        :return: a cPRA value
        """
        if self._generic is not None:
            return self._generic.draw()
        if hasABOCompatibleDonor is None:
            raise Exception(
                "Tried to draw cPRA without either specifying ABO compatible donor or giving generic distribution"
            )
        if hasABOCompatibleDonor:
            if self._compatible_generator is None:
                raise Exception(
                    "Tried to draw cPRA for ABO compatible donor but without giving specific distribution"
                )
            return self._compatible_generator.draw()
        if self._incompatible_generator is None:
            raise Exception(
                "Tried to draw cPRA for ABO incompatible donor but without giving specific distribution"
            )
        return self._incompatible_generator.draw()

    def config(self) -> dict[str, FloatGeneratorConfig]:
        """Returns the configuration of this CPRAGenerator.

        :return: a dictionary with a subset of ["Generic", "Compatible", and
            "Incompatible"] as keys, such that the value for each is a
            FloatGenerator configuration that corresponds to the distribution
            of cPRA amongst all recipients, recipients with an ABO compatible
            donor, and recipients without an ABO compatible donor respectively.
            Note that the dictionary will either only contain "Generic", or will
            only contain "Compatible" and "Incompatible"
        """
        res = {}
        if self._generic is not None:
            res["Generic"] = self._generic.config()
            return res
        assert self._incompatible_generator is not None
        assert self._compatible_generator is not None
        res["Incompatible"] = self._incompatible_generator.config()
        res["Compatible"] = self._compatible_generator.config()
        return res

    @classmethod
    def from_json(cls, json_obj) -> "CPRAGenerator":
        """Create a CPRAGenerator from a JSON object. The JSON object should be
        a list of (low, high, bands) tuples such that if the recipient cPRA is
        between low and high, then bands is a FloatGenerator that will
        generate the compatibility chance for this recipient.
        """
        if "Generic" in json_obj:
            generic = FloatGenerator.from_json(json_obj["Generic"])
            return cls(generic=generic)
        incompatible_generator = FloatGenerator.from_json(json_obj["Incompatible"])
        compatible_generator = FloatGenerator.from_json(json_obj["Compatible"])
        return cls(
            compatible_generator=compatible_generator,
            incompatible_generator=incompatible_generator,
        )


def _donor_id_gen(recipient: Recipient) -> str:
    """A function that takes as input a recipient with identifier "RX"
    and returns the string "RX_DY" where Y is one plus the current number of donors this recipient has.

    This function is the default function used when generating donors for a recipient.
    """
    return f"{recipient.id}_D{len(recipient.donors())+1}"


RecipientGeneratorConfig = dict[
    str,
    Union[
        BloodGroupGeneratorConfig,
        DonorCountGeneratorConfig,
        DonorGeneratorConfig,
        CPRAGeneratorConfig,
        CompatibilityChanceGeneratorConfig,
    ],
]


class RecipientGenerator:
    """A generator for recipients. This class will generate a blood group, an
    integer N such that this recipient will have N donors, the N donors
    themselves, as well as both the cPRA and compatibility chance of a
    recipient.
    """

    def __init__(
        self,
        recipient_bloodgroup_generator: BloodGroupGenerator,
        donor_count_generator: DonorCountGenerator,
        donor_generator: DonorGenerator,
        cpra_generator: CPRAGenerator,
        compatibility_chance_generator: CompatibilityChanceGenerator,
    ):
        """Constructs a RecipientGenerator.

        :param recipient_bloodgroup_generator: A generator for the blood group
            for recipients
        :param donor_count_generator: A generator for number of donors a
            recipient is paired with
        :param donor_generator: A donor generator
        :param cpra_generator: A cPRA generator
        :param compatibility_chance_generator: A generator for a recipient's
            chance of compatibility
        """
        self._recipient_bloodgroup_generator: BloodGroupGenerator = (
            recipient_bloodgroup_generator
        )
        self._donor_count_generator: DonorCountGenerator = donor_count_generator
        self._donor_generator: DonorGenerator = donor_generator
        self._cpra_generator: CPRAGenerator = cpra_generator
        self._compatibility_chance_generator: CompatibilityChanceGenerator = (
            compatibility_chance_generator
        )

    def draw(
        self, id_: str, donor_id_function: Callable[[Recipient], str] = _donor_id_gen
    ) -> Recipient:
        """Generate a Recipient.

        :param id_: An identifier for this Recipient.
        :param donor_id_function: A function that takes as input this recipient,
            and returns an identifier for the next donor for this recipient. The
            default is, given a Recipient with identifier "RX", to use the
            identifier "RX_DY" where Y is an integer that starts at 1 and increases
            for additional donors.
        """
        r = Recipient(id=id_)
        r.bloodGroup = self._recipient_bloodgroup_generator.draw()
        donorCount = self._donor_count_generator.draw()
        for _ in range(donorCount):
            d = self._donor_generator.draw(donor_id_function(r), r.bloodGroup)
            d.recipient = r
            r.addDonor(d)
        r.cPRA = self._cpra_generator.draw(r.hasBloodCompatibleDonor())
        r.compatibilityChance = self._compatibility_chance_generator.draw(r.cPRA)
        return r

    def config(self) -> RecipientGeneratorConfig:
        """Returns the configuration of this RecipientGenerator.

        :return: a dictionary with the following keys and corresponding
            configurations for the respective generators:
            * RecipientBloodGroupGenerator
            * DonorCountGenerator
            * DonorGenerator
            * CPRAGenerator
            * CompatibilityChanceGenerator
        """
        return {
            "RecipientBloodGroupGenerator": self._recipient_bloodgroup_generator.config(),
            "DonorCountGenerator": self._donor_count_generator.config(),
            "DonorGenerator": self._donor_generator.config(),
            "CPRAGenerator": self._cpra_generator.config(),
            "CompatibilityChanceGenerator": self._compatibility_chance_generator.config(),
        }

    @classmethod
    def from_json(cls, json_obj) -> "RecipientGenerator":
        """Create a RecipientGenerator from a JSON object.
        The JSON object should be a dictionary with the following keys
        containing corresponding configurations for the respective generators:
        * RecipientBloodGroupGenerator
        * DonorCountGenerator
        * DonorGenerator
        * CPRAGenerator
        * CompatibilityChanceGenerator
        """
        return cls(
            recipient_bloodgroup_generator=BloodGroupGenerator.from_json(
                json_obj["RecipientBloodGroupGenerator"]
            ),
            donor_count_generator=DonorCountGenerator.from_json(
                json_obj["DonorCountGenerator"]
            ),
            donor_generator=DonorGenerator.from_json(json_obj["DonorGenerator"]),
            cpra_generator=CPRAGenerator.from_json(json_obj["CPRAGenerator"]),
            compatibility_chance_generator=CompatibilityChanceGenerator.from_json(
                json_obj["CompatibilityChanceGenerator"]
            ),
        )


def _defaultWeight(donor: Donor, recipient: Recipient) -> float:
    """A default function to determine the weight (or score) of a transplant,
    given the donor and recipient involved. It just returns 1.0 for any
    transplant.

    :param donor: The donor who is to donate a kidney
    :param recipient: The recipient of said kidney.
    """
    return 1.0


InstanceGeneratorConfig = dict[
    str, Union[RecipientGeneratorConfig, BloodGroupGeneratorConfig]
]


def _recip_id_gen(num: int) -> str:
    """A function that takes as input a number X, and returns the string "RX".

    This function is the default function used when generating IDs for recipients.

    :param num: The number (numerical index) of a recipient to which we are
        assigning a string ID.
    """
    return f"R{num}"


def _ndd_id_gen(num: int) -> str:
    """A function that takes as input a number X, and returns the string "NDDX".

    This function is the default function used when generating IDs for
    non-directed donors.

    :param num: The number (numerical index) of a non-directed donor to which we
        are assigning a string ID.
    """
    return f"NDD{num}"


class InstanceGenerator:
    """A class for generating Instances. Uses a RecipientGenerator to generate
    Recipients, and also takes a BloodGroupGenerator that can be used to
    generate non-directed donors.
    """

    def __init__(
        self,
        recipient_generator: RecipientGenerator,
        ndd_bloodgroup_generator: Optional[BloodGroupGenerator] = None,
    ):
        """Constructor for InstanceGenerator.

        :param recipient_generator: The RecipientGenerator to use
        :param ndd_bloodgroup_generator: The BloodGroupGenerator to use for
            non-directed donors.
        """
        self._recipient_generator: RecipientGenerator = recipient_generator
        self._ndd_bloodgroup_generator = ndd_bloodgroup_generator

    def draw(
        self,
        numRecipients: int,
        numNonDirectedDonors: int = 0,
        *,
        weightFn: Callable[[Donor, Recipient], float] = _defaultWeight,
        donor_id_function: Callable[[Recipient], str] = _donor_id_gen,
        recipient_id_function: Callable[[int], str] = _recip_id_gen,
        ndd_id_function: Callable[[int], str] = _ndd_id_gen,
    ) -> Instance:
        """Create a random instance with the given number of recipients and
        non-directed donors. Note that the number of directed donors is
        determined through the RecipientGenerator as it decides how many donors
        to pair with each recipient.

        :param numRecipients: The number of recipients to generate.
        :param numNonDirectedDonors: The number of non-directed donors to generate.
        :param weightFn: A function that takes as input a Donor and a Recipient
            (not paired), and returns the score that should be used for a potential
            transplant between the Donor and Recipient. The default is to give each
            transplant a score of 1.0.
        """
        i = Instance()
        recips = [
            self._recipient_generator.draw(
                recipient_id_function(num), donor_id_function
            )
            for num in range(numRecipients)
        ]
        for r in recips:
            # This also adds corresponding donors
            i.addRecipient(r)
        if self._ndd_bloodgroup_generator is None:
            if numNonDirectedDonors:
                raise Exception(
                    "Tried to generate non-directed donor without knowing blood group distribution of non-directed donors."
                )
        else:
            for num in range(numNonDirectedDonors):
                donor = Donor(ndd_id_function(num))
                donor.NDD = True
                donor.bloodGroup = self._ndd_bloodgroup_generator.draw()
                i.addDonor(donor)

        # Generate transplants
        for recip in i.allRecipients():
            for donor in i.allDonors():
                if not recip.pairedWith(donor):
                    if donor.bloodGroupCompatible(recip):
                        if random.random() <= recip.compatibilityChance:
                            t = Transplant(donor, recip, weightFn(donor, recip))
                            i.addTransplant(t)
        return i

    def config(self) -> InstanceGeneratorConfig:
        """Returns the configuration of this InstanceGenerator.

        :return: a dictionary with the following keys and corresponding
            configurations for the following generators:
            * RecipientGenerator
            * NDDBloodGroupGenerator
        """
        res: InstanceGeneratorConfig = {
            "RecipientGenerator": self._recipient_generator.config()
        }
        if self._ndd_bloodgroup_generator is not None:
            res["NDDBloodGroupGenerator"] = self._ndd_bloodgroup_generator.config()
        return res

    @classmethod
    def from_json(cls, json_obj) -> "InstanceGenerator":
        """Create a RecipientGenerator from a JSON object.
        The JSON object should be a dictionary with the following keys
        containing corresponding configurations for the following generators:
        * RecipientGenerator
        * NDDBloodGroupGenerator
        """
        return cls(
            recipient_generator=RecipientGenerator.from_json(
                json_obj["RecipientGenerator"]
            ),
            ndd_bloodgroup_generator=BloodGroupGenerator.from_json(
                json_obj["NDDBloodGroupGenerator"]
            ),
        )


class DynamicGenerator:
    """A generator of dynamic instances. These are instances that also include
    details on arrival and departure rates and temporary departure periods for
    participants, as well as a list of transplants that will have a positive
    laboratory crossmatch. Note that periods are arbitary, the user can think
    of each period as a week, or a month, or any suitable time period.
    """

    def __init__(
        self,
        recipient_arrival_function: Callable[[int], list[int]],
        recipient_attrition_function: Callable[[Recipient], float],
        recipient_temporary_departure_function: Callable[[Recipient, int], float],
        recipient_positive_crossmatch_function: Callable[[Recipient, Donor], bool],
        ndd_arrival_function: Callable[[int], list[int]],
        ndd_attrition_function: Callable[[Donor], float],
        ndd_temporary_departure_function: Callable[[Donor, int], float],
        instance_generator: InstanceGenerator | None = None,
    ):
        """Create a dynamic generator.

        :param recipient_arrival_function: A function that takes as input the
            number of periods, and returns a list of integers of that length
            such that the x'th element in that list contains the number of
            recipients arriving during the x'th period.
        :param recipient_attrition_function: A function that takes a Recipient
            and returns the chance that the given recipient will leave in any
            period.
        :param recipient_temporary_departure_function: A function that takes a
            Recipient and the length of their current temporary departure and
            returns the chance of this recipient being ill in any period
        :param recipient_positive_crossmatch_function: A function that takes as
            input a recipient and a donor, and returns the chance of a positive
            laboratory crossmatch between the recipient and donor.
        :param ndd_arrival_function: A function that takes as input the number
            of periods, and returns a list of integers of that length such that
            the x'th element in that list contains the number of non-directed
            donors arriving during the x'th period.
        :param ndd_attrition_function: A function that takes a non-directed
            donor and the length of their current temporary departure and
            returns the chance that this donor will leave in any period.
        :param recipient_temporary_departure_function: A function that takes a
            non-directed donor and returns the chance of this donor being ill in
            any period
        :param instance_generator: (Optional) An InstanceGenerator for static
            instances. If provided, this generator will be used to generate the
            actual donors, recipients, and transplants. If not provided, each
            call to draw() must also include a static Instance.
        """
        self._recipient_arrival_function = recipient_arrival_function
        self._recipient_attrition_function = recipient_attrition_function
        self._recipient_temporary_departure_function = (
            recipient_temporary_departure_function
        )
        self._recipient_positive_crossmatch_function = (
            recipient_positive_crossmatch_function
        )
        self._ndd_arrival_function = ndd_arrival_function
        self._ndd_attrition_function = ndd_attrition_function
        self._ndd_temporary_departure_function = ndd_temporary_departure_function
        self._instance_generator = instance_generator

    def _gen_participants(
        self,
        participants: Iterable[ParticipantType],
        arrival_counts: list[int],
        temporary_departure_function: Callable[[ParticipantType, int], float],
        attrition_function: Callable[[ParticipantType], float],
    ) -> tuple[dict[str, int], dict[str, int], dict[str, list[int]]]:
        """Generate participant information - in particular, arrivals, departures, and temporary departure periods.
            Temporary departures are often (but not always) due to illness, and
            the temporary departure function takes as input both the
            participant and the length of any current temporary departure.

        :param participants: The participants for whome we are generating information.
        :param arrival_counts: How many people arrive in each period
        :param temporary_departure_function: A function that takes as input a participant, and returns the chance that they are ill in any given period.
        """
        periods = len(arrival_counts)
        temporary_departures: dict[str, list[int]] = {}
        arrivals: dict[str, int] = {}
        departures: dict[str, int] = {}

        def _get_temporary_departure_departure(
            participant: ParticipantType,
            temporary_departure_function: Callable[[ParticipantType, int], float],
            attrition_function: Callable[[ParticipantType], float],
            arrival: int,
        ) -> tuple[list[int], int]:
            """Determine when the given participant arrives, leaves, and has to
            temporarily leave the programme. Temporary departures are often
            (but not always) due to illness, and the temporary departure
            function takes as input both the participant and the length of any
            current temporary departure.

            :param participant: The participant in question
            :param temporary_departure_function: A function that takes as input a
                participant, and the length of their current temporary
                departure, and returns the chance they are ill in any given
                period.
            :param attrition_function: A function that takes as input a
                participant, and returns the chance that they leave in a given
                period.
            :param arrival: The period in which this participant arrives
            :return: A list of periods in which the participant is ill, and the period in which they leave the programme.
            """
            # Everyone leaves after last period
            departure = periods + 1
            temporary_departures: list[int] = []
            current_departure_length = 0
            for r_period in range(arrival + 1, periods):
                if np.random.random() < temporary_departure_function(
                    participant, current_departure_length
                ):
                    temporary_departures.append(r_period)
                    current_departure_length += 1
                else:
                    current_departure_length = 0
                if np.random.random() < attrition_function(participant):
                    departure = r_period
                    break
            return temporary_departures, departure

        participants_iter = iter(participants)
        for period, count in enumerate(arrival_counts):
            for _ in range(count):
                try:
                    participant = next(participants_iter)
                except StopIteration:
                    # No one left to add
                    return arrivals, departures, temporary_departures
                # Arriving at this period
                arrivals[participant.id] = period
                temporary_departures[participant.id], departures[participant.id] = (
                    _get_temporary_departure_departure(
                        participant,
                        temporary_departure_function,
                        attrition_function,
                        arrival=period,
                    )
                )
        return arrivals, departures, temporary_departures

    def generate(
        self,
        periods: int,
        instance: Instance | None = None,
    ) -> DynamicInstance:
        """Generate a dynamic instance. A dynamic instance is a regular
        instance that also includes information on when recipients and
        non-directed donors arrive, leave, or are ill. Directed (paired) donors
        are assumed to always be present when their recipient is present.

        :param periods: For how many periods will the dynamic simulator run
        :param instance: The (regular) Instance in question. If not provided,
            the DynamicGenerator will attempt to use its own internal
            InstanceGenerator.
        :return: A dynamic instance
        """
        # work out how many recipients and ndds per period using poisson
        recip_arrival_counts = self._recipient_arrival_function(periods)
        ndd_arrival_counts = self._ndd_arrival_function(periods)
        if not instance:
            if self._instance_generator is None:
                raise Exception(
                    "Tried to generate random dynamic instance without specifying "
                    "a regular instance or regular instance generator."
                )
            instance = self._instance_generator.draw(
                sum(recip_arrival_counts),
                sum(ndd_arrival_counts),
            )
        dynamic_instance = DynamicInstance(
            recipients=instance.recipients,
            donors=instance.donors,
        )
        # Work out when recipients leave, and when they are ill
        recipient_arrivals, recipient_departures, recipient_temporary_departures = (
            self._gen_participants(
                dynamic_instance.allRecipients(),
                recip_arrival_counts,
                self._recipient_temporary_departure_function,
                self._recipient_attrition_function,
            )
        )
        dynamic_instance.recipient_arrivals = recipient_arrivals
        dynamic_instance.recipient_departures = recipient_departures
        dynamic_instance.recipient_temporary_departures = recipient_temporary_departures
        # Work out when NDDs leave, and when they are ill
        ndd_arrivals, ndd_departures, ndd_temporary_departures = self._gen_participants(
            instance.allNDDs(),
            ndd_arrival_counts,
            self._ndd_temporary_departure_function,
            self._ndd_attrition_function,
        )
        dynamic_instance.ndd_arrivals = ndd_arrivals
        dynamic_instance.ndd_departures = ndd_departures
        dynamic_instance.ndd_temporary_departures = ndd_temporary_departures
        # Now work out failing transplants
        dynamic_instance.failing_transplants = [
            t
            for t in instance.transplants
            if self._recipient_positive_crossmatch_function(t.recipient, t.donor)
        ]
        return dynamic_instance
