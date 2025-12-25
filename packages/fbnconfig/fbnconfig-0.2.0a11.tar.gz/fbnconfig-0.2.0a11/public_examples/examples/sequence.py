from fbnconfig import Deployment, sequence

"""
An example configuration for defining sequences.
The script configures the following entities:
- Sequence
"""


def configure(env):
    seq1 = sequence.SequenceResource(id="seq1", scope="sc1", code="seq1")

    return Deployment("sequence_example", [seq1])
