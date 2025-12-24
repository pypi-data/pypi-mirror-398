************
File formats
************

Input
=====

This package supports JSON, XML, and YAML. Note that two distinct JSON schema
are supported. The first exists due to historical reasons, the second removes
some unnecessary restrictions and streamlines some options. The XML format
expects identical data to the first JSON schema. However, while the YAML format
is very similar, but does away with some peculiarities of the other two
formats. In particular, the first JSON schema and XML require all recipient
identifies to be integers, while the second JSON schema and YAML allow
arbitrary strings to be used as recipient identifiers. Note that in testing, we
have noticed that JSON reading appears to be significantly faster in Python, so
the new `v2` JSON schema is recommended.

-------
JSON v1
-------

This software expects exactly one `data` object at the root. This contains an
object for each donor, indexed by the identifier of the donor. Each donor can
contain a `sources` object, itself a list containing zero, one, or more,
identifiers of recipients paired with this donor.  Each donor object can also
contain a `matches` element, containing a list of match objects, each
containing a `recipient` identifier (which must be an integer) and a `score`
value A donor object can also contain `dage` (donor age) and `altruistic` keys.
The `altruistic` element, while used in other software, is not used to mark
non-directed donors in kep_solver. Instead, a donor is non-directed if they are
paired with zero donors.

The following snippet gives an example input file containing two paired donors
(donor 1 paired with recipient 1 and donor 2 paired with recipient 2) as well
as an altruistic donor (donor 3). Donor 3 and donor 1 can donate to recipient
2, and donor 2 can donate to recipient 1.

.. code-block:: json

  { "data" :
      {
      "1" : {
              "sources" : [1],
              "dage" : 65,
              "matches" : [ { "recipient" : 2, "score" : 3 } ]
            },
      "2" : {
              "sources" : [2],
              "dage" : 45,
              "matches" : [ { "recipient" : 1, "score" : 2 } ]
            },
      "3" : {
              "altruistic": true,
              "dage" : 25,
              "matches" : [ { "recipient" : 2, "score" : 1 } ]
            }
      }
  }

-------
JSON v2
-------

The key `schema` at the root denotes the schema version. For `kep_solver` to
parse a file using this schema, the schema value must be an integer and at most 3. A file
using this schema must have two further objects at the root, a `donors` object
and a `recipients` object. The `donors` object contains either an array of `donor`
objects, or a dictionary mapping donor IDs to donors, where each `donor` contains the expected parameters (`id`, `age`,
`bloodtype`) as well as an array `paired_recipients` of IDs of paired
recipients (which may be empty for non-directed altruistic donors) and an array
`outgoing_transplants` containing, for each outgoing transplant. Each outgoing
transplant is represented as an object with a `recipient` key containing the
recipient's ID, and an integral `score`. The `recipients` object contains the
parameters `id`, `cPRA`, and `bloodtype`.

The following snippet gives an example input file containing two paired donors
(donor 1 paired with recipient 1 and donor 2 paired with recipient 2) as well
as an altruistic donor (donor 3). Donor 3 and donor 1 can donate to recipient
2, and donor 2 can donate to recipient 1.

.. code-block:: json

  {
  "schema": 3,
  "donors" : {
      "1": {
              "id" : "1",
              "paired_recipients" : ["1"],
              "age" : 65,
              "bloodtype": "A",
              "outgoing_transplants" : [
                      { "recipient" : 2, "score" : 3 }
              ]
              },
      "2": {
              "id": "2",
              "paired_recipients" : ["2"],
              "age" : 45,
              "outgoing_transplants" : [
                      { "recipient" : 1, "score" : 2 }
              ]
      },
      "3": {
              "id": "3",
              "paired_recipients": [],
              "age" : 25,
              "outgoing_transplants" : [
                      { "recipient" : 2, "score" : 1 }
              ]
      }
    },
  "recipients": {
      "1": {
              "id": "1",
              "cPRA": 85,
              "bloodtype": "A",
      },
      "2": {
              "id": "2",
              "cPRA": 99,
              "bloodtype": "O",
      },
    }
  }

---
XML
---

