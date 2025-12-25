import os
from types import SimpleNamespace

from pytest import fixture

import fbnconfig
from fbnconfig import compliance as cp
from fbnconfig import property as pr
from tests.integration.generate_test_name import gen

if os.getenv("FBN_ACCESS_TOKEN") is None or os.getenv("LUSID_ENV") is None:
    raise (
        RuntimeError("Both FBN_ACCESS_TOKEN and LUSID_ENV variables need to be set to run these tests")
    )

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
host_vars = {}
client = fbnconfig.create_client(lusid_env, token)


@fixture()
def deployment_name():
    return gen("compliance")


@fixture()
def portfolio_group(deployment_name):
    scope = deployment_name
    code = "compliance_test_group"
    client.post(f"/api/api/portfoliogroups/{scope}", json={
        "code": code,
        "values": [],
        "displayName": "Compliance Rule test group",
        "description": "Group to support fbnconfig compliance rule int tests"
    })
    yield cp.ResourceId(scope=scope, code=code)
    client.delete(f"/api/api/portfoliogroups/{scope}/{code}")


@fixture()
def base_resources(setup_deployment, portfolio_group):
    deployment_name = setup_deployment.name
    # Create property definition reference
    ccy = pr.DefinitionRef(
        id="prop_ccy",
        domain=pr.Domain.Instrument,
        scope="default",
        code="Currency",
    )
    # Create compliance template
    template1 = cp.ComplianceTemplateResource(
        id="template1",
        scope=deployment_name,
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
    # Create compliance rule
    rule1 = cp.ComplianceRuleResource(
        id="rule1",
        scope=deployment_name,
        code="rule1",
        name="ExampleComplianceRule",
        description="This is an example compliance rule",
        active=True,
        template_id=template1,
        variation="Variation1",
        portfolio_group_id=portfolio_group,
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
    return [template1, rule1]


@fixture()
def setup_deployment(deployment_name):
    print(f"\nRunning for deployment {deployment_name}...")
    yield SimpleNamespace(name=deployment_name)
    # Clean up compliance resources after tests
    try:
        fbnconfig.deployex(fbnconfig.Deployment(deployment_name, []), lusid_env, token)
        client.delete(f"/api/api/compliance/rules/{deployment_name}/rule1")
        client.delete(f"/api/api/compliance/templates/{deployment_name}/template1")
    except Exception:
        pass  # Ignore cleanup errors


def test_create(setup_deployment, base_resources):
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # Verify template was created
    template_response = client.get(
        f"/api/api/compliance/templates/{setup_deployment.name}/template1"
    ).json()
    assert template_response["id"]["scope"] == setup_deployment.name
    assert template_response["id"]["code"] == "template1"
    assert template_response["description"] == "This is the first compliance template"
    assert len(template_response["variations"]) == 1
    assert template_response["variations"][0]["label"] == "Variation1"
    # Verify rule was created
    rule_response = client.get(f"/api/api/compliance/rules/{setup_deployment.name}/rule1").json()
    assert rule_response["id"]["scope"] == setup_deployment.name
    assert rule_response["id"]["code"] == "rule1"
    assert rule_response["name"] == "ExampleComplianceRule"
    assert rule_response["description"] == "This is an example compliance rule"
    assert rule_response["active"] is True
    assert rule_response["templateId"]["scope"] == setup_deployment.name
    assert rule_response["templateId"]["code"] == "template1"
    assert rule_response["variation"] == "Variation1"


def test_nochange(setup_deployment, base_resources):
    # given we have deployed the base case
    deployment = fbnconfig.Deployment(setup_deployment.name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # when we apply it again
    update = fbnconfig.deployex(deployment, lusid_env, token)
    # then there are no changes
    template_changes = [a.change for a in update if a.type == "ComplianceTemplateResource"]
    rule_changes = [a.change for a in update if a.type == "ComplianceRuleResource"]
    assert template_changes == ["nochange"]
    assert rule_changes == ["nochange"]


def test_teardown(setup_deployment, base_resources):
    deployment_name = setup_deployment.name
    # given we have deployed the base case
    deployment = fbnconfig.Deployment(deployment_name, base_resources)
    fbnconfig.deployex(deployment, lusid_env, token)
    # when we remove all the resources
    empty = fbnconfig.Deployment(deployment_name, [])
    update = fbnconfig.deployex(empty, lusid_env, token)
    # then resources are removed
    template_changes = [a.change for a in update if a.type == "ComplianceTemplateResource"]
    rule_changes = [a.change for a in update if a.type == "ComplianceRuleResource"]
    assert template_changes == ["remove"]
    assert rule_changes == ["remove"]


def test_update(setup_deployment, base_resources, portfolio_group):
    deployment_name = setup_deployment.name
    # Given we have deployed the base case
    initial = fbnconfig.Deployment(deployment_name, base_resources)
    fbnconfig.deployex(initial, lusid_env, token)
    # when we update resources
    ccy = pr.DefinitionRef(
        id="prop_ccy",
        domain=pr.Domain.Instrument,
        scope="default",
        code="Currency",
    )
    # Update the template with different description
    updated_template = cp.ComplianceTemplateResource(
        id="template1",
        scope=deployment_name,
        code="template1",
        tags=["tag1", "tag2", "updated"],  # Added tag
        description="This is the updated first compliance template",  # Changed description
        variations=[
            cp.ComplianceTemplateVariation(
                label="Variation1",
                description="This is the updated first variation of the template",  # Changed
                outcome_description="This variation checks for updated specific conditions",  # Changed
                steps=[
                    cp.BranchStep(
                        label="Branch-Step-1",
                        parameters=[
                            cp.ComplianceTemplateParameter(
                                name="param1",
                                description="Updated parameter for branch step",  # Changed description
                                type="string",
                            )
                        ]
                    ),
                ],
                referenced_group_label=None
            )
        ]
    )
    # Update the rule with different description
    updated_rule = cp.ComplianceRuleResource(
        id="rule1",
        scope=deployment_name,
        code="rule1",
        name="UpdatedExampleComplianceRule",  # Changed name
        description="This is an updated example compliance rule",  # Changed description
        active=False,  # Changed active status
        template_id=updated_template,
        variation="Variation1",
        portfolio_group_id=portfolio_group,
        parameters={
            # Changed value
            "Branch-Step-1.BranchingKey": cp.GroupBySelectorComplianceParameter(value="2"),
        },
        properties=[
            cp.PropertyListItem(
                key=ccy,
                value=cp.PropertyValue(
                    label_value="EUR",  # Changed currency
                ),
            )
        ]
    )
    updated_resources = [updated_template, updated_rule]
    # and deploy it
    updated_deployment = fbnconfig.Deployment(deployment_name, updated_resources)
    update = fbnconfig.deployex(updated_deployment, lusid_env, token)
    # then we expect both resources to change
    template_changes = [a.change for a in update if a.type == "ComplianceTemplateResource"]
    rule_changes = [a.change for a in update if a.type == "ComplianceRuleResource"]
    assert template_changes == ["update"]
    assert rule_changes == ["update"]
    # and they have the new values
    updated_template_response = client.get(
        f"/api/api/compliance/templates/{deployment_name}/template1"
    ).json()
    assert updated_template_response["description"] == "This is the updated first compliance template"
    updated_rule_response = client.get(
        f"/api/api/compliance/rules/{deployment_name}/rule1"
    ).json()
    assert updated_rule_response["name"] == "UpdatedExampleComplianceRule"
    assert updated_rule_response["description"] == "This is an updated example compliance rule"
    assert updated_rule_response["active"] is False
