from fbnconfig import Deployment
from fbnconfig import reference_list as rl


def configure(env):
    strlist1 = rl.ReferenceListResource(
        id="strlist1",
        scope="sc1",
        code="strlist1",
        name="strlist_name",
        tags=["tag1", "tag2"],
        reference_list=rl.StringList(
            values=["value1", "value2", "value3"],
        )
    )
    instrlist1 = rl.ReferenceListResource(
        id="instrlist1",
        scope="sc1",
        code="instrlist1",
        name="instrlist1",
        tags=["tag1", "tag2"],
        reference_list=rl.InstrumentList(
            values=[
                "CCY_USD",
            ]
        )
    )
    return Deployment("reference_list_example", [strlist1, instrlist1])
