# attrs_xml

**A standalone library for XML-serializable attrs classes with intelligent type conversion**

## Overview

`attrs_xml` extends [attrs](https://www.attrs.org/) to create Python classes that can:
- ✅ Serialize to/from XML
- ✅ Automatically convert values to correct types
- ✅ Validate types at runtime
- ✅ Manage parent-child relationships in hierarchical structures

## Quick Start

```python
from attrs_xml import element_define, element, BaseElement
from attrs_xml.xml import dumps, loads

@element_define
class Person(BaseElement):
    name: str = element()
    age: int = element()
    email: str = element(default="")

# Create and serialize
person = Person(name="Alice", age=30)
xml_str = dumps(person)
print(xml_str)
# <person>
#   <name>Alice</name>
#   <age>30</age>
#   <email></email>
# </person>

# Deserialize
person2 = loads(xml_str, Person)
assert person2.name == "Alice"
```

## Architecture

```
attrs_xml/
├── core/              # Attrs extension framework
│   ├── decorators.py          # @element_define decorator
│   ├── fields.py              # Field helpers (element, attr, text)
│   ├── base_element.py        # BaseElement base class
│   ├── converter_factory.py  # Automatic type conversion
│   ├── validator_factory.py  # Type validation
│   └── ...
│
├── xml/               # XML serialization
│   ├── io.py                  # load(), dump(), loads(), dumps()
│   ├── converter.py           # cattrs integration
│   └── ...
│
├── resolution/        # Pluggable value resolution
│   ├── strategies.py          # Resolution strategies
│   ├── registry.py            # Strategy registry
│   └── ...
│
└── ...
```

## Features

### Automatic Type Conversion

Values are automatically converted to the correct type using a pluggable resolution system:

```python
@element_define
class Config(BaseElement):
    port: int = element()        # Strings converted to int
    enabled: bool = element()    # "true"/"false" to bool
    timeout: float = element()   # Numeric strings to float

# Works with string inputs from XML
config = Config(port="8080", enabled="true", timeout="30.5")
assert config.port == 8080
assert config.enabled is True
assert config.timeout == 30.5
```

### Type Validation

Runtime type checking with helpful error messages:

```python
@element_define
class Data(BaseElement):
    value: int = element()

try:
    Data(value="not a number")  # Will fail validation
except TypeError as e:
    print(f"Validation error: {e}")
```

### Parent-Child Relationships

Hierarchical structures maintain parent references:

```python
@element_define
class Parent(BaseElement):
    child: Child = element()

@element_define  
class Child(BaseElement):
    name: str = element()

parent = Parent(child=Child(name="test"))
assert parent.child._parent is parent  # Automatic parent reference
```

## Integration with ptr_editor

When used with [ptr_editor](https://github.com/luca-penasa/ptr-editor), `attrs_xml` gains additional features:

- **Template Resolution**: Reference shared templates with `#template_name`
- **AGM Configuration**: Automatic case normalization for AGM fields
- **PTR-specific Validation**: Domain-specific validation rules

```python
# With ptr_editor
from ptr_editor import PtrElement
from attrs_xml import element

@element_define
class MyPtrElement(PtrElement):
    value: str = element()
    template_ref: MyOtherElement = element()  # Can use "#template_name"
```

The integration is **optional** - `attrs_xml` works perfectly standalone.

## Resolution System

The resolution system uses pluggable strategies to convert values:

```python
from attrs_xml.resolution import get_default_registry

registry = get_default_registry()

# Built-in strategies (in priority order):
# 1. Passthrough (10) - values already correct type
# 2. Callable (20) - invoke factory functions
# 3. Method (40) - call from_any/from_string methods
```

### Custom Strategies

You can register custom resolution strategies:

```python
from attrs_xml.resolution.strategies import ResolutionStrategy, ResolutionResult

class MyCustomStrategy(ResolutionStrategy):
    def __init__(self):
        super().__init__(priority=35)
    
    @property
    def name(self) -> str:
        return "my_custom"
    
    def can_resolve(self, context) -> bool:
        # Check if this strategy applies
        return isinstance(context.value, str) and context.value.startswith("$")
    
    def resolve(self, context):
        # Perform custom resolution
        special_value = lookup_special_value(context.value[1:])
        return ResolutionResult.succeeded(special_value, strategy_name=self.name)

# Register it
from attrs_xml.resolution import get_default_registry
registry = get_default_registry()
registry.register(MyCustomStrategy())
```

## Dependencies

### Required
- `attrs` - Class definition
- `cattrs` - Serialization framework
- `xmltodict` - XML parsing
- `loguru` - Logging

### Optional
- `ptr_editor` - For PTR-specific features (templates, AGM, etc.)

## Status

**attrs_xml is 100% standalone** - it has zero code dependencies on ptr_editor.

The only remaining reference is in the version metadata, which falls back gracefully:
```python
# Gets version from ptr_editor if installed, otherwise uses "0.0.0-dev"
__version__ = metadata.version("ptr_editor") if available else "0.0.0-dev"
```

This allows attrs_xml to be:
- ✅ Used completely standalone
- ✅ Extracted into a separate package if needed
- ✅ Extended by ptr_editor without coupling

## License

See LICENSE file in repository root.
