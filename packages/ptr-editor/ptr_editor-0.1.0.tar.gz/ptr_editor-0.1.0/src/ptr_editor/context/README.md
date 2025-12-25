# Context Management System

The `context` submodule provides a comprehensive configuration and service management system for ptr-editor, built on three core concepts:

1. **Defaults** - Immutable, context-scoped configuration values
2. **Services** - Mutable, global singleton registry
3. **Service Config** - Extensible, context-scoped service behavior configuration

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                     Context System                            │
├──────────────────────────────────────────────────────────────┤
│  Defaults (defaults.py)                                       │
│  - Thread-safe, immutable configuration                       │
│  - Context-scoped using contextvars                           │
│  - Default values for creating PTR elements                   │
├──────────────────────────────────────────────────────────────┤
│  Services (services.py)                                       │
│  - Global singleton registry                                  │
│  - Lazy initialization                                        │
│  - Application-wide services (AGM, validators, etc.)          │
├──────────────────────────────────────────────────────────────┤
│  Service Config (service_config.py)                           │
│  - Context-scoped service behavior configuration              │
│  - Extensible by third-party modules                          │
│  - Controls HOW services operate                              │
├──────────────────────────────────────────────────────────────┤
│  Presets (presets.py)                                         │
│  - Pre-configured defaults for common scenarios               │
│  - Mission-specific configurations (JANUS, etc.)              │
└──────────────────────────────────────────────────────────────┘
```

## Key Principles

### Defaults vs Services vs Service Config

| Aspect | Defaults | Services | Service Config |
|--------|----------|----------|----------------|
| **Mutability** | Immutable | Mutable | Immutable |
| **Scope** | Context-local | Global | Context-local |
| **Thread-safe** | Yes (contextvars) | No | Yes (contextvars) |
| **Purpose** | Default values for data | Singleton instances | Service behavior |
| **Example** | Default target="Jupiter" | AGMConfiguration instance | Validation ruleset |
| **When to use** | Default attribute values | Shared resources | Runtime behavior control |

## Modules

### defaults.py

Provides immutable, context-managed default values for creating PTR elements using Python's `contextvars` for thread-safe context management.

**Key Classes:**
- `DefaultsConfig` - Top-level defaults container
- `PointingDefaults` - Pointing-specific defaults (target, boresight, etc.)

**Usage:**
```python
from ptr_editor.context import PointingDefaults, get_defaults_config

# Temporarily override defaults
with PointingDefaults(target="Mars", designer="JANUS"):
    obs = ObservationRequest()  # Uses Mars as default target

# Access current defaults
config = get_defaults_config()
print(config.pointing.target)  # "Jupiter" (default)
```

**Factory Functions:**
- `from_defaults(attribute_path)` - Create attrs field factories that pull from context

```python
from attrs import define, field
from ptr_editor.context import from_defaults

@define
class ObsRequest:
    target: str = field(factory=from_defaults("pointing.target"))
    # Automatically uses current context default
```

### services.py

Provides a global singleton registry for application services with lazy initialization. Services are mutable, application-wide resources.

**Key Classes:**
- `ServiceRegistry` - Global service container with lazy instantiation

**Usage:**
```python
from ptr_editor.context import get_services

# Register services (typically done at startup)
get_services().register("agm_config", AGMConfiguration)
get_services().register("validator", PTRValidator)

# Access services (lazily initialized)
config = get_services()["agm_config"]
validator = get_services()["validator"]

# Testing with mocks
get_services().set_override("agm_config", MockAGMConfig())
# ... run tests ...
get_services().clear_override("agm_config")
```

**Factory Functions:**
- `from_service(service_name, attribute_path)` - Create attrs field factories that pull from service registry

```python
@define
class Processor:
    config = field(factory=from_service("agm_config"))
```

### service_config.py

Provides an extensible configuration system where modules can register their own configuration schemas that integrate with the context management system.

**Key Classes:**
- `ServiceConfig` - Dynamic container for service configurations
- `ValidationConfig` - Built-in validation behavior configuration
- `ResolutionConfig` - Built-in input resolution configuration

**Usage:**
```python
from ptr_editor.context import ServiceConfig, ValidationConfig

# Use built-in configurations
with ValidationConfig(ruleset="strict", fail_fast=True):
    validator.validate(ptr)

# Register custom configuration
from attrs import define
from ptr_editor.context import register_service_config

@define(frozen=True)
class MyPluginConfig:
    enabled: bool = True
    timeout: int = 30

register_service_config("my_plugin", MyPluginConfig)

# Use custom configuration
with ServiceConfig(my_plugin=MyPluginConfig(timeout=60)):
    plugin = get_services()["my_plugin"]
    plugin.do_work()  # Reads config via get_service_config()
```

**Built-in Configurations:**

**ValidationConfig**
- Controls validation behavior (ruleset, fail_fast, warnings_as_errors)
- Supports rule filtering (enabled_rules, disabled_rules)

**ResolutionConfig**
- Controls input resolution (fuzzy matching, case sensitivity, abbreviations)
- Configurable resolution strategies with priority ordering

**Factory Functions:**
- `from_service_config(service_name, attribute_path)` - Create attrs field factories

```python
@define
class ValidatorOptions:
    ruleset: str = field(
        factory=from_service_config("validation", "ruleset")
    )
```

### presets.py

Pre-configured `DefaultsConfig` instances for common use cases and missions.

**Available Presets:**
- `janus_defaults()` - JANUS mission configuration

**Usage:**
```python
from ptr_editor.context import janus_defaults

with janus_defaults():
    obs = ObservationRequest()  # Uses JANUS-specific defaults
```

## Common Patterns

### Pattern 1: Temporary Configuration Override

```python
from ptr_editor.context import PointingDefaults