This software expects exactly one `data` tag at the root. This tag will contain
one `entry` tag for each donor, with a `donor_id` attribute storing the
identifier of the donor. Each `entry` tag can contain a `sources` tag, itself
containing zero, one, or more, `source` tags. Text inside each `source` tag
corresponds to the identifier of a recipient paired with this donor (the
recipient identifier must be an integer). Each `entry` should also contain a
`matches` tag, containing a number of `match` tags. Each `match` tag contains a
`recipient` tag and a `score` tag, which contain the recipient and score of the
match respectively. An `entry` can also contain `dage` (donor age) and
`altruistic` tags. The `altruistic` tag, while used in other software, is not
used to mark non-directed donors in kep_solver. Instead, a donor is non-directed
if they are paired with zero donors.

The following snippet gives an example input file containing two paired donors
(donor 1 paired with recipient 1 and donor 2 paired with recipient 2) as well
as an altruistic donor (donor 3). Donor 3 and donor 1 can donate to recipient
2, and donor 2 can donate to recipient 1.

.. code-block:: xml

  <?xml version="1.0" ?>
  <data>
      <entry donor_id="1">
      <sources>
        <source>1</source>
      </sources>
      <dage>65</dage>
      <matches>
        <match>
          <recipient>2</recipient>
          <score>3</score>
        </match>
      </matches>
    </entry>
    <entry donor_id="2">
      <sources>
        <source>2</source>
      </sources>
      <dage>58</dage>
      <matches>
        <match>
          <recipient>1</recipient>
          <score>4</score>
        </match>
      </matches>
    </entry>
    <entry donor_id="3">
      <dage>29</dage>
      <altruistic>true</altruistic>
      <matches>
        <match>
          <recipient>2</recipient>
          <score>10</score>
        </match>
      </matches>
    </entry>
  </data>


----
YAML
----

This format has a `schema` variable, denoting the version of the file format
used. For now, we are still on schema version 1. This format expects exactly one
`donors` dictionary at the root. Each key of this dictionary is a donor ID, and
contains any number of attributes. The currently supported attributes are `age`,
and `bloodtype`. Each donor can contain a `recipients` object, itself a list
containing zero, one, or more, identifiers of recipients paired with this donor.
Each donor object can also contain a `matches` element, containing a list of
match objects, each containing a `recipient_id` identifier and a `score` value.
Note that this format does not have a separate altruistic marker. Instead, a
donor is non-directed if they are paired with zero donors.

The following snippet gives an example input file containing two paired donors
(donor 1 paired with recipient 1 and donor 2 paired with recipient 2) as well
as an altruistic donor (donor 3). Donor 3 and donor 1 can donate to recipient
2, and donor 2 can donate to recipient 1.

.. code-block:: yaml

  schema: 1
  donors:
    '1':
      age: 50.0
      matches:
      - recipient_id: '2'
        score: 1.0
      recipients:
      - '1'
      bloodtype: O
    '2':
      age: 50.0
      matches:
      - recipient_id: '1'
        score: 1.0
      recipients:
      - '2'
      bloodtype: A
    '3':
      age: 60.0
      matches:
      - recipient_id: '2'
        score: 1.0
      bloodtype: AB
  recipients:
    '1':
      pra: 0.25
      bloodgroup: O
    '2':
      pra: 0.0
      bloodgroup: B


Output
======

Currently the only supported output format is a JSON format that is used by the
UK Living Kidney Sharing Scheme. It is very particular to this kidney exchange
programme.

-----------
UKLKSS JSON
-----------

This JSON output represents the solution to a single instance of a KEP problem.
Note that despite terminology in the JSON, `all_cycles` and `cycles` can also
represent chains in this format.

