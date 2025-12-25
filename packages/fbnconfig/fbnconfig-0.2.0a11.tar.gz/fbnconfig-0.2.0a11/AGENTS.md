# fbnconfig Library Analysis

## Overview

**fbnconfig** is a declarative infrastructure-as-code library for managing LUSID (Financial Software Platform) environments. It provides a Python-based framework for defining desired state configurations and automatically converging live environments to match those configurations through create, update, and delete operations.

### Key Characteristics
- **Declarative Configuration**: Users define desired state, not imperative steps
- **State Management**: Tracks deployed resources via LUSID CustomEntityDefinitions
- **Dependency Resolution**: Automatically orders operations based on resource dependencies
- **Idempotent Operations**: Safe to run multiple times; only applies necessary changes
- **Python-First**: Configuration scripts are Python code with type hints and validation

---

## Architecture

### Core Components

#### 1. **Resource System** (`resource_abc.py`)
The foundation of the library, providing base classes and registration mechanism:

```python
# Two main abstractions:
class Resource(ABC):  # Managed resources
    - read()   # Check current state
    - create() # Create new resource
    - update() # Update existing resource
    - delete() # Remove resource
    - deps()   # Return dependencies

class Ref(ABC):  # References to existing resources
    - attach() # Verify resource exists
```

**Key Features**:
- Resource registry system for dynamic lookup
- Decorator-based registration: `@register_resource()`
- Type-safe resource references
- Pydantic models for validation and serialization

#### 2. **Deployment Engine** (`deploy.py`)
Orchestrates the deployment lifecycle:

**Flow**:
1. **Recurse Resources**: Flatten deployment into dependency-ordered list
2. **Load State**: Fetch current deployment state from LUSID logs
3. **Create/Update/Attach**: Process each resource
   - New resources → `create()`
   - Existing resources → `update()`
   - References → `attach()`
4. **Clean Up**: Delete resources no longer in desired state
5. **Log Changes**: Record final state for each resource

**Key Functions**:
- `run()`: Main deployment executor
- `recurse_resources()`: Dependency graph traversal
- `dump_deployment()`: Serialize to JSON
- `undump_deployment()`: Deserialize from JSON

#### 3. **State Tracking** (`log.py`)
Manages deployment history using LUSID CustomEntities:

**Storage Schema**:
```json
{
  "identifiers": [{"type": "resource", "value": "deployment_id_resource_id"}],
  "fields": [
    {"name": "deployment", "value": "deployment_id"},
    {"name": "resourceType", "value": "ResourceClassName"},
    {"name": "dependencies", "value": ["dep1", "dep2"]},
    {"name": "resource", "value": "resource_id"},
    {"name": "state", "value": "{...}"}
  ]
}
```

**Capabilities**:
- Track what resources are deployed
- Store resource state for update comparison
- Record dependencies for proper deletion order
- Query deployment history and dependencies

#### 4. **HTTP Client** (`http_client.py`)
Thin wrapper around httpx for LUSID API communication:
- Bearer token authentication
- Base URL configuration
- Request/response handling
- Retry logic via backoff handler

#### 5. **CLI Interface** (`main.py`)
Command-line tool built with Click:

```bash
# Setup (one-time per domain)
fbnconfig setup -e https://foo.lusid.com -t <token>

# Deploy configuration
fbnconfig run script.py -v vars.json

# Inspect deployments
fbnconfig log list [deployment_id]
fbnconfig log get <deployment> <resource_id>
fbnconfig log deps <deployment> <resource_id>
fbnconfig log uses <deployment> <resource_id>
fbnconfig log rm <deployment> <resource_id> [--force|--recursive]

# Dump/restore
fbnconfig dump script.py -v vars.json > deployment.json
fbnconfig rundump deployment.json
```

---

## Resource Modules

The library includes 27 resource modules covering different LUSID domains:

### Infrastructure Resources
- **`drive.py`** (287 lines): File system operations
  - `FolderResource`, `FolderRef`, `FileResource`
  - Manages hierarchical folder structures and files
  
- **`scheduler.py`** (616 lines): Job scheduling
  - `ImageResource`, `ImageRef`: Docker image management
  - `JobResource`, `JobRef`: Job definitions
  - `ScheduleResource`: Job scheduling

### Identity & Access Management
- **`identity.py`** (406 lines): User management
  - `UserResource`, `UserRef`: User accounts
  - `ApiKeyResource`: API key generation

- **`access.py`** (643 lines): Authorization policies
  - `PolicyResource`, `PolicyRef`: Access policies
  - `RoleResource`, `RoleRef`: Role definitions
  - `PolicyCollectionResource`: Policy grouping

### Data Management
- **`property.py`** (292 lines): Property definitions
  - `DefinitionResource`, `DefinitionRef`: Custom properties

