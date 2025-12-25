
from fbnconfig import Deployment
from fbnconfig import compliance as cp
from fbnconfig import property as pr


def configure(env):
    ccy = pr.DefinitionRef(
        id="prop_ccy",
        domain=pr.Domain.Instrument,
        scope="default",
        code="Currency",
    )
    template1 = cp.ComplianceTemplateResource(
        id="template1",
        scope="sc1",
        code="template1",
        tags=["tag1", "tag2"],
        description="This is the first compliance template",
        variations=[
            cp.ComplianceTemplateVariation(
                label="Variation1",
                description="This is the first variation of the template",
                outcome_description="This variation checks for specific conditions",
                steps=[
                    cp.BranchStep(
                        label="Branch-Step-1",
                        parameters=[
                            cp.ComplianceTemplateParameter(
                                name="param1",
                                description="Parameter for branch step",
                                type="string",
                            )
                        ]
                    ),
                ],
                referenced_group_label=None
            )
        ]
    )
    rule1 = cp.ComplianceRuleResource(
        id="rule1",
        scope="sc1",
        code="rule1",
        name="ExampleComplianceRule",
        description="This is an example compliance rule",
        active=True,
        template_id=template1,
        variation="Variation1",
        portfolio_group_id=cp.ResourceId(
            scope="robtest",
            code="group10"
        ),
        parameters={
            "Branch-Step-1.BranchingKey": cp.GroupBySelectorComplianceParameter(value="1"),
        },
        properties=[
            cp.PropertyListItem(
                key=ccy,
                value=cp.PropertyValue(
                    label_value="USD",
                ),
            )
        ]
    )
    return Deployment("compliance_example", [template1, rule1])
