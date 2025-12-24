"""Describes a number of classes related to the compatibility graph."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any, Union, Optional, Iterable, Callable

from kep_solver.entities import Donor, Recipient, Status, Transplant


class Vertex:
    """A vertex in a digraph representing a donor (directed or
    non-directed)."""

    _sink: Optional["Vertex"] = None

    def __init__(self, index: int, represents: Donor) -> None:
        self._index: int = index
        self._represents: Donor = represents
        self._properties: dict[str, Any] = {}
        self._edges_out: list[Edge] = []
        self._edges_in: list[Edge] = []
        self._adj: Optional[list[Vertex]] = None

    @property
    def index(self) -> int:
        """Get the index (in the graph) of this vertex.

        :return: the index
        """
        return self._index

    def isNdd(self) -> bool:
        """True if this vertex corresponds to a non-directed donor.

        :return: True if this vertex corresponds to a non-directed
            donor
        """
        return self.donor.NDD

    @property
    def donor(self) -> Donor:
        """Return the donor associated with this vertex.

        :return: the associated donor"""
        return self._represents

    def addEdgeIn(self, edge: Edge) -> None:
        """Add an edge leading in to this vertex.

        :param edge: the edge
        """
        self._edges_in.append(edge)

    def addEdgeOut(self, edge: Edge) -> None:
        """Add an edge leading out from this vertex.

        :param edge: the edge
        """
        self._adj = None
        self._edges_out.append(edge)

    @property
    def edgesIn(self) -> list[Edge]:
        """Return the list of edges leading in to this vertex.

        :return: the list of edges leading in to this vertex.
        """
        return self._edges_in

    @property
    def edgesOut(self) -> list[Edge]:
        """Return the list of edges leading out from this vertex.

        :return: the list of edges leading out of this vertex.
        """
        return self._edges_out

    def adjacent(self) -> list[Vertex]:
        """Return the neighbours of this vertex

        :return: the list of neighbouring vertices
        """
        if self._adj is None:
            self._adj = [edge.end for edge in self.edgesOut]
        return self._adj

    def __str__(self) -> str:
        """Return a string representation of the vertex."""
        if self.isNdd():
            return f"V({self.donor} ({self.index}))"
        else:
            return f"V({self.donor},{self.donor.recipient} ({self.index}))"

    def __repr__(self) -> str:
        return str(self)

    @staticmethod
    def sink() -> Vertex:
        if Vertex._sink is None:
            sink_donor = Donor(id="sink")
            sink_donor.NDD = True
            Vertex._sink = Vertex(index=-1, represents=sink_donor)
        return Vertex._sink


class Exchange:
    """An exchange is either a cycle or a chain. This class lets us embed
    information (like embedded exchanges, or alternates) into the exchange.
    """

    def __init__(self, _id: str, vertices: list[Vertex]):
        self._id: str = _id
        self._vertices: tuple[Vertex, ...] = tuple(vertices)
        self._alternates: list[Exchange] = []
        self._embedded: list[Exchange] = []
        self._hash = hash(tuple([v.index for v in self.vertices]))

    @property
    def id(self) -> str:
        """The ID of the exchange."""
        return self._id

    @property
    def vertices(self) -> tuple[Vertex, ...]:
        """The vertices in this exchange."""
        return self._vertices

    @property
    def chain(self) -> bool:
        """Returns True if this exchange represents a chain."""
        return self._vertices[0].isNdd()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Exchange):
            return NotImplemented
        return self.id == other.id

    def __neq__(self, other: object) -> bool:
        return not (self == other)

    def __len__(self):
        """Returns the number of vertices (donors) in the exchange. Note that
        in the case of a non-directed altruistic donor, this will be greater
        than the number of recipients in the exchange.
        """
        return len(self._vertices)

    def __getitem__(self, index):
        """Gets the vertex at the appropriate index in the chain.

        :param index: The desired index
        """
        return self._vertices[index]

    def __iter__(self):
        """Allow iteration over exchanges, by returning an iterator to the
        vertices in it.
        """
        return self._vertices.__iter__()

    def __str__(self) -> str:
        return f"{self._vertices}"

    def __repr__(self) -> str:
        return str(self)

    def allDonors(self) -> list[Donor]:
        """Get all of the donors involved in this exchange."""
        return [v.donor for v in self._vertices]

    def allRecipients(self) -> list[Recipient]:
        """Get all of the recipients."""
        return [v.donor.recipient for v in self._vertices if not v.isNdd()]

    def allPairs(self) -> list[tuple[Donor, Optional[Recipient]]]:
        """Get all the donor,recipient pairs in this exchange, in order."""
        return [
            (v.donor, v.donor.recipient if not v.isNdd() else None)
            for v in self._vertices
        ]

    def hasParticipant(self, participant: Donor | Recipient) -> bool:
        """Return True if this exchange involves the given participant.

        :param participant: The participant in question
        :return: True if and only if the participant is involved in this
            exchange.
        """
        if isinstance(participant, Donor):
            return participant in self.allDonors()
        return participant in self.allRecipients()

    def hasTransplant(self, transplant: Transplant) -> bool:
        """Return True if this exchange involves the given transplant.

        :param transplant: The transplant in question
        :return: True if and only if the transplant is in this exchange.
        """
        for donor, recipient in self.transplantPairs():
            if donor == transplant.donor and recipient == transplant.recipient:
                return True
        return False

    def transplantPairs(self) -> list[tuple[Donor, Recipient]]:
        """Get the pairs of transplant-donor, transplant-recipient
        corresponding to this exchange."""
        pairs: list[tuple[Donor, Recipient]] = []
        for index, vert in enumerate(self._vertices[:-1]):
            donor = vert.donor
            recipient = self._vertices[index + 1].donor.recipient
            pairs.append((donor, recipient))
        if not self.chain:
            # Final transplant pair
            donor = self._vertices[-1].donor
            recipient = self._vertices[0].donor.recipient
            pairs.append((donor, recipient))
        return pairs

    def backarc_exchanges_uk(self) -> list[Exchange]:
        """Return the exchanges that contain backarcs from this exchange (by
        the UK definition of backarc).

        A backarc, by UK counting, is only defined for exchanges with three
        transplants (i.e., three donors). Let the three donors be A, B, and C.
        A backarc exists if A (respectively B and C) can donate to the paired
        recipient of C (respectively A and B).

        :return: A list containing each Exchange object that has a backarc from
            this Exchange.
        """
        if len(self) == 2:
            return []
        if len(self) != 3:
            raise Exception(
                "Backarcs are not defined for exchanges of length 4 or more"
            )
        backarc_exchanges = []
        for ind, v in enumerate(self):
            prev_v = self[(ind - 1) % len(self)]
            prev_donor = prev_v.donor
            donor = v.donor
            # Backarcs are tricky to deal with as if there is an NDD, we cannot
            # access its recipient.
            if prev_donor.NDD:
                # Need to find exchange containing backarc back to NDD
                recipients = set([donor.recipient])
            else:
                if donor.NDD:
                    # Need to find backarc from NDD to previous recipient
                    recipients = set([prev_donor.recipient])
                else:
                    # No NDDs involved, just look for exchange with same two
                    # recipents
                    recipients = set([donor.recipient, prev_donor.recipient])
            # Note that a backarc may exist in an alternate (rather than
            # embedded) exchange if this exchange is a chain, as an exchange is
            # an alternate if it has the same set of recipients (unlike
            # embedded exchanges, which have a strict subset only). This can
            # occur in a long chain, if there is also a two-way cycle between
            # the two vertices representing directed (paired) donors.
            if self.chain:
                for exchange in self.alternates:
                    # Backarc must have length 2
                    if len(exchange) != 2:
                        continue
                    if set(exchange.allRecipients()) == recipients:
                        backarc_exchanges.append(exchange)
                        break
            for exchange in self.embedded:
                if set(exchange.allRecipients()) == recipients:
                    backarc_exchanges.append(exchange)
                    break
        return backarc_exchanges

    def num_backarcs_uk(self) -> int:
        """Return the number of backarcs in this exchange (by the UK definition
        of backarc).

        A backarc, by UK counting, is only defined for exchanges with three
        transplants (i.e., three donors). Let the three donors be A, B, and C.
        A backarc exists if A (respectively B and C) can donate to the paired
        recipient of C (respectively A and B).

        :return: The number of backarcs in this Exchange.
        """
        return len(self.backarc_exchanges_uk())

    @property
    def alternates(self) -> list[Exchange]:
        """Return the alternate exchanges for this exchange. An alternate
        exchange is one that still matches exactly the same set of recipients,
        but possibly with either different donors (if some recipients are
        paired with multiple donors) or perhaps different donors and recipients
        are paired together.

        Note that this attribute is only populated if the function
        build_alternates_and_embeds is run.
        """
        return self._alternates

    def add_alternate(self, alt: Exchange) -> None:
        """Add an alternate exchange. An alternate exchange is one that still
        matches exactly the same set of recipients, but possibly with either
        different donors (if some recipients are paired with multiple donors)
        or perhaps different donors and recipients are paired together.

        :param alt: The alternate exchange.
        """
        if alt != self:
            self._alternates.append(alt)

    def add_alternates(self, alts: Iterable[Exchange]) -> None:
        """Add alternate exchanges. An alternate exchange is one that still
        matches exactly the same set of recipients, but possibly with either
        different donors (if some recipients are paired with multiple donors)
        or perhaps different donors and recipients are paired together.

        :param alts: The alternate exchanges.
        """
        for alt in alts:
            self.add_alternate(alt)

    @property
    def embedded(self) -> list[Exchange]:
        """Returns the exchanges embedded in this exchange. An embedded
        exchange is one that still matches some of the recipients within this
        exchange, but does not match any recipients not in this exchange.

        Note that this attribute is only populated if the function
        build_alternates_and_embeds is run.
        """
        return self._embedded

    def add_embedded(self, embed: Exchange) -> None:
        """Add an embedded exchange. An embedded exchange is one that still
        matches some of the recipients within this exchange, but does not match
        any recipients not in this exchange.

        :param embed: The embedded exchange.
        """
        self._embedded.append(embed)

    def add_embeddeds(self, embeds: Iterable[Exchange]) -> None:
        """Adds embedded exchanges. An embedded exchange is one that still
        matches some of the recipients within this exchange, but does not match
        any recipients not in this exchange.

        :param embeds: The embedded exchanges.
        """
        for embed in embeds:
            self.add_embedded(embed)

    def __hash__(self):
        return self._hash


class Edge:
    """An edge in a digraph, representing a potential transplant. An
    edge is always associated with a donor.
    """

    def __init__(self, donor: Donor, start: Vertex, end: Vertex) -> None:
        self._donor: Donor = donor
        self._properties: dict[str, Any] = {}
        self._start_vertex: Vertex = start
        self._end_vertex: Vertex = end

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"Edge({self._start_vertex} -> {self._end_vertex})"

    @property
    def donor(self) -> Donor:
        """Return the donor associated with this transplant.

        :return: The associated donor
        """
        return self._donor

    @property
    def start(self) -> Vertex:
        """Return the start point of this edge.

        :return: the start Vertex of this edge
        """
        return self._start_vertex

    @property
    def end(self) -> Vertex:
        """Return the end-point of this edge.

        :return: the end Vertex of this edge
        """
        return self._end_vertex

    def addProperty(self, name: str, value) -> None:
        """Add an arbitrary property to this edge. This can be used
        for e.g. a score value associated with the transplant.

        :param name: the name of the property
        """
        self._properties[name] = value

    def getProperty(self, name: str) -> Any:
        """Get a property of this transplant.

        :param name: the name of the property
        :return: the associated value, which may have any type
        """
        return self._properties[name]


class CompatibilityGraph:
    """A :ref:`compatibility graph` is a digraph representing a KEP instance.
    Note that each vertex is a donor. Each edge corresponds to a potential
    transplant, and thus is associated with a donor that is paired with the
    recipient at beginning of the arc.
    """

    def __init__(self, instance=None) -> None:
        self._vertices: list[Vertex] = []
        self._edges: list[Edge] = []

        # Map each recipient or ndd to a vertex object
        self._vertex_map: dict[Union[Donor, Recipient], Vertex] = {}
        if instance is not None:
            for donor in instance.allDonors():
                if donor.inPool():
                    self.addDonor(donor)
            for transplant in instance.transplants:
                if (
                    not transplant.known_to_fail
                    and self.hasDonor(transplant.donor)
                    and transplant.donor.inPool()
                    and self.hasRecipient(transplant.recipient)
                    and transplant.recipient.inPool()
                ):
                    self.addEdges(
                        transplant.donor,
                        transplant.recipient,
                        properties={"weight": transplant.weight},
                    )

    @property
    def size(self) -> int:
        """The number of vertices in the graph.

        :return: the number of vertices
        """
        return len(self._vertices)

    @property
    def vertices(self) -> list[Vertex]:
        """The vertices in the graph.

        :return: the vertices
        """
        return self._vertices

    def edges(self) -> list[Edge]:
        """The edges in the graph.

        :return: the edges
        """
        return self._edges

    def number_ndds(self) -> int:
        """Count the number of non-directed donors in this graph.

        :return: The number of non-directed donors.
        """
        return len([v for v in self.vertices if v.isNdd()])

    def hasDonor(self, donor: Donor) -> bool:
        """Return True if the given donor is represented in this graph."""
        return donor in self._vertex_map

    def hasRecipient(self, recipient: Recipient) -> bool:
        """Return True if the given donor is represented in this graph."""
        return any(self.hasDonor(donor) for donor in recipient.donors())

    def exchangeEdges(self, exchange: Exchange) -> list[Edge]:
        """Return the edges in the given exchange.

        :param exchange: The exchange in question
        :return: The edges in this exchange.
        """
        result: list[Edge] = []
        for j, vertex in enumerate(exchange[:-1]):
            for edge in vertex.edgesOut:
                if edge.end == exchange[j + 1]:
                    result.append(edge)
                    break
        if not exchange.chain:
            for edge in exchange[-1].edgesOut:
                if edge.end == exchange[0]:
                    result.append(edge)
                    break
        return result

    def addDonor(self, donor: Donor) -> None:
        """Add a vertex representing a donor.

        :param donor: a donor to be added to the graph.
        """
        vertex = Vertex(len(self._vertices), donor)
        self._vertices.append(vertex)
        self._vertex_map[donor] = vertex

    def donorVertex(self, donor: Donor) -> Vertex:
        """Get the vertex associated with a donor.

        :param donor: the donor to find
        :return: the vertex associated with the donor
        """
        return self._vertex_map[donor]

    def addEdges(self, donor: Donor, recip: Recipient, properties: dict[str, Any]):
        """Add edges to the digraph corresponding to some potential
        transplant, optionally with some additional properties. Note
        that since the graph uses donors to represent vertices, if the
        given recipient has multiple donors then one edge will be added
        for each paired donor

        :param donor: the donor in the transplant
        :param recip: the recipient in the transplant
        :param properties: an optional dictionary mapping property
            names (as strings) to properties
        """
        start = self._vertex_map[donor]
        for pairedDonor in recip.donors():
            if pairedDonor.status != Status.InPool:
                continue
            end = self._vertex_map[pairedDonor]
            edge = Edge(donor, start, end)
            for name, value in properties.items():
                edge.addProperty(name, value)
            start.addEdgeOut(edge)
            end.addEdgeIn(edge)
            self._edges.append(edge)

    def findChains(self, maxChainLength: int, index_offset: int = 0) -> list[Exchange]:
        """Finds and returns all chains in this graph. Note that this
        is specifically chains, and does not include cycles.

        :param maxchainLength: the maximum length of any chain
        :param index_offset: By default, chains are given IDs starting at zero. By
          setting this parameter to a non-zero value, IDs start at this number. This
          can help avoid ID clashes.
        :returns: a list of chains, where each chain is represented as
            a list of vertices
        """
        if maxChainLength == 0:
            return []
        chains: list[Exchange] = []
        used: set[int] = set()
        stack: list[Vertex]

        def _extend(v: Vertex):
            chains.append(Exchange(f"{len(chains) + index_offset}", stack.copy()))
            if len(stack) == maxChainLength:
                return
            for w in v.adjacent():
                if w.index not in used:
                    used.add(w.index)
                    stack.append(w)
                    _extend(w)
                    stack.pop()
                    used.remove(w.index)

        for vert in self.vertices:
            if not vert.isNdd():
                continue
            stack = [vert]
            _extend(vert)
        return chains

    def findCycles(
        self,
        maxCycleLength: int,
        index_offset: int = 0,
        considerConnectedComponents: bool = False,
    ) -> list[Exchange]:
        """Finds and returns all cycles in this graph. Note that this
        is specifically cycles, and does not include chains.

        :param maxCycleLength: the maximum length of any cycle
        :param index_offset: By default, chains are given IDs starting at zero. By
          setting this parameter to a non-zero value, IDs start at this number. This
          can help avoid ID clashes.
        :param considerConnectedComponents: If True, we use Tarjan's algorithm
          to first split the graph into strongly connected components and never
          follow edges that go between strongly connected components. This is
          valid as any cycle must exist completely within one strongly connected
          cycle, but the overhead of calculating strongly connected components is
          generally not worth it. If False, we instead are allowed to follow any
          edge.
        :returns: a list of cycles, where each cycle is represented as
          a list of vertices
        """
        # Lazily return an empty list in this scenario.
        if maxCycleLength == 0:
            return []
        # Implementing a variant of Johnson's algorithm from
        # Finding All The Elementary Circuits of a Directed Graph,
        # Donald B. Johnson, SIAM J.
        # Comput., 1975
        # There are some changes, however. Blocklists (B(n) in the
        # paper) aren't used, as since we limit cycle lengths we will
        # return when the stack is too long, but that doesn't mean we
        # must've created all cycles through a given vertex. For the
        # same reason, v is unblocked after each visit, regardless of
        # whether we find any cycles
        stack: list[int] = []
        cycles: list[list[int]] = []

        def _circuit(v: int, condition: Callable[[int], bool]) -> None:
            stack.append(v)
            for w in self.vertices[v].adjacent():
                if w.index == stack[0]:
                    cycles.append(stack.copy())
                    # Have completed cycle, and cannot recurse as we are at the
                    # max length, so no need to check other neighbours of v
                    if len(stack) == maxCycleLength:
                        stack.pop(-1)
                        return
                    continue
                if condition(w.index):
                    continue
                if len(stack) == maxCycleLength:
                    continue
                if w.index not in stack:
                    _circuit(w.index, condition)
            stack.pop(-1)
            return

        def _tarjan(num_forbidden_vertices: int) -> Optional[list[int]]:
            index = 0
            component = None
            stack = list()
            indices = [-1] * self.size
            lowlink = [-1] * self.size
            onStack = [False] * self.size

            def _strongconnect(v: int, index: int) -> tuple[int, Optional[list[int]]]:
                indices[v] = index
                lowlink[v] = index
                index += 1
                onStack[v] = True
                component = None
                stack.append(v)
                for w in self.vertices[v].adjacent():
                    if w.index < num_forbidden_vertices:
                        continue
                    if indices[w.index] == -1:
                        index, component = _strongconnect(w.index, index)
                        lowlink[v] = min(lowlink[v], lowlink[w.index])
                    elif onStack[w.index]:
                        lowlink[v] = min(lowlink[v], indices[w.index])
                if lowlink[v] == indices[v]:
                    component = stack
                return index, component

            for v in range(num_forbidden_vertices, self.size):
                if indices[v] == -1:
                    index, component = _strongconnect(v, index)
                if component is not None:
                    return component
            return None

        if considerConnectedComponents:
            s = 0
            while s < self.size:
                # Let Ak be adj matrix of strongly connected component K of
                # the induced graph on {s, s+1, ... , n} that contains the
                # lowest vertex
                component = _tarjan(s)
                if component is None:
                    s = self.size
                else:
                    compset = set(component)
                    s = component[0]
                    _circuit(s, lambda v: v not in compset)

        else:
            for s in range(self.size):
                if not self.vertices[s].isNdd():
                    _circuit(s, lambda v: v < s)
        realCycles: list[Exchange] = []
        for indices in cycles:
            real = [self.vertices[i] for i in indices]
            realCycles.append(Exchange(f"{len(realCycles) + index_offset}", real))
        return realCycles

    def dot(
        self,
        labels: bool = True,
        exchanges: list[Exchange] = [],
        colours: list[str] = [],
    ) -> str:
        """Return a string that represents this graph in DOT format. Labels can
        be enabled and disabled with the labels parameter. A list of exchanges
        can be passed in; the edges for each transplant in each exchange will
        be coloured the same colour. The colours can also be specified, but
        they must be colours that your graph drawing tool supports.

        :param labels: If True, labels will be inside the nodes.
        :param exchanges: If not empty, each exchange will be coloured.
        :param colours: A list of colours to use for colouring exchanges.
        """
        if not colours:
            colours = [
                "cornflowerblue",
                "darkorchid",
                "chartreuse2",
                "deeppink",
                "goldenrod",
                "palegreen1",
                "rosybrown1",
                "sienna1",
            ]

        def mk_name(vertex):
            if vertex.donor.NDD:
                return str(vertex.donor)
            else:
                return f"{str(vertex.donor)},{str(vertex.donor.recipient)}"

        res = "digraph kep {\n"
        if not labels:
            res += 'node [label="",fixedsize="true",width=0.1,height=0.1]\n'
        # Add coloured edges last so they appear "over" uncoloured edges
        delayed = ""
        for edge in self.edges():
            colour = ""
            if exchanges:
                colour = " [penwidth=0.1,arrowsize=0.2]"
                transplant = Transplant(
                    edge.start.donor, edge.end.donor.recipient, weight=0
                )
                for index, exchange in enumerate(exchanges):
                    if exchange.hasTransplant(transplant):
                        colour = (
                            f" [color={colours[index % len(colours)]},penwidth=1.2]"
                        )
                        break
            edge_str = f'"{mk_name(edge.start)}" -> "{mk_name(edge.end)}"{colour};\n'
            if "color" in colour:
                delayed += edge_str
            else:
                res += f'"{mk_name(edge.start)}" -> "{mk_name(edge.end)}"{colour};\n'
        res += delayed
        res += "}"
        return res


def build_alternates_and_embeds(
    exchanges: list[Exchange],
    uk_variant: int = 0,
) -> None:
    """Finds and adds alternate and embedded exchanges based on the given exchanges. An
    alternate exchange is one that still matches exactly the same set of
    recipients, but possibly with either different donors (if some recipients
    are paired with multiple donors) or perhaps different donors and recipients
    are selected for transplant.  An embedded exchange is one that matches some
    (but not all) of the recipients within this exchange, but still does not
    match any recipients not in this exchange. Note that in both cases, if the
    exchange is a chain, we require that any alternate or embedded exchanges
    that are also chains must still be initiated by the same non-directed
    donor.

    Note that if uk_variant is either 1 or 2, then alternate exchanges are
    limited to those that have the recipients in the same order. If uk_variant
    is 1, then all embedded exchanges are returned, whereas if uk_variant is 2,
    then only embedded exchanges that do not use new (alternate) donors are
    included.

    :param exchanges: The exchanges to search for alternates
    :param uk_variant: Whether to limit alternate and embedded exchanges to
        those that NHSBT expect
    """
    # Note that Model._build_alt_embed - 1 property must map onto the uk_variant
    # parameter of the build_alternates_and_embeds function

    def okay_alternate(exchange, orig):
        if uk_variant == 0:
            return True
        # Cannot swap 2nd and 3rd pair in a long chain
        if orig.chain and exchange.chain:
            for v1, v2 in zip(orig[1:], exchange[1:]):
                if v1.donor.recipient != v2.donor.recipient:
                    return False
        # Cannot swap order in a 3-way cycle
        if (
            not orig.chain
            and not exchange.chain
            and len(orig) == len(exchange)
            and len(exchange) == 3
        ):
            first_orig = orig[0].donor.recipient.id
            second_orig = orig[1].donor.recipient.id
            for idx, v in enumerate(exchange):
                if v.donor.recipient.id == first_orig:
                    if exchange[(idx + 1) % 3].donor.recipient.id != second_orig:
                        return False
        return True

    def okay_embedded(exchange: Exchange, orig: Exchange):
        if uk_variant == 0:
            return True
        if uk_variant == 2:
            # Only allow embedded exchanges that don't use any new donors
            if len(set(exchange.allDonors()) - set(orig.allDonors())) != 0:
                return False
        return True

    cache: dict[tuple[Recipient, ...], list[Exchange]] = defaultdict(list)
    # First create a mapping from sets of recipients to possible exchanges
    for exchange in exchanges:
        recipients = exchange.allRecipients()
        # Sort the recipients so we don't think [1,2] is different to [2,1]
        recipients.sort(key=lambda r: r.id)
        cache[tuple(recipients)].append(exchange)
    # Next, add the alternates to each exchange
    for exchange in exchanges:
        recipients = exchange.allRecipients()
        # Sort the recipients so we don't think [1,2] is different to [2,1]
        recipients.sort(key=lambda r: r.id)
        if exchange.chain:
            first = exchange[0].donor
            exchange.add_alternates(
                e
                for e in cache[tuple(recipients)]
                if e[0].donor == first and okay_alternate(e, exchange)
            )
        else:
            exchange.add_alternates(
                e
                for e in cache[tuple(recipients)]
                if not e.chain and okay_alternate(e, exchange)
            )
        # Note: We allow a chain consisting of only a non-directed donor, but
        # they should not be counted as an "embedded" exchange, hence minimum
        # size of 1 below
        largest_embedded = len(recipients)
        # A long chain may have an embedded two-cycle which matches the exact
        # same set of recipients, so increase our upper limit on embed_size
        if exchange.chain:
            largest_embedded += 1

        for embed_size in range(1, largest_embedded):
            for subset in combinations(recipients, embed_size):
                # Recipients is already sorted, so subsets should be too
                if exchange.chain:
                    first = exchange[0].donor
                    exchange.add_embeddeds(
                        e
                        for e in cache[tuple(subset)]
                        if (
                            not e.chain
                            or (len(e) < len(exchange) and e[0].donor == first)
                        )
                        and okay_embedded(e, exchange)
                    )
                else:
                    exchange.add_embeddeds(
                        e
                        for e in cache[tuple(subset)]
                        if not e.chain and okay_embedded(e, exchange)
                    )
