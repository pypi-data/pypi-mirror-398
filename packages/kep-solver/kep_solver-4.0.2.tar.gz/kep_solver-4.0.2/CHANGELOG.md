# Changelog

## [Unreleased]

## [4.0.2]

- Add `nWayExchanges` objective. This constraint counts the number of cycles or chains
    of a given length, as a minimisation when included in the objective.
- [BUGFIX] Fix reading of v3 JSON files

## [4.0.1]

- Add `extra_constraints` to Programme as well.
- Add `nWayCycles` objective. This constraint counts number of cycles of a given length,
    as a minimisation when included in the objective.
- Add `extra_constraints` to models. This allows a user to add objectives as constraints to
    a model outside of what is required under normal circumstances. For instance, the
    user can add a constraint to say "no more than 2 three-way exchanges".

## [4.0.0]

- Add ability to save dynamic simulation outputs directly to a standard format
- Turn `DynamicSimulation.programme` into `programme_factory`, a function that takes as
    input the period, the current instance, and whether this is a programme to find a
    recourse option, and returns the appropriate Programme in each case.
- Turn `DynamicSimulation.allow_bridge_donors` into `would_be_bridge_donor`. This
    is a function that takes as input a Donor, and returns True or False if the donor
    would be a bridge donor.
- If a person isn't represented in a temporary departures list, assume they are
    always present.
- [BUGFIX] Fix typo in docs
- Add colours and label-options to Graph.dot() output
- [BUGFIX] Don't crash if setting maxChainLength == 0
- Add support for v3 of the new JSON format, where recipients and donors can also be
    stored as a dictionary indexed by ID as well as a list.
- [BUGFIX] Don't use int() for IDs in new JSON format

## [3.1.4]

- [BUGFIX] Allow the new JSON format even if donor ages are not known

## [3.1.3]

- Add a new JSON format that allows string identifiers for recipients
- Dynamic simulations won't let a person arrive and immediately take a break.

## [3.1.2]

- Add Instance.activeTransplants() which only returns transplants where the
    donor and recipient are both in this instance. This sounds useless, but
    in dynamic simulations donors still know about "all" transplants, to anyone
    in the overall instance, but sub-instances only have certain donors and
    recipients within them.

## [3.1.1]

- Require HiGHS for testing, otherwise RCVF tests fail

## [3.1.0]

- Introduce KEPSolveFail, a specific exception thrown if the model is not
  solved to optimality. This can be useful to catch if you have set a solver
  timeout.
- Add SolverOptions and SolverStatistics classes to help set up and analyse the
  ILP solving when solving KEP problems.
- Add reduced cost variable fixing to solver implementations. This can, for
  larger problems, reduce running times significantly by quickly determining
  which variables can be deactivated early. See Delorme et al. (2022) "New
  algorithms for hierarchical optimization in kidney exchange programs" for more
  details.

## [3.0.8]

- Fix cycle finding when the cycle length limit is 0
- Warn that PICEF doesn't support full details (list all potential cycles and
    chains)
- Set the selected exchanges even if the final objective function(s) are empty
- Ensure that if EffectiveTwoWay or BackArc objectives are used then alternate
    and embedded cycles are built

## [3.0.7]

- Remove Instance.getTransplant(Donor, Recipient), and add
    Donor.getTransplantTo(Recipient). This makes more sense given that
    transplants are stored associated with a donor, and not an instance.
- Allow NDDs and recipients in DynamicInstances to not have arrivals and
    departures. This occurs if the participant never enters a pool.

## [3.0.6]

- BUGFIX: Store NDD arrival/departure info in YAML as well
- Allow saving and loading of compressed files. Currently only LZMA-compressed
    (.xz) files are supported.

## [3.0.5]

- Allow writing of dynamic instances to YAML as well as JSON.

## [3.0.4]

- Recipients and non-directed donors will now both have the properties
    `match_runs_participated` and `periods_since_arrival` set during dynamic
    simulation. These both start at zero.
- Add Donor.property and Recipient.property. These allow the user to store
    arbitrary data related to either donor or recipient, and this data can then
    be later recalled in e.g. new objective functions

## [3.0.3]

- Change DynamicInstance.is_ill() function to DynamicInstance.is_available() and
    make it return a reason for being unavailable

## [3.0.2]

- Improve logging of dynamic simulation
- Change "illness" to be temporary departure in dynamic generation and
    simulation

## [3.0.1]

