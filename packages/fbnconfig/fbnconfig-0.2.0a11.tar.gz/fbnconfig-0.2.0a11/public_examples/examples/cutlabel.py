from fbnconfig import Deployment, cutlabel

"""
An example configuration for cut labels
The script configures the following entities:
- CutLabel

More information can be found here:
https://support.lusid.com/docs/what-is-a-cut-label
"""


def configure(env):
    ldn_close = cutlabel.CutLabelResource(
        id="ldn-close",
        code="ldn-close",
        display_name="London Close",
        description="The London close cut label",
        cut_local_time=cutlabel.CutTime(hours=16, minutes=30, seconds=0.9999),
        time_zone="Europe/London",
    )
    nyk_close = cutlabel.CutLabelResource(
        id="nyk-close",
        code="nyk-close",
        display_name="New York Close",
        description="The New York close cut label",
        cut_local_time=cutlabel.CutTime(hours=16, minutes=2, seconds=0),
        time_zone="America/New_York",
    )
    return Deployment("cutlabel_example", [nyk_close, ldn_close])
