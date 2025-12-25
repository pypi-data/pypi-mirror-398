from fbnconfig import Deployment, workspace

num_groups = 3
num_items = 2


def make_shared_branch(org, region):
    wksp = workspace.WorkspaceResource(
        id=f"wksp-{org}-{region}",
        visibility=workspace.Visibility.SHARED,
        name=f"{org}-{region}",
        description=f"workspace for {region} {org}",
    )
    items = [
        workspace.WorkspaceItemResource(
        id=f"item-{org}-{region}-{i}",
        workspace=wksp,
        group=f"group{1 + (i % num_groups)}",
        name=f"item{i}",
        description=f"item {i} version two",
        format=1,
        type="lusid-web-dashboard",
        content={"msg": "some text"},
    ) for i in range(0, num_items)]
    return [wksp] + items


def make_personal_branch(user):
    wksp = workspace.WorkspaceResource(
        id=f"wksp-personal-{user}",
        visibility=workspace.Visibility.PERSONAL,
        name=user,
        description=f"workspace for {user}",
    )
    num_groups = 2
    items = [
        workspace.WorkspaceItemResource(
        id=f"item-personal-{user}-{i}",
        workspace=wksp,
        group=f"group{1 + (i % num_groups)}",
        name=f"myitem{i}",
        description=f"item {i} version two",
        type="lusid-web-dashboard",
        format=1,
        content={"msg": "some text"},
    ) for i in range(0, num_items)]
    return [wksp] + items


def configure(env):
    deployment_name = getattr(env, "name", "workspace_example")
    orgs = ["operations", "equity-trading", "compliance", "risk-management", "market-data"]
    regions = ["emea", "apac", "us", "latam"]
    users = ["bill", "ted", "john", "paul", "ringo", "diana-ross", "florence", "mary-wilson",
        "micheal", "jermaine", "jackie", "marlon", "lionel", "william", "walter", "james-dean"]
    resources = []
    for org in orgs:
        for region in regions:
            resources.extend(make_shared_branch(org, region))
    for user in users:
        resources.extend(make_personal_branch(user))
    return Deployment(deployment_name, resources)