- Small fixes for recourse: Don't add multiple copies of a transplant to
    instances when doing recourse, and also allow recourse to select multiple
    internal exchanges. This does mean that it's simpler to just re-create the
    smaller instance from scratch than to try to determine which alternate and
    embedded exchanges cannot be selected together.

## [3.0.0]

- Rename Pool to Programme
- Add dynamic simulation. These allow for the simulation of a programme over
    time, as participants arrive, get selected, get transplanted, or leave. This
    is a large change, including new specific entities (DynamicInstance) that
    contain all of this information as well as new generators (DynamicGenerator)
    that can randomly generate all of this data.
- Status: Add Selected, tweak text for readability
- Model: Move the graph property to the Model superclass.
- Pool: Add build_alternates_and_embeds property and getOptimal().
    build_alternates_and_embeds is True if the pool will build alternates and
    embeds, while getOptimal() takes a list of exchanges and the graph they are
    from, and returns an optimal exchange from the list.
- Instance: Add hasDonor() and hasRecipient()
- ModelledExchange: Add __len__, __repr__, and improve __str__
- Add Exchange.allPairs(), Exchange.hasParticipant(), Exchange.hasTransplant(),
    and Exchange.transplantPairs(). Exchange.allPairs() returns all paired
    donors and recipients in the exchange, hasParticipant() is True if a given
    donor or recipient is part of the exchange, hasTransplant() returns True if
    a given transplant is in the exchange, and transplantPairs() returns for
    each transplant the donor and the recipient.
- Turn Instance into a dataclass. This means Instance.donors and
    Instance.recipients are now direct access to the mapping from ID to the
    donor or recipient, and Instance.transplants gives direct access to the list
    of transplants. To get an iterable over all donors or recipients, use
    Instance.allDonors() or Instance.allRecipients(). Also introduce
    Instance.allNDDs(). Also rename Exchange.all_recipients() and
    Exchange.all_donors() to Exchange.allRecipients() and Exchange.allDonors()
- Add function to retrieve transplant from an Instance by referring to the donor
    and recipient

## [2.4.4]

- Fix recording of model build times. They used to be built in the constructors,
    hence timing around them, but this is no longer true.
- Add generators using parameters from M. Delorme, S. García, J. Gondzio,
    J. Kalcsics, D. Manlove, W. Pettersson, J. Trimble Improved instance
    generation for kidney exchange programmes; Computers & Operations Research
    2022; doi: 10.1016/j.cor.2022.105707 
- Drop Python 3.9 support, explicitly add Python 3.12 support

## [2.4.3]

- Bugfix: Don't always run build_alternates_and_embeds in
    CycleAndChainFormulation

## [2.4.2]

- Another bugfix, this time for CompatibilityGraph.addEdges()

## [2.4.1]

- Bugfix for typo in CompatibilityGraph.exchangeEdges

## [2.4.0]

- Add PICEF model

## [2.3.1]

- Add ability to output CompatibilityGraph in DOT graph format
- Add an option `build_alt_embed` to models that can be set to 0 (for no
    alternate or embedded cycles), 1 (for all alternate and embedded cycles) and
    2 and 3 (two ways of restricting alternate and embedded cycles to those
    expected by NHSBT).
    For more precise details on what this means, see the documentation for
    `build_alternates_and_embeds` in `kep_solver/graph.py`.
- Add UKXML output format
- Allow for floating-point inaccuracies when checking validity of distributions
    for dataset generators.

## [2.3.0]

- API changes to models - maxCycleLength and maxChainLength must now be
    specified as keyword arguments.