- **`datatype.py`**: Data type definitions
  - `ResourceId`: Scope/code pairs

- **`customentity.py`**: Custom entity definitions

- **`custom_data_model.py`**: Custom data model definitions
  - `CustomDataModelResource`, `CustomDataModelRef`: JSON schema-based data models

- **`sequence.py`**: Sequence definitions

- **`identifier_definition.py`** (265 lines): Identifier definitions

### Configuration & Recipes
- **`configuration.py`** (356 lines): Configuration store
  - `ConfigurationItemResource`: Key-value configuration

- **`recipe.py`**: Valuation recipes

- **`cutlabel.py`**: Cut label definitions

### Financial Entities
- **`transaction_type.py`** (290 lines): Transaction configurations

- **`side_definition.py`**: Transaction side definitions

- **`compliance.py`** (473 lines): Compliance rules

- **`fund_configurations.py`**: Fund setup

- **`fund_accounting.py`** (438 lines): Accounting configurations

- **`corporate_action.py`**: Corporate action sources

- **`instrument_events.py`**: Instrument event definitions

### Advanced Features
- **`workflows.py`** (904 lines): Workflow definitions
  - Largest module - complex workflow orchestration

- **`lumi.py`** (782 lines): LUMI (Luminesce) queries
  - SQL query management

- **`horizon.py`**: Horizon integrations
  - External system connections

- **`notifications.py`** (479 lines): Event notifications

- **`workspace.py`**: Workspace management

- **`reference_list.py`**: Reference data lists

- **`posting_module.py`**: Chart of accounts posting rules

- **`cleardown_module.py`**: Cleardown configurations

---

## Design Patterns

### 1. **Resource/Ref Pattern**
Every LUSID entity type has two variants:
- `XxxResource`: Managed by deployment, full CRUD lifecycle
- `XxxRef`: Reference to existing entity, read-only

```python
# Managed folder
f1 = drive.FolderResource(id="my_folder", name="Reports", parent=drive.root)

# Reference to existing folder
f2 = drive.FolderRef(id="existing", folder_path="/Shared/Reports")
```

### 2. **Dependency Injection via Python Variables**
Dependencies expressed through Python object references:

```python
def configure(env):
    parent = drive.FolderResource(id="parent", name="Parent", parent=drive.root)
    child = drive.FolderResource(id="child", name="Child", parent=parent)
    # parent.deps() returns [drive.root]
    # child.deps() returns [parent]
    return Deployment("folders", [parent, child])
```

### 3. **Pydantic Model Configuration**
Standard configuration for all resources:

```python
std_config = ConfigDict(
    populate_by_name=True,
    alias_generator=AliasGenerator(
        serialization_alias=to_camel,      # Python → API
        validation_alias=to_camel,         # API → Python
    )
)
```

Enables:
- Snake_case in Python, camelCase for API
- Automatic validation
- JSON serialization
- Round-trip dump/restore

### 4. **State Comparison for Updates**
Resources compare current state with desired state:

```python
def update(self, client, old_state):
    current = self.read(client, old_state)
    if current == desired:
        return None  # No change
    # Apply only necessary updates
    return new_state
```

### 5. **Context-Aware Serialization**
Pydantic context for different serialization modes:

```python
# Dumping: Convert Resource refs to {"$ref": "id"}
resource.model_dump(context={"style": "dump"})

# Restoring: Resolve {"$ref": "id"} back to Resources
Resource.model_validate(data, context={"style": "dump", "$refs": objects})
```

---

## Key Workflows

### 1. **First Time Setup**
```python
# Creates CustomEntityDefinition for deployment logs
client = create_client(lusid_url, token)
setup(client)
```

### 2. **Resource Creation**
```
User Script → configure(env) → Deployment
            ↓
deploy.run() → recurse_resources() → [ordered_resources]
            ↓
For each resource:
  - Check log for existing entry
  - If not found: resource.create()
  - log.record(deployment, resource, state)
```

### 3. **Resource Update**
```
For each resource:
  - Find in log
  - resource.update(client, old_state)
  - If changed: log.record(deployment, resource, new_state)
  - If unchanged: print "nochange"
```

### 4. **Resource Deletion**
```
For each logged resource not in new deployment:
  - Get resource class from registry
  - Sort by reverse dependency order
  - ResourceClass.delete(client, old_state)
  - log.remove(deployment, resource_id)
```

### 5. **Dependency Resolution**
```
recurse_resources():
  - Depth-first traversal of deps()
  - Build ordered list (dependencies first)
  - Validate unique resource IDs
  - Detect cycles (RuntimeError)
```

---

## Extension Points

### Adding a New Resource Type

1. **Create Module** (e.g., `my_resource.py`)

