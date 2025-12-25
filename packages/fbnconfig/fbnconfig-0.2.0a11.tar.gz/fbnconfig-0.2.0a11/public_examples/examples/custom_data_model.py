from fbnconfig import Deployment
from fbnconfig import custom_data_model as cdm

"""
An example configuration for a custom data model.
The script configures the following entities:
- CustomDataModel

More information can be found here:
https://support.lusid.com/docs/creating-custom-data-models-for-entities
"""


def configure(env):
    cdm_resource = cdm.CustomDataModelResource(
        id="cdm1",
        entity_type="Instrument",
        resource_id=cdm.ResourceId(scope="CustomDataModels", code="ExampleCustomDataModel"),
        display_name="Example Custom Data Model",
        description="An example custom data model for instruments",
        parent_data_model=None,
        conditions="",
        properties=None,
        identifier_types=None,
        recommended_sort_by=None,
    )
    return Deployment("custom_data_model_example", [cdm_resource])