- Add status field for donors and recipients. Only donors and recipients who are
    "InPool" can be in a matching run. Note that if a donor is "InPool" but
    their paired recipient is not, then the donor still won't be in the matching
    run (and vice-versa if all of a recipient's donors are not "InPool")
- Add a new YAML format. In particular, this format allows recipient identifiers
    to be arbitrary strings, instead of just integers.

## [2.2.0]

- Add ability to count number of solutions at each objective step
- Calculate time taken to solve each individual objective
- Move to pyproject.toml completely for builds, and using the build package to
	actually build. This is required as setuptools is being deprecated.
- Allow a user to specify how ID strings for Donors and Recipients should be
	generated when generating random instances.
- Add Instance.writeFileXml() to write to XML.

## [2.1.3]

- Add Instance.writeFile() and Instance.writeFileJson() methods for writing
	instances to files. So far only the NHSBT JSON format is supported.
- Fix DonorCountGenerator to not expect integers as keys in JSON. JSON doesn't
	allow integers as keys, so expect the keys to be string representations of
	integers instead.
- Fix reading of FloatGenerator from JSON when a single floating point number
	has a chance of occuring.

## [2.1.2]

- RecipientGenerator now links a donor to their recipient correctly
- CompatibilityGraph.findCycles() speed-ups
- CompatibilityGraph.findChains() speed-ups
- Cache Vertex.adjacent() list and hash(Exchange)
- Update python version for notebooks
- Added prototype functions to Model superclass for getting cycles, chains,
	exchanges, and getting exchange values. These obviously might not be easily
	implementable by all models, and may be left unimplemented.

## [2.1.1]

- Documentation updates

## [2.1.0]

- Create random entity generators. Each of these can generate random instances
	according to some given configuration. The configuration of each can be read
	from a JSON object, and also be written to a JSON object (with the exception
	of CompatibilityChanceGenerator when a function is used to define the
	distribution to use). These items can also nested (e.g., the
	RecipientGenerator includes a DonorGenerator object) and will automatically
	export the configurations of nested generators. The complete list of
	generators added is:
	* BloodGroupGenerator
	* DonorGenerator
	* DonorCountGenerator
	* FloatGenerator (can be used for cPRA or compatibility chance)
	* cPRAGenerator
	* CompatibilityChanceGenerator
	* RecipientGenerator
	* InstanceGenerator
- Create InstanceSet entity. This stores a set of Instance objects, and can
	also calculate the compatibility chance for recipients. There are also
	helpful functions to output all donor or recipient information into a Pandas
	dataframe for statistical analysis.
- Instance: Add ability to add pre-constructed recipients
- Add underscores to string representations to separate object type and ID
- Add CompatibilityChance to Recipient class. This represents the chance that
	this Recipient will be compatible with a Donor, assuming that the two are
	ABO compatible.
- Move BloodGroup functions into the class

## [2.0.12]

- Fixed bug with single altruistic donors (i.e. chains containing just an
	altruistic donor) counting as containing an effective two-way exchange.

## [2.0.11]

- Add documentation of output format

## [2.0.10]

- Bug fixes for the JSON output.

## [2.0.9]

- Add support for JSON output (in UK style). This involved some refactoring, as
	this output needs to know the model used to solve an instance.
- Add tests for JSON output
- pool.Pool objects now must have a string description
- pool.Pool exposes maxCycleLength and maxChainLength as properties
- pool.solve\_single() now returns a Solution and the Model used to find it
- model.UK\_age\_score(): Move the UK age scoring into its own function
- Hide pulp warnings on overwriting objectives

## [2.0.8]

- More fixes for backarcs. Make sure that a backarc exchange only has two
	vertices in it, otherwise we might accidentally catch a long chain in the
	reverse direction.
- EffectiveTwoWay: Chains should be counted.

## [2.0.7]

- The CycleAndChainModel needs all cycles and exchanges to have unique IDs, so
	force this.
- Accidentally missed version 2.0.6

## [2.0.5]

- Another backarc calculation fix. Each arc should have at most one "backarc"
	exchange, even if there are multiple other exchanges that could match the
	correct recipients (due to some of said recipients having multiple donors).

## [2.0.4]

- Equality comparisons of exchanges only considers exchange IDs now
- Fix backarc calculation. Backarcs can use different donors, but must have the
	right recipients

## [2.0.3]

- Fix error with Pulp and empty objectives

## [2.0.2]

- Rework UK backarcs. To match existing code, these are implemented in a
	specific manner.
- Alternate and embedded exchanges for cycles must be cycles, and alternate and
	embedded exchanges for chains must be chains that use the same non-directed
	donor
- Add __repr__ to Donor

## [2.0.0]

- New class for Exchange objects
- Add build\_alternates\_and\_embeds() function to find alternate and embedded
	cycles
- Update documentation to add example of CompatibiltyGraph usage
- Moved to [Black](https://black.readthedocs.io/en/stable/) for formatting

## [1.0.4]

- Use setuptools\_scm for versioning

## [1.0.3]

- Fix continuous deployment

## [1.0.2]

- Fix documentation

## [1.0.1]

- Add ability to read blood groups of donors and recipients
- Add Recipient.pairedWith(Donor) function
- Add custom exceptions for data IO
- Allow variations of bloodgroup/bloodtype in input
- Allow variations of cPRA/PRA/cpra in input
- Add functions for blood group compatibility checks to Donor and Recipient

## [1.0.0]

First release
