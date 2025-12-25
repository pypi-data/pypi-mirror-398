Stick to PEP8 style guide, here's a practical set of rules: https://luminousmen.com/post/the-ultimate-python-style-guidelines

* snake_case for variables and method names
* _snake_case with leading underscore for 'private' variables
* PascalCase for class names
* UPPERCASE for Enum names

Running the below command will identify violations of our ruff config as well as typing issues
and will fix the ones that can be autocorrected.
```bash
ruff check --fix && ruff format -e && pyright
```


The fields in the *state* stored in the deployments can be either snake_case or camelCase, as long as consistent for a given resource.
