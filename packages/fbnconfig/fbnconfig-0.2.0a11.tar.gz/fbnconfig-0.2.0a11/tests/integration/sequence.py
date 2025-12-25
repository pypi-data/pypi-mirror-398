from fbnconfig import Deployment, sequence


def configure(env):
    deployment_name = getattr(env, "name", "seq_example")
    seq1 = sequence.SequenceResource(id="seq1", scope=deployment_name, code="seq1")
    return Deployment(deployment_name, [seq1])