```python
from fbnconfig.resource_abc import Resource, Ref, register_resource
from pydantic import BaseModel, Field

@register_resource()
class MyResourceRef(BaseModel, Ref):
    id: str = Field(exclude=True)
    name: str
    
    def attach(self, client):
        # Verify resource exists in LUSID
        response = client.get(f"/api/myresources/{self.name}")
        if response.status_code == 404:
            raise RuntimeError(f"MyResource {self.name} not found")

@register_resource()
class MyResourceResource(BaseModel, Resource):
    id: str = Field(exclude=True)
    name: str
    description: str | None = None
    dependency: MyResourceRef | None = None  # Optional dependency
    
    def read(self, client, old_state):
        """Fetch current state from LUSID"""
        return client.get(f"/api/myresources/{self.name}").json()
    
    def create(self, client):
        """Create new resource"""
        body = self.model_dump(mode="json", exclude={"id"})
        response = client.post("/api/myresources", json=body)
        return {
            "name": self.name,
            "description": self.description,
        }
    
    def update(self, client, old_state):
        """Update if changed"""
        current = self.read(client, old_state)
        if current["description"] == self.description:
            return None  # No change
        body = self.model_dump(mode="json", exclude={"id"})
        client.put(f"/api/myresources/{self.name}", json=body)
        return {"name": self.name, "description": self.description}
    
    @staticmethod
    def delete(client, old_state):
        """Delete resource"""
        client.delete(f"/api/myresources/{old_state.name}")
    
    def deps(self):
        """Return dependencies"""
        return [self.dependency] if self.dependency else []
```

2. **Register in `__init__.py`**

```python
from fbnconfig import my_resource  # Triggers @register_resource
```

3. **Write Tests** (`tests/unit/test_my_resource.py`)

```python
import respx
from fbnconfig import my_resource

class TestMyResource:
    def test_create(self):
        with respx.mock:
            route = respx.post("/api/myresources").mock(return_value=...)
            resource = my_resource.MyResourceResource(
                id="test", name="Test", description="Desc"
            )
            resource.create(client)
            assert route.called
```

4. **Add Integration Test** (`tests/integration/int_my_resource.py`)

5. **Document** (add example to README)

---

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Mock HTTP responses with `respx`
- Test each CRUD operation independently
- Validate serialization/deserialization
- Test dependency resolution
- **913 total unit tests** (passing)

Example pattern:
```python
@respx.mock
def test_create_resource():
    route = respx.post("/api/endpoint").mock(return_value=Response(200, json={...}))
    resource.create(client)
    assert route.called
    assert route.calls.last.request.json() == expected_body
```

### Integration Tests (`tests/integration/`)
- Test against real LUSID environment
- Require authentication
- Full end-to-end deployment scenarios
- Clean up after tests

### Test Coverage
Run with: `pytest tests/unit/ --cov=fbnconfig --cov-report=html`

---

## Common Patterns in Existing Resources

### Pattern: Autogenerated IDs
Some LUSID resources generate IDs server-side:

```python
def create(self, client):
    response = client.post("/api/endpoint", json=body)
    self.generated_id = response.json()["id"]
    return {"id": self.generated_id, ...}

def update(self, client, old_state):
    # Use old_state.id to update
    client.put(f"/api/endpoint/{old_state.id}", json=body)
```

### Pattern: Scope/Code Identifiers
Many LUSID entities use scope/code pairs:

```python
from fbnconfig.coretypes import ResourceId

@register_resource()
class MyResource(BaseModel, Resource):
    id: str = Field(exclude=True)
    resource_id: ResourceId  # {scope: "...", code: "..."}
    
    def create(self, client):
        body = self.model_dump(...)
        client.post(f"/api/endpoint/{self.resource_id.scope}/{self.resource_id.code}", json=body)
```

### Pattern: Nested Resources
Resources with child collections:

```python
@register_resource()
class ParentResource(BaseModel, Resource):
    children: List[ChildResource] = []
    
    def deps(self):
        return self.children  # Children created first
```

### Pattern: File Content
Resources that reference file content:

```python
from pathlib import Path

@register_resource()
class FileResource(BaseModel, Resource):
    content_path: Path = Field(exclude=True)
    
    def create(self, client):
        content = self.content_path.read_text()
        body = {"content": content, ...}
        client.post("/api/files", json=body)
```

### Pattern: Reference Resolution During Restore
When restoring from dump, resolve `{"$ref": "id"}` back to objects:

```python
def ref_validator(v, info):
    if isinstance(v, dict) and "$ref" in v:
        refs = info.context.get("$refs", {})
        return refs[v["$ref"]]
    return v

DependencyType = Annotated[
    Union[ResourceType, ResourceRef],
    BeforeValidator(ref_validator)
]
```

---

## Development Workflow