# Override defaults for a block
with PointingDefaults(target="Mars"):
    obs1 = ObservationRequest()  # target="Mars"
    obs2 = ObservationRequest()  # target="Mars"

# Reverts to previous defaults after context
obs3 = ObservationRequest()  # target="Jupiter" (default)
```

### Pattern 2: Nested Context Managers

```python
from ptr_editor.context import PointingDefaults, ValidationConfig

with PointingDefaults(target="Europa"):
    with ValidationConfig(ruleset="permissive"):
        # Both contexts active
        obs = ObservationRequest()  # target="Europa"
        validator.validate(obs)     # permissive ruleset
```

### Pattern 3: Factory Functions for attrs Fields

```python
from attrs import define, field
from ptr_editor.context import from_defaults, from_service

@define
class ObservationRequest:
    # Pulls from context defaults
    target: str = field(factory=from_defaults("pointing.target"))
    
    # Pulls from service registry
    validator = field(factory=from_service("validator"))
```

### Pattern 4: Service Registration and Configuration

```python
from ptr_editor.context import get_services, ServiceConfig
from attrs import define

# 1. Register service
get_services().register("my_service", MyService)

# 2. Register configuration schema
@define(frozen=True)
class MyServiceConfig:
    timeout: int = 30

register_service_config("my_service", MyServiceConfig)

# 3. Use with context-specific configuration
with ServiceConfig(my_service=MyServiceConfig(timeout=60)):
    service = get_services()["my_service"]
    config = get_service_config().my_service
    service.do_work(timeout=config.timeout)
```

### Pattern 5: Testing with Service Overrides

```python
from ptr_editor.context import get_services

def test_with_mock_agm():
    # Override for testing
    get_services().set_override("agm_config", MockAGMConfig())
    
    try:
        # Test code here
        result = my_function()
        assert result == expected
    finally:
        # Clean up
        get_services().clear_override("agm_config")
```

## Thread Safety

- **Defaults**: Fully thread-safe using `contextvars`
- **Service Config**: Fully thread-safe using `contextvars`
- **Services**: NOT thread-safe (global singleton registry)

Each thread/async context has its own independent defaults and service config, while services are shared globally.

## Extending the System

### Adding a New Service

```python
from ptr_editor.context import get_services

class MyService:
    def __init__(self):
        self.data = load_data()
    
    def process(self):
        return self.data

# Register at application startup
get_services().register("my_service", MyService)
```

### Adding a New Service Configuration

```python
from attrs import define
from ptr_editor.context import register_service_config, get_service_config

@define(frozen=True)
class MyServiceConfig:
    enabled: bool = True
    max_retries: int = 3

# Register at module import time
register_service_config("my_service", MyServiceConfig)

# Use in service implementation
class MyService:
    def process(self):
        config = get_service_config().my_service
        if not config.enabled:
            return None
        # ... use config.max_retries ...
```

### Adding a New Preset

```python
from ptr_editor.context import DefaultsConfig, PointingDefaults

def ganymede_defaults() -> DefaultsConfig:
    """Configuration for Ganymede observations."""
    return DefaultsConfig(
        pointing=PointingDefaults(
            target="Ganymede",
            boresight="JANUS_boresight",
            designer="JANUS",
        )
    )
```

## API Reference

### Defaults API

```python
get_defaults_config() -> DefaultsConfig
set_defaults_config(config: DefaultsConfig) -> None
from_defaults(attribute_path: str) -> Callable
```

### Services API

```python
get_services() -> ServiceRegistry
from_service(service_name: str, attribute_path: str | None) -> Callable
```

### Service Config API

```python
get_service_config() -> ServiceConfig
set_service_config(config: ServiceConfig) -> None
register_service_config(name: str, config_class: type) -> None
get_registered_service_configs() -> dict[str, type]
from_service_config(service_name: str, attribute_path: str | None) -> Callable
```

## Best Practices

1. **Use defaults for data** - Default attribute values that vary by context
2. **Use services for behavior** - Shared resources and singleton instances
3. **Use service config for runtime behavior** - How services should operate
4. **Prefer context managers** - Temporary overrides with automatic cleanup
5. **Register early** - Register services and configs at startup/import time
6. **Keep configs immutable** - Use frozen attrs classes for all configurations
7. **Use factory functions** - Leverage `from_defaults()` and `from_service()` for attrs fields
8. **Document presets** - Make it easy to discover common configurations
9. **Test with overrides** - Use service overrides for testing with mocks
10. **Keep it simple** - Don't over-engineer context management

## Migration Guide

### From Global Variables

**Before:**
```python
# globals.py
DEFAULT_TARGET = "Jupiter"

# usage.py
from globals import DEFAULT_TARGET
obs = ObservationRequest(target=DEFAULT_TARGET)
```

**After:**
```python
from ptr_editor.context import PointingDefaults, from_defaults

@define
class ObservationRequest:
    target: str = field(factory=from_defaults("pointing.target"))

# Override when needed
with PointingDefaults(target="Mars"):
    obs = ObservationRequest()
```

### From Module-level Singletons

**Before:**
```python
# config.py
_agm_config = None

def get_agm_config():
    global _agm_config
    if _agm_config is None:
        _agm_config = AGMConfiguration()
    return _agm_config
```

**After:**
```python
from ptr_editor.context import get_services

# At startup
get_services().register("agm_config", AGMConfiguration)

# Usage
config = get_services()["agm_config"]
```

## See Also

- [CONTEXT_MODULE_STRUCTURE.md](../../../CONTEXT_MODULE_STRUCTURE.md) - Detailed design documentation
- [examples/](../../../examples/) - Example usage patterns
- Python `contextvars` documentation - Understanding context-local state
