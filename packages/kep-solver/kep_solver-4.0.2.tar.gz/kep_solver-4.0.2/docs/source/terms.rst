***********
Terminology
***********

Medical terminology
===================

As kep_solver deals with kidney exchange programmes, it must necessarily use
some medical terms. This page should not be used as a source for medical
information. Medical doctors and experts, as well as medical texts, will
provide much more accurate definitions of the terms herein. This page should
only be used as a reference when using the kep_solver package.

.. _Blood groups:
.. _Blood group:

------------
Blood groups
------------

Each person has a blood group (sometimes referred to as a blood type). In
particular, the four blood groups are A, B, AB, and O. Blood typing may also
involve extra markers (such as +/- to indicate a presence or absence of the
Rh(D) antigen), but for kep_solver we strictly use A, B, AB, and O. When
determining compatibility, kep_solver follows the usual diamond of blood group
compatibility. That is to say, a recipient with blood group O is only ever
compatible with donors who have blood group O, a recipient with blood group AB
can be compatible with donors who have any blood group, and a recipient with
blood group A (respectively blood group B) can potentially be compatible with
donors with blood groups A or O (respectively blood groups B or O).

.. _cPRA:

----
cPRA
----

cPRA stands for calculate Panel Reactive Antibodies. Panel Reactive Antibodies,
or PRA, is a technique to estimate what proportion of donors a given recipient
will be tissue-type compatible with. For a PRA, this is done by actual lab
testing of compatibility against a panel of 100 samples, where the exact
samples used varies. A newer technique, cPRA tries to provide a more accurate
representation of the same information (what portion of donors will a recipient
be expected to be compatible with) by examining the present of antibodies to
human leukocyte antigens (HLA) present in the recipient, and comparing that
with expected HLA distribution amongst donors. The exact calculation, again,
varies.

cPRA is often reported as a percentage ranging from 0% to 100%, and the percent
symbol is occasionally missed. Within kep_solver, we treat cPRA as a
floating-point number in the range [0, 1]. That is, cPRA is a number that is
between 0 and 1 inclusive. Depending on your data source, you may need to
divide by 100 before importing data (or multiply by 100 if exporting data).
Note that kep_solver will not allow you to set a cPRA value outside of the
range [0, 1], but will instead raise an exception.


.. _compatibility chance:

---------------------
Compatibility chance
---------------------

For a given recipient `R`, we say that their compatibility chance is the ratio of
`number of blood group compatible donors who have a transplant with R` divided
by `number of blood group compatible donors who appear in a matching run with R`.
The goal with compatibility chance is to represent the possibility of a
transplant being present once blood groups have been accounted for. Note that
this is distinct from cPRA, which aims only to represent the possibility of a
tissue-type incompatibility, while compatibility chance is aiming to
incorporate not only tissue-type incompatibility but also any other sources of
incompatibility.


.. _ndds:

------------------
Non-directed donor
------------------

A non-directed donor (sometimes also called an altruistic donor) is a donor who
joins a kidney exchange programme to donate a kidney, but without any
expectation of a kidney for a paired recipient in return. In particular,
a non-directed donor is required to initiate a chain.



Computational terminology
=========================


.. _compatibility graph:

-------------------
Compatibility Graph
-------------------

A compatibility graph is one way of representing recipients, donors, and
potential transplants at any given point in time. It is a directed graph,
consisting of vertices and (directed) arcs between some of these vertices.
Recall that each recipient joins a KEP with one or more paired donors, such
that if the recipient receives a kidney then one of their paired donors is
willing to donate a kidney.
`kep\_solver` uses the following construction for compatibility
graphs. This particular construction is used as it simplifies the handling of
recipients with multiple paired donors.
First, create one vertex for each donor.
Then, for each donor `D`, for each recipient `R` that `D` is not paired with but
where `D` is medically compatible with `R`,
and for each `D'` that `R` is paired with,
add an arc from donor `D` to `D'`.

Each arc from `D` to `D'` represents a potential transplant from `D` to the
paired recipient of `D'`.

Note that other definitions of compatibility graphs may merge all donors that
are paired with one recipient into one vertex.

.. _cycle:

-----
Cycle
-----

A cycle is a set of transplants such that for each recipient who is receiving a
transplant, exactly one of their paired donors is donating a kidney. In a
compatibility graph, such a set of transplants will appear as a cycle, hence
the name.

.. _chain:

-----
Chain
-----

A chain is a set of transplants that is started by a non-directed donor. For
each recipient in the chain, except for the last, exactly one of said
recipient's paired donors will donate a kidney to the next recipient.

.. _exchange:

--------
Exchange
--------

We use exchange to mean either a cycle or a chain.

