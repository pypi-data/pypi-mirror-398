# fbnconfig

[![pypi](https://img.shields.io/pypi/v/fbnconfig)](https://pypi.org/project/fbnconfig/)
[![python](https://img.shields.io/pypi/pyversions/fbnconfig.svg)](https://pypi.python.org/pypi/fbnconfig)

fbnconfig is a Python library (and commandline tool) to allow a declarative description of a LUSID
environment. It allows you to specify the desired state and, when you deploy, it converges the
LUSID environment to your desired state by creating, updating, or deleting entities within LUSID
so that the LUSID environment and the desired state match.

## Getting started

fbnconfig is available from PyPi

```cli
pip install fbnconfig
```

## Running the command

```cli
fbnconfig -e https://foo.lusid.com -t <token> run path/to/script.py
```

This will apply the deployment script (script.py) to the foo.lusid.com domain.

For a list of commands that let you view what's already deployed, use `fbnconfig --help`.

## Authentication

fbnconfig needs a valid LUSID url and a token to create and modify a LUSID environment.
The token will most likely be a personal access token (PAT), but could be a token from an
authentication exchange. For more information on PATs and how to create them, start by reading
[What is a personal access token?](https://support.lusid.com/knowledgebase/article/KA-01911/) on
FINBOURNE's Knowledge Base.

We recommend configuring the url and token as environment variables:

```environment
FBN_ACCESS_TOKEN=xyzabc1234
LUSID_ENV=https://foo.lusid.com
fbnconfig setup
```

Alternatively, you can use the commandline:

```cli
fbnconfig setup -e https://foo.lusid.com -t xyzabc1234
```

## One time setup

Before being able to run a deployment, a one time per-domain setup is required. This creates a 
required CustomEntityDefinition where deployment logs are stored. 

To run using the cli, assuming the appropriate environment variables are set, then run the following:

```cli
fbnconfig setup
```

To run using the library:

```python
import fbnconfig
import os

lusid_env = os.environ["LUSID_ENV"]
token = os.environ["FBN_ACCESS_TOKEN"]
client = fbnconfig.create_client(lusid_env, token)
fbnconfig.setup(client)
```

## Writing the deployment script

A fbnconfig configure script is a Python file that includes the `configure(env):` function. When you
create an fbnconfig configure script, you must define one or more `Deployments`.

For example, the following code is a valid fbnconfig configure script. The configure script defines
the desired state, and running it changes the remote LUSID environment to match.

```Python
from fbnconfig import drive
from fbnconfig import Deployment


def configure(env):
    f1 = drive.FolderResource(id="base_folder", name="my_folder", parent=drive.root)
    return Deployment("my_deployment", [f1])
```

* Configure scripts need to import references resource like a normal Python
  script would.
* The `configure(env):`  function is the entrypoint, which should return a `Deployment`.
* `Deployments` contain one or more resources. In this case, the `Deployment` contains a single
  `FolderResource` Resource that's saved in the `f1` variable.

When we run this script the first time it will create a folder in LUSID Drive called `my_folder`.
The second time we run it, fbnconfig knows the folder already exists and will not make any changes.
If we change the name of the folder (for example `name="another_name"`) and run fbnconfig again it
will rename the folder in LUSID Drive.

### Deployment and Resource Ids

Deployments require an `id`. In this example we define a value of `my_deployment` for the
Deployment's `id` when we return the Deployment object.  

Be careful if you change the ID of a Deployment. If you change the ID and re-run the configure
script, fbnconfig creates a new LUSID environment with a new Deployment ID and new Resources.
The previous Deployment's Resources are not automatically removed.

Each Resource must also have an `id` and these `id`s must be unique within the fbnconfig Deployment.
In this example, we use `id="base_folder"` to uniquely identify the folder Resource we create.

* We can change the `name` of a folder and it will get renamed
  because it has the same `id`.
* If we change the `id` then the existing folder will be deleted and a new one will be created. Note
  that the original folder does not persist, because fbnconfig configure scripts are declarative
  fbnconfig makes the LUSID state match the configure file state. If the original folder disappears
  from the configure file, fbnconfig makes the original folder disappear from the corresponding
  LUSID environment.
* The Python variable `f1` that references the folder is only used to identify the resource within
  the Python configure script. This variable is not used for tracking changes in LUSID, therefore
  changing the Python variable names does not affect what gets deployed.

## Dependencies

Resources may need to reference other resources. For example, the following code creates the nested
folder Resources.

```Python
def configure(env):
    f1 = drive.FolderResource(id="base_folder", name="my_folder", parent=drive.root)
    f2 = drive.FolderResource(id="sub_folder", name="my_subfolder", parent=f1)
    return Deployment("my_deployment", [f1, f2])
```

If we run this it will create the structure `/my_folder/my_subfolder`. Using the Python variable
names we say that `my_subfolder` (`f1` in the script) is a subfolder of its parent `my_folder`
(`f2` in the script).  Relationships are defined by the Python variables, in this case `parent=f1`.

When we have nested structures like this, fbnconfig creates the parents before the children. For
example, `f1` would get created (or updated) before `f2`, and if they are removed from the
deployment then `f2` will be deleted before `f1`.

This example references both folders (`[f1, f2]`), however we could instead reference just the
subfolder (`[f2]`). Because `f2` depends on `f1`, `f1` will be implicitly included.

## Dependencies outside the deployment

When we define a Deployment in a configure script and use fbnconfig to create the corresponding
LUSID environment, all the underlying Resources are fully managed by fbnconfig. This means we want
to use fbnconfig to manage all related Resources within a single Deployment.

However, if we need to establish a relationship between existing Resources and our configure script,
we can use a `Ref`. In the following example, we account for the `downloads` folder which already
exists because it has been created manually or is part of another Deployment.

```Python
def configure(env):
    f1 = drive.FolderRef(id="downloads", name="downloads")
    f2 = drive.FolderResource(id="sub_folder", name="my_subfolder", parent=f1)
    return Deployment("my_deployment", [f1, f2])
```

* This code will create `sub_folder` within the existing `downloads` Resource. We tell fbnconfig
  that `downloads` already exists by using the `drive.FolderRef()` function instead of
  `drive.FolderResource()`.
* If `downloads` doesn't exist at the time this is run, we get an error.
* The `downloads` folder will be the parent of `sub_folder`, but it won't be managed within this
  Deployment.
* If `f1` is removed, it won't get deleted because it is not being managed in this deployment.

## The vars file

To aid with using the same script for dev, uat, and prod, fbnconfig takes a commandline argument to
a json file called the "vars file". The vars file (called `env` in the examples above) is
parsed and passed into the configure function.

For example, suppose we wanted to use different email for dev and prod (like the environment
variable example above).

We would:

1. Create two vars files.

```json
// prod.json                                    // dev.json
{                                               {
    "email": "prod@company.com"                     "email": "dev@company.com"
}                                               }
```

1. Reference the files from the script var env.

    ```Python
    def configure(env):
        export_user = identity.UserResource(
            id="user2",
            ...
            email_address=env.email,
        )
    ```

2. Run the following command to use the `dev@company.com` email..

    ```cli
    fbnconfig -e https://dev.lusid.com -v dev.json script.py
    ```

These vars files can be comitted to the repo to capture variations between environments. For
secrets, it's better to use explicit environment variables in the script (see below).

## Using Python in the script

A deployment script is normal Python, so Python language features are available. For example
variables and f-strings. To allow values to depend on the environment, you can use `os.environ` to
initialize the variables. This is useful when setting up secrets in the config store.

For example, the following code:

1. Passes the secret as an environment variable.
2. Makes an http request or use a library from a vault provider to source the
secret.
3. Uses the secret inside the configure function.

```Python
import os

company = os.environ["company"]

def configure(env):
    export_user = identity.UserResource(
        id="user2",
        ...
        email_address=f"exports@{company}",
        login=f"exports@{company}",
    )
```

You can even create resources in a loop, for example:

```Python
def configure(env):
    folders = [
        drive.FolderResource(id=f"folder_{i}", name="i", parent=drive.root)
        for i in range(0, 10)
    ]
    return Deployment('ten-folders', folders)
```

The Python variables for the Resources need to be added to the deployment and each Resource must
have a unique `id`.

## Using fbnconfig as a library

Using fbnconfig from the commandline dynamically loads your Python script and executes the
Deployment. In some cases (for example using fbnconfig as part of another application) you can call
it from Python as well.

The following example creates an empty deployment called "my-jobs":

```Python
from os import environ
from fbnconfig import Deployment, deploy


def configure(env):
    return Deployment("my-jobs", [])


host_vars = {}
lusid_url = "https://foo.lusid.com"
token = environ["MY_TOKEN_VAR"]
deployment = configure(host_vars)
deploy(deployment, lusid_url, token)
```