The JSON contains three name/value pairs. The first is named `algorithm` and
its value is a text description of the programme. This is currently user-configured.
The next item is named `output`, and its value is a nested collection
which contains exactly one element named `all_cycles`. This `all_cycles`
element contains another nested collection, with one entry for each potential
exchange. The name of each element is an identifier for the exchange, and these
will commonly but not necessarily be integers. Each exchange is then
represented by a collection, containing the following items. First, `alt` is an
ordered list of exchange identifiers that correspond to alternate exchanges for
this exchange. An alternate exchange is a different exchange that will still
match exactly the same recipients. Next, `backarcs` contains the number of
backarcs present in this exchange, and `weight` contains the weight (as
calculated by the UK scoring mechanism) of this exchange. Lastly, the set of
donor-recipient pairs is given as an ordered list of collections, named
`cycle`. Each collection in the cycle will contain `d` storing the identifier
of the donor, `s` containing the score of the transplant from `d` to the
recipient of the next pair, `dif` containing the age weight bonus based on the
age difference between `d` and the donor of the next pair, and `tb` containing
the tie-breaker value based on the age difference between `d` and the donor of
the next pair. The `cycle` collection may also contain a key `b` that stores
the number of backarcs for the transplant from `d` to the next recipient, `p`
containing the recipient of this pair (if `d` is directed), and `a` containing
the value `true` if `d` is non-directed. The JSON, at the root level, also
contains the key `exchange_data` which contains information about the selected
solution. This includes `description`, a text-based description of the
exchange, which is currently user-configured, the list of exchanges selected as
an ordered list of identifiers in `exchanges`, as well as `two_way_exchanges,
`three_way_exchanges`, `total_transplants`, and `weight`, which give the number
of two-way exchanges, number of three-way exchanges, total number of
transplants, and total weight of the selected exchanges.

The following snippet gives an example output file. We can first note that the
solution is given by exchanges `0` and `2`, giving a total of 4 transplants in
two two-way exchanges, and for a total weight of 12.121. Afterwards we see the
complete list of exchanges. Looking at exchange 0, we see that it has no
alternative exchanges, and a total weight of 8.072. It contains two pairs,
firstly the pair containing donor 3 and recipient 3 and then the pair
containing donor 4 and recipient 4.

We can also look at exchange `4` to see an example of a chain. This is a chain
because the first donor (i.e., the first element in the `cycle` list, has
`a=true`, and no `p` key. As `d=1`, this is donor 1 and donor 1 is
non-directed. In this exchange, donor 1 would donate to recipient 3 in the next
element of `cycle`, who is paired with donor 3, and donor 3 would donate to
recipient 4 in the last element of `cycle`. Note that in a chain, the final
transplant has `dif=0`, `s=0`, `tb=0`, as there is no transplant from the final
donor back to the first pair.

.. code-block:: json

    {
        "algorithm": "UKLKSS Objectives",
        "exchange_data": [
            {
                "description": "UKLKSS Objectives",
                "exchanges": [
                    "0",
                    "2"
                ],
                "three_way_exchanges": 0,
                "total_transplants": 4.0,
                "two_way_exchanges": 2,
                "weight": 12.121
            }
        ],
        "output": {
            "all_cycles": {
                "0": {
                    "alt": [],
                    "backarcs": 0,
                    "cycle": [
                        {
                            "d": "3",
                            "dif": 3,
                            "p": "3",
                            "s": 1.0,
                            "tb": 0.036
                        },
                        {
                            "d": "4",
                            "dif": 3,
                            "p": "4",
                            "s": 1.0,
                            "tb": 0.036
                        }
                    ],
                    "weight": 8.072
                },
                "2": {
                    "alt": [],
                    "backarcs": 0,
                    "cycle": [
                        {
                            "a": true,
                            "d": "1",
                            "dif": 3,
                            "s": 1.0,
                            "tb": 0.049
                        },
                        {
                            "d": "2",
                            "dif": 0,
                            "p": "2",
                            "s": 0,
                            "tb": 0
                        }
                    ],
                    "weight": 4.049
                },
                "3": {
                    "alt": [],
                    "backarcs": 0,
                    "cycle": [
                        {
                            "a": true,
                            "d": "1",
                            "dif": 3,
                            "s": 1.0,
                            "tb": 0.036
                        },
                        {
                            "d": "3",
                            "dif": 0,
                            "p": "3",
                            "s": 0,
                            "tb": 0
                        }
                    ],
                    "weight": 4.036
                },
                "4": {
                    "alt": [
                        "0"
                    ],
                    "backarcs": 2,
                    "cycle": [
                        {
                            "a": true,
                            "b": "3",
                            "d": "1",
                            "dif": 3,
                            "s": 1.0,
                            "tb": 0.036
                        },
                        {
                            "b": "0",
                            "d": "3",
                            "dif": 3,
                            "p": "3",
                            "s": 1.0,
                            "tb": 0.036
                        },
                        {
                            "d": "4",
                            "dif": 0,
                            "p": "4",
                            "s": 0,
                            "tb": 0
                        }
                    ],
                    "weight": 8.072
                }
            }
        }
    }


Adding more
===========

Feel free to either file issues on Gitlab or get in touch if you wish to have
more formats added. Include specifics on the file formats