### Setup Development Environment
```bash
# Clone and install
git clone git@gitlab.com:finbourne/clientengineering/fbnconfig.git
cd fbnconfig
uv sync
source .venv/bin/activate
```

### Code Quality
```bash
# Lint and format
ruff check --fix
ruff format

# Type checking
pyright

# All in one
ruff check --fix && ruff format && pyright
```

### Testing
```bash
# Unit tests only (fast)
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=fbnconfig --cov-report=html

# Integration tests (requires LUSID access)
export FBN_ACCESS_TOKEN="..."
export LUSID_ENV="https://foo.lusid.com"
pytest tests/integration/ -v

# Run in parallel
pytest tests/unit/ -n auto
```

### Building
```bash
# Build package
uv build

# Install locally
pip install dist/fbnconfig-*.whl

# Publish (maintainers only)
uv publish
```

---

## Important Considerations for New Features

### 1. **Resource ID Stability**
- Resource `id` field is the **primary key** in deployment logs
- Changing `id` causes delete + recreate (data loss!)
- Design IDs to be stable across deployments
- Document ID changes in migration guides

### 2. **State Storage**
- State stored in log must be JSON-serializable
- Include enough info to update/delete without re-reading
- Balance completeness vs. storage size
- Don't store sensitive data (tokens, passwords)

### 3. **Dependency Management**
- Circular dependencies cause RuntimeError
- Dependencies must exist before dependents
- Delete in reverse order (dependents first)
- Use `Ref` for external dependencies

### 4. **Update Semantics**
- Compare current vs. desired state carefully
- Don't overwrite server defaults unless specified
- Return `None` if no change needed (important for logs!)
- Handle partial updates when possible

### 5. **Error Handling**
- Distinguish between retryable and non-retryable errors
- Provide clear error messages with context
- Don't swallow exceptions silently
- Use `HTTPStatusError` for API errors

### 6. **API Compatibility**
- Handle API versioning gracefully
- Support optional fields for backwards compatibility
- Document required LUSID version/licenses
- Test against multiple LUSID versions if possible

### 7. **Serialization**
- Use Pydantic validators for complex types
- Implement custom serializers for special cases
- Test round-trip (dump → restore)
- Handle context-dependent serialization

### 8. **Performance**
- Minimize API calls (batch where possible)
- Cache reads during update checks
- Use efficient queries (filters, paging)
- Consider parallel execution for independent resources

---

## Known Limitations

1. **No Rollback**: Failed deployments leave partial state
2. **No Dry Run**: Must deploy to see changes (use `dump` as workaround)
3. **No Drift Detection**: Doesn't alert on manual changes outside fbnconfig
4. **Single Deployment**: Can't split large configs across multiple deployments easily
5. **No Resource Import**: Can't import existing resources into management
6. **Limited Conflict Resolution**: Concurrent deployments may conflict

---

## Resources & References

### Documentation
- **User Guide**: `fbnconfig.md` - Installation and usage
- **Developer Guide**: `readme.md` - Contributing and development
- **Contributing**: `CONTRIBUTING.md` - Code style and practices

### Key Files
- **Core**: `deploy.py`, `resource_abc.py`, `log.py`
- **CLI**: `main.py`
- **HTTP**: `http_client.py`, `backoff_handler.py`
- **Utilities**: `urlfmt.py`, `load_module.py`, `coretypes.py`

### External Dependencies
- **Pydantic** (2.6-2.8): Data validation and serialization
- **httpx** (0.28): HTTP client with async support
- **Click** (8.1+): CLI framework
- **pytest** (8.3): Testing framework
- **respx** (0.22): HTTP mocking for tests
- **ruff** (0.8): Linting and formatting
- **pyright** (1.1+): Static type checking

### LUSID API
- Base URL: `https://{domain}.lusid.com`
- Authentication: Bearer token (PAT or OAuth)
- API Docs: Available in LUSID UI under "API Documentation"

---

## Summary

**fbnconfig** is a mature, well-architected infrastructure-as-code library with:

✅ **Strengths**:
- Clear separation of concerns (Resource, Deployment, Logging, CLI)
- Extensive resource coverage (27 modules, 91+ resource types)
- Strong typing and validation via Pydantic
- Comprehensive test suite (913 unit tests)
- Flexible dependency resolution
- Round-trip serialization support
- Production-ready error handling

⚠️ **Considerations for New Features**:
- Follow established patterns (Resource/Ref, deps, CRUD)
- Ensure state is JSON-serializable
- Test both unit and integration scenarios
- Document ID stability and dependencies
- Handle API errors gracefully
- Consider backwards compatibility

🎯 **Ready for Extension**:
The library is well-prepared for adding new resource types with clear extension points, established patterns, and good test infrastructure. The resource registry system makes adding new types straightforward while maintaining consistency across the codebase.
