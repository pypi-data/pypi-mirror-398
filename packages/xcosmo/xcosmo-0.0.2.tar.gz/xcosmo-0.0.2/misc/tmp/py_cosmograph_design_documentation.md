# py_cosmograph: Design Documentation for Maintainers

**Version**: 0.5.1  
**Last Updated**: 2025-10-22  
**Target Audience**: Package maintainers and developers extending the package

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Package Structure](#package-structure)
4. [Python-JavaScript Communication](#python-javascript-communication)
5. [Data Flow](#data-flow)
6. [Adding New Functionality](#adding-new-functionality)
7. [Validation and Testing](#validation-and-testing)
8. [Key Design Patterns](#key-design-patterns)

---

## 1. Overview

### Purpose

py_cosmograph is a Python package that provides a Python interface to the Cosmograph JavaScript library for interactive network visualization in Jupyter notebooks. It bridges the gap between Python data manipulation (using pandas DataFrames) and JavaScript-based visualization using the anywidget framework.

### Core Technology Stack

- **Frontend**: Cosmograph JavaScript library (from cosmograph-org/cosmograph)
- **Bridge Framework**: anywidget (Python-JavaScript communication in Jupyter)
- **Data Format**: Apache Arrow IPC (Inter-Process Communication) for efficient data transfer
- **Python Widget Framework**: traitlets for reactive state management
- **Data Handling**: pandas DataFrames for points and links

---

## 2. Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Python Layer                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  User Interface Functions:                                   │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ cosmo()      │  │ base_cosmo() │                         │
│  └──────┬───────┘  └──────┬───────┘                         │
│         │                  │                                 │
│         └──────────┬───────┘                                 │
│                    │                                         │
│         ┌──────────▼──────────┐                             │
│         │   Data Processing   │                             │
│         │   (base.py)         │                             │
│         └──────────┬──────────┘                             │
│                    │                                         │
│         ┌──────────▼──────────┐                             │
│         │  Cosmograph Widget  │                             │
│         │  (widget/__init__)  │                             │
│         └──────────┬──────────┘                             │
│                    │                                         │
└────────────────────┼─────────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │   anywidget Bridge      │
        │   - Traitlets sync      │
        │   - Arrow IPC streams   │
        │   - Custom messages     │
        └────────────┬────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│                  JavaScript Layer                             │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Widget JavaScript Module:                                   │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │   model()    │  │   render()   │                         │
│  └──────┬───────┘  └──────┬───────┘                         │
│         │                  │                                 │
│         │  ┌───────────────▼──────────────┐                 │
│         │  │  Arrow Table Deserialization │                 │
│         │  └───────────────┬──────────────┘                 │
│         │                  │                                 │
│         └──────────┬───────┘                                 │
│                    │                                         │
│         ┌──────────▼──────────┐                             │
│         │  Cosmograph Library │                             │
│         │  (graph rendering)  │                             │
│         └─────────────────────┘                             │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### Python Components

1. **base.py**: Entry point functions with signature definitions and documentation
2. **widget/__init__.py**: Core widget class with traitlets definitions
3. **util.py**: Utility functions for data transformation, type handling, signature generation
4. **validation.py**: Input validation for data and configuration
5. **config.py**: Global configuration management (API keys)
6. **widget/utils.py**: Arrow IPC serialization utilities

#### JavaScript Components

1. **widget.js** (compiled from TypeScript): anywidget interface with `model()` and `render()` functions
2. **Cosmograph library integration**: Actual graph rendering and interaction

---

## 3. Package Structure

### File Organization

```
cosmograph/
├── __init__.py              # Package exports (cosmo, Cosmograph, etc.)
├── __about__.py             # Version metadata
├── base.py                  # High-level interface functions
├── config.py                # Global configuration (API keys)
├── util.py                  # Utilities (type conversion, signatures)
├── validation.py            # Input validation
├── widget/
│   ├── __init__.py          # Cosmograph widget class (core)
│   ├── utils.py             # Arrow IPC conversion
│   ├── static/
│   │   ├── widget.js        # Compiled JS (from TypeScript)
│   │   ├── widget.css       # Styling
│   │   └── meta.json        # Build metadata
│   └── export_project/      # Cloud export functionality
│       ├── __init__.py
│       ├── config.py
│       ├── create_project.py
│       ├── prepare_parquet.py
│       └── upload_file.py
├── data/
│   └── params_ssot.json     # Single Source of Truth for parameters
└── tests/
    ├── __init__.py
    ├── base_test.py
    └── datagen.py
```

### Key Design Decision: Single Source of Truth (SSOT)

The `params_ssot.json` file contains the canonical definition of all Cosmograph parameters including:
- Parameter names
- Type annotations
- Default values
- Descriptions
- Whether they map to camelCase for JS

This enables:
- Automatic signature generation
- Automatic docstring generation
- Type validation
- Consistent naming between Python and JavaScript

---

## 4. Python-JavaScript Communication

### Communication Mechanisms

py_cosmograph uses **three distinct mechanisms** for Python-JavaScript communication:

#### 4.1 Traitlets Synchronization (Bidirectional)

**Purpose**: Synchronize configuration parameters and state

**How it works**:
- Python traitlets with `.tag(sync=True)` automatically sync with JavaScript
- Changes on either side propagate to the other
- Uses anywidget's built-in synchronization

**Python Side Example**:
```python
class Cosmograph(anywidget.AnyWidget):
    point_size = Float(None, allow_none=True).tag(sync=True)
    show_labels = Bool(None, allow_none=True).tag(sync=True)
    clicked_point_index = Int(None, allow_none=True).tag(sync=True)
```

**JavaScript Side Access**:
```javascript
function render({ model, el }) {
    // Read synced value
    const pointSize = model.get('point_size');
    
    // Listen for changes
    model.on('change:point_size', () => {
        const newSize = model.get('point_size');
        // Update visualization
    });
    
    // Set value (syncs back to Python)
    model.set('clicked_point_index', 5);
    model.save_changes();
}
```

**Synchronized Parameters**:
- Configuration: All `point_*`, `link_*`, `simulation_*`, display settings
- State: `clicked_point_index`, `clicked_point_id`, `selected_point_indices`, etc.
- Data references: `_ipc_points`, `_ipc_links` (as bytes)

#### 4.2 Apache Arrow IPC Streams (Python → JavaScript)

**Purpose**: Efficient transfer of large tabular data (points and links DataFrames)

**How it works**:
1. Python converts pandas DataFrame to Apache Arrow Table
2. Serializes to Arrow IPC stream format (bytes)
3. Bytes transferred via traitlets (`_ipc_points`, `_ipc_links`)
4. JavaScript deserializes Arrow stream back to columnar data

**Python Side** (`widget/utils.py`):
```python
def get_buffered_arrow_table(df):
    """Convert pandas DataFrame to buffered Arrow IPC stream"""
    if df is None:
        return None
    
    # Convert int64 to int32 for efficiency
    df_int32 = df.select_dtypes(include=["int64"]).astype("int32")
    df[df_int32.columns] = df_int32
    
    # Create Arrow table
    table = pa.Table.from_pandas(df)
    
    # Serialize to IPC stream
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, table.schema) as writer:
        writer.write(table)
    
    return sink.getvalue().to_pybytes()
```

**Python Side** (`widget/__init__.py`):
```python
@observe("points")
def changePoints(self, change):
    points = change.new
    self._ipc_points = get_buffered_arrow_table(points)

@observe("links") 
def changeLinks(self, change):
    links = change.new
    self._ipc_links = get_buffered_arrow_table(links)
```

**JavaScript Side**:
```javascript
// Deserialize Arrow IPC stream
import * as arrow from 'apache-arrow';

function deserializeArrowTable(ipcBytes) {
    const table = arrow.tableFromIPC(ipcBytes);
    // Convert to format Cosmograph expects
    return processArrowTable(table);
}

// Listen for data updates
model.on('change:_ipc_points', () => {
    const pointsBytes = model.get('_ipc_points');
    const pointsData = deserializeArrowTable(pointsBytes);
    cosmograph.setData(pointsData, linksData);
});
```

**Why Arrow IPC**:
- **Efficient**: Zero-copy deserialization possible
- **Fast**: Binary columnar format optimized for analytical data
- **Type-safe**: Preserves data types across language boundary
- **Compact**: More efficient than JSON for large datasets

#### 4.3 Custom Messages (Python → JavaScript)

**Purpose**: Invoke specific methods/actions on the JavaScript side

**How it works**:
- Python calls `self.send(message_dict)`
- JavaScript receives message in model's custom message handler
- Message contains `type` field and any additional parameters

**Python Side** (`widget/__init__.py`):
```python
def select_point_by_index(self, index):
    self.send({"type": "select_point_by_index", "index": index})

def fit_view(self):
    self.send({"type": "fit_view"})

def activate_rect_selection(self):
    self.send({"type": "activate_rect_selection"})
```

**JavaScript Side**:
```javascript
function render({ model, el }) {
    model.on('msg:custom', (msg) => {
        switch(msg.type) {
            case 'select_point_by_index':
                cosmograph.selectNode(msg.index);
                break;
            case 'fit_view':
                cosmograph.fitView();
                break;
            case 'activate_rect_selection':
                cosmograph.activateRectangleSelection();
                break;
        }
    });
}
```

**Message Types** (from Python public methods):
- Selection: `select_point_by_index`, `select_point_by_id`, `select_points_by_indices`
- View control: `fit_view`, `fit_view_by_indices`, `fit_view_by_coordinates`
- Simulation: `start`, `pause`, `restart`, `step`
- Interaction modes: `activate_rect_selection`, `activate_polygonal_selection`
- Capture: `capture_screenshot`

### Communication Flow Summary

```
Configuration Changes:
  Python traitlet ←→ anywidget sync ←→ JavaScript model ←→ Cosmograph

Large Data Updates:
  pandas DataFrame → Arrow IPC bytes → traitlet → JS deserialize → Cosmograph

Method Calls:
  Python method → send(message) → JS msg handler → Cosmograph method

State Updates (JS → Python):
  User click → Cosmograph event → model.set() → traitlet → Python observer
```

---

## 5. Data Flow

### Complete Data Flow Diagram

```
┌────────────────────────────────────────────────────────────┐
│                      User Code                              │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│  cosmo(points=df, links=df_links, point_color_by='type')  │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│             Data Processing (base.py)                       │
│  1. Handle 'data' argument priority                        │
│  2. Remove None values                                      │
│  3. Validate inputs (types, column existence)              │
│  4. Apply name transformations (snake_case → camelCase)    │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│           Cosmograph Widget Creation                        │
│  Cosmograph(points=df, links=df_links,                    │
│             pointColorBy='type')                           │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│         Widget Initialization (__init__)                    │
│  - Set traitlets from kwargs                               │
│  - Trigger @observe decorators                             │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│      Data Serialization (widget/utils.py)                  │
│  changePoints() / changeLinks() observers:                 │
│  1. Convert DataFrame to Arrow Table                       │
│  2. Serialize to IPC stream bytes                          │
│  3. Set _ipc_points / _ipc_links traitlets                │
│  4. Cache with joblib.Memory                               │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│          anywidget Framework                                │
│  - Sends traitlets to JavaScript via Jupyter Comm         │
│  - Transfers bytes efficiently                             │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│        JavaScript Widget (widget.js)                        │
│  render({ model, el }):                                    │
│  1. Deserialize Arrow IPC → columnar data                 │
│  2. Transform to Cosmograph format                         │
│  3. Create Cosmograph instance                             │
│  4. Apply configuration from model                         │
│  5. Render graph in el (container element)                │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│           Cosmograph Library                                │
│  - WebGL rendering                                          │
│  - Force simulation                                         │
│  - User interactions                                        │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼ (on user interaction)
┌────────────────────────────────────────────────────────────┐
│      State Updates (JavaScript → Python)                    │
│  - User clicks point → model.set('clicked_point_index')   │
│  - User selects → model.set('selected_point_indices')     │
│  - Changes sync back to Python traitlets                   │
└─────────────────────────────────────────────────────────────┘
```

### Data Transformation Pipeline

#### 1. Input Data Formats

py_cosmograph accepts flexible input formats:

```python
# Accepted formats for points/links:
- pandas DataFrame
- dict of lists/arrays
- list of dicts
- None (for links only)
```

#### 2. Parameter Name Transformation

**Snake Case → Camel Case**: Python uses snake_case, JavaScript uses camelCase

```python
# util.py
def snake_to_camel_case(name, first_char_trans=str.lower):
    """Convert snake_case to camelCase"""
    components = name.split('_')
    return first_char_trans(components[0]) + ''.join(
        x.title() for x in components[1:]
    )

# Example:
point_color_by  → pointColorBy
link_width_scale → linkWidthScale
```

This transformation is critical because:
- Python convention is snake_case
- JavaScript convention is camelCase
- Cosmograph JS library expects camelCase
- Automatic transformation maintains user experience

#### 3. Type Validation

Key validation steps (in `validation.py`):

```python
def validate_kwargs(kwargs):
    """Validate cosmograph arguments"""
    # Check for valid color names/formats
    # Verify column references exist in DataFrames
    # Validate numeric ranges
    # Check enum values (e.g., point_color_strategy)
    return kwargs
```

---

## 6. Adding New Functionality

This section provides a **step-by-step process** for maintainers to add new features from the Cosmograph JavaScript library to the Python wrapper.

### Process Overview

```
1. Check JS Cosmograph documentation/changelog
2. Update params_ssot.json (SSOT)
3. Add Python traitlet to Cosmograph class
4. Update JavaScript widget code (if needed)
5. Test synchronization
6. Document new parameter
7. Add usage example
```

### Step-by-Step Guide

#### Step 1: Identify New JS Functionality

**Source**: Check the Cosmograph JavaScript library repository:
- Repository: `https://github.com/cosmograph-org/cosmograph`
- Check releases, changelog, or commit history
- Look at TypeScript interface definitions

**Example**: Suppose JS Cosmograph adds a new `linkOpacity` configuration parameter.

#### Step 2: Update Single Source of Truth (params_ssot.json)

Location: `cosmograph/data/params_ssot.json`

```json
{
  "name": "link_opacity",
  "annotation": "float",
  "default": null,
  "description": "Opacity of links (0.0 to 1.0)"
}
```

**Important**: This JSON drives:
- Automatic signature generation in `base.py`
- Type annotations
- Docstring generation
- Parameter validation

**Fields**:
- `name`: Python parameter name (snake_case)
- `annotation`: Python type as string (e.g., "float", "int", "list[str]", "Union[str, list[float]]")
- `default`: Default value (use `null` for None)
- `description`: User-facing documentation

#### Step 3: Add Traitlet to Cosmograph Class

Location: `cosmograph/widget/__init__.py`

```python
class Cosmograph(anywidget.AnyWidget):
    # ... existing traits ...
    
    link_opacity = Float(None, allow_none=True).tag(sync=True)
```

**Traitlet Type Mapping**:
- Python `float` → `Float()`
- Python `int` → `Int()`
- Python `str` → `Unicode()`
- Python `bool` → `Bool()`
- Python `list[float]` → `List(Float, ...)`
- Python `Union[str, list[float]]` → `Union([Unicode(), List(Float())])`
- Python `Dict[str, Any]` → `Dict()`

**Key Points**:
- Always use `allow_none=True` for optional parameters
- Always add `.tag(sync=True)` to sync with JavaScript
- Name must match the snake_case name in params_ssot.json

#### Step 4: Update JavaScript Widget Code

**If parameter is directly passed to Cosmograph**: No changes needed! The anywidget sync mechanism automatically passes it.

**If parameter requires transformation**:

Location: `js/widget.tsx` or similar (TypeScript source)

```typescript
function render({ model, el }: RenderContext) {
    // Read parameter from model
    const linkOpacity = model.get('link_opacity');
    
    // Apply to Cosmograph
    cosmograph.setConfig({
        linkOpacity: linkOpacity  // camelCase for JS
    });
    
    // Listen for changes
    model.on('change:link_opacity', () => {
        const newOpacity = model.get('link_opacity');
        cosmograph.setConfig({ linkOpacity: newOpacity });
    });
}
```

**After modifying TypeScript**:
```bash
# Rebuild the JavaScript bundle
npm run build

# This compiles TypeScript → JavaScript and updates:
# - cosmograph/widget/static/widget-<hash>.js
# - cosmograph/widget/static/meta.json
```

#### Step 5: Test Synchronization

Create a test in `tests/base_test.py`:

```python
def test_link_opacity_sync():
    """Test that link_opacity syncs properly"""
    from cosmograph import cosmo
    import pandas as pd
    
    df = pd.DataFrame({
        'id': ['a', 'b'],
        'x': [0, 1],
        'y': [0, 1]
    })
    
    # Test parameter acceptance
    graph = cosmo(
        df,
        links=pd.DataFrame({
            'source': ['a'],
            'target': ['b']
        }),
        link_opacity=0.5
    )
    
    # Verify traitlet was set
    assert graph.link_opacity == 0.5
    
    # Test dynamic update
    graph.link_opacity = 0.8
    assert graph.link_opacity == 0.8
```

**Manual testing in Jupyter**:
```python
from cosmograph import cosmo
import pandas as pd

# Create test data
df = pd.DataFrame({'id': ['a', 'b', 'c'], 'x': [0, 1, 2], 'y': [0, 1, 0]})
links = pd.DataFrame({'source': ['a', 'b'], 'target': ['b', 'c']})

# Test new parameter
g = cosmo(df, links=links, link_opacity=0.5)
display(g)

# Test dynamic update
g.link_opacity = 0.3  # Should see change in visualization
```

#### Step 6: Update Documentation

Add to function docstring via params_ssot.json (already done in Step 2).

Update any package-level documentation:
- README examples
- Tutorial notebooks
- API reference

#### Step 7: Update CHANGELOG

Location: `misc/CHANGELOG.md`

```markdown
## 2025-10-22: Add link opacity support

- Added `link_opacity` parameter to control transparency of links
- Syncs with Cosmograph's linkOpacity configuration
- Supports values from 0.0 (transparent) to 1.0 (opaque)
```

### Special Cases

#### Adding a Method (not just a parameter)

Example: Adding `export_to_png()` method

**Python Side** (`widget/__init__.py`):
```python
def export_to_png(self):
    """Export current visualization as PNG"""
    self.send({"type": "export_to_png"})
```

**JavaScript Side**:
```typescript
model.on('msg:custom', (msg) => {
    if (msg.type === 'export_to_png') {
        const imageData = cosmograph.getCanvas().toDataURL('image/png');
        // Could send back to Python via model.set() if needed
        // or trigger browser download
    }
});
```

#### Adding a Callback/Event Handler

Example: Exposing `onPointHover` event

**Python Side**:
```python
class Cosmograph(anywidget.AnyWidget):
    hovered_point_index = Int(None, allow_none=True).tag(sync=True)
```

**JavaScript Side**:
```typescript
cosmograph.onPointHover((pointIndex) => {
    model.set('hovered_point_index', pointIndex);
    model.save_changes();  // Sync to Python
});
```

**Python Usage**:
```python
graph = cosmo(data)

def on_hover_change(change):
    print(f"Hovering over point {change.new}")

graph.observe(on_hover_change, names='hovered_point_index')
```

---

## 7. Validation and Testing

### What Must Be Validated

When adding or modifying functionality, verify:

#### 7.1 Type Consistency

**Check**: Python type annotations match JavaScript expectations

```python
# Python declares:
point_size: float = None

# JavaScript receives:
const pointSize = model.get('point_size');  // Should be number or null
```

**Validation checklist**:
- [ ] Python traitlet type matches params_ssot.json annotation
- [ ] JavaScript receives expected type
- [ ] Null/None handling is correct
- [ ] Union types are handled properly

#### 7.2 Name Transformation

**Check**: snake_case → camelCase conversion works

```python
# Python:
point_color_by='category'

# Should become in JS:
pointColorBy = 'category'
```

**Validation**:
- Check `argument_aliases` in `base.py` includes the mapping
- Verify JavaScript reads the camelCase version from model

#### 7.3 Data Column References

**Check**: Parameters referencing DataFrame columns are validated

```python
# If points DataFrame doesn't have 'category' column:
cosmo(points, point_color_by='category')  # Should raise ValidationError
```

**Validation happens in**:
- `validation.py`: `validate_kwargs()`
- Must check column existence before passing to widget

#### 7.4 Value Ranges

**Check**: Numeric parameters are within valid ranges

```python
# Invalid values should be caught:
cosmo(data, point_size=-1)  # Negative size invalid
cosmo(data, link_opacity=1.5)  # > 1.0 invalid
```

#### 7.5 Sync Mechanism

**Check**: Bidirectional sync works correctly

**Test Python → JavaScript**:
```python
g = cosmo(data, point_size=5)
# Verify in JS: model.get('point_size') === 5
```

**Test JavaScript → Python**:
```python
g = cosmo(data)
# Simulate JS click that sets clicked_point_index
# Verify: g.clicked_point_index reflects the change
```

### Testing Strategy

#### Unit Tests

Location: `tests/base_test.py`

```python
def test_new_parameter():
    """Test new parameter end-to-end"""
    # 1. Test parameter acceptance
    # 2. Test type validation
    # 3. Test default value
    # 4. Test None handling
```

#### Integration Tests

**Manual testing in Jupyter notebook**:

1. Create visualization with new parameter
2. Verify visual effect
3. Test dynamic updates
4. Test with various data types/sizes
5. Check error messages for invalid inputs

#### Visual Regression Tests (if applicable)

For changes affecting rendering:
- Capture screenshots before/after
- Compare with reference images
- Check for unintended visual changes

---

## 8. Key Design Patterns

### 8.1 Single Source of Truth (SSOT)

**Location**: `cosmograph/data/params_ssot.json`

**Purpose**: Centralize parameter definitions to avoid drift

**Benefits**:
- Auto-generate signatures
- Auto-generate documentation
- Consistent validation
- Easy to add new parameters

**Usage in code**:
```python
from cosmograph.util import cosmograph_base_signature, cosmograph_base_docs

# Generate signature from SSOT
sig = cosmograph_base_signature()

# Generate docstring from SSOT
docs = cosmograph_base_docs()
```

### 8.2 Facade Pattern

**Where**: `base.py` provides simple functions wrapping the widget

```python
def cosmo(**kwargs) -> Cosmograph:
    """Simple facade over Cosmograph widget"""
    # Process inputs
    # Validate
    # Return widget instance
```

**Benefits**:
- User-friendly interface
- Hide complexity of widget initialization
- Allow for data preprocessing

### 8.3 Observer Pattern

**Where**: Widget uses traitlets' `@observe` decorator

```python
@observe("points")
def changePoints(self, change):
    """React to points DataFrame changes"""
    points = change.new
    self._ipc_points = get_buffered_arrow_table(points)
```

**Benefits**:
- Automatic data serialization when data changes
- Decoupled components
- Reactive updates

### 8.4 Dependency Injection

**Where**: Configuration management

```python
# Global API key injected into all widgets
from cosmograph import set_api_key, cosmo

set_api_key("my-key")

# All subsequent widgets use this key
g1 = cosmo(data1)  # Uses global API key
g2 = cosmo(data2)  # Also uses global API key
```

**Implementation**:
```python
# config.py
_GLOBAL_API_KEY = None
_COSMOGRAPH_INSTANCES = set()

def set_api_key(api_key):
    global _GLOBAL_API_KEY
    _GLOBAL_API_KEY = api_key
    # Update all existing instances
    for instance in _COSMOGRAPH_INSTANCES:
        instance.api_key = api_key
```

### 8.5 Caching Strategy

**Where**: `widget/utils.py`

```python
from joblib import Memory

memory = Memory(CACHE_DIR, verbose=0)

@memory.cache
def get_buffered_arrow_table(df):
    """Cache Arrow serialization"""
    # ... expensive serialization ...
```

**Purpose**:
- Avoid re-serializing unchanged DataFrames
- Improve performance for large datasets
- Transparent to users

### 8.6 Type Codec Pattern

**Where**: `util.py`

```python
def annotation_to_str(annotation):
    """Encode Python type annotations as strings"""
    # For JSON serialization in params_ssot.json

def str_to_annotation(string):
    """Decode string back to Python type annotation"""
    # For signature generation from params_ssot.json
```

**Purpose**:
- Store type information in JSON (params_ssot.json)
- Reconstruct actual Python types at runtime
- Enable dynamic signature generation

---

## 9. Troubleshooting Common Issues

### Issue: New Parameter Not Appearing in JavaScript

**Symptoms**: Set parameter in Python, but JavaScript doesn't receive it

**Debug steps**:
1. Check if traitlet has `.tag(sync=True)`
2. Verify parameter name matches exactly (case-sensitive)
3. Check browser console for sync errors
4. Test with simple value: `g.new_param = "test"`

### Issue: Data Not Updating in Visualization

**Symptoms**: Update DataFrame in Python, but graph doesn't change

**Debug steps**:
1. Verify `@observe` decorator is on correct method
2. Check if Arrow serialization succeeds (look for warnings)
3. Verify JavaScript deserializes Arrow data correctly
4. Check if Cosmograph's `setData()` is called

### Issue: Type Mismatch Errors

**Symptoms**: TraitError about unexpected type

**Debug steps**:
1. Check traitlet definition matches expected type
2. Verify params_ssot.json annotation is correct
3. Ensure Python value can be serialized to JSON
4. Check for None vs. empty string confusion

### Issue: Changes Not Syncing Back to Python

**Symptoms**: User interaction in JS doesn't update Python attributes

**Debug steps**:
1. Verify JavaScript calls `model.set('attr_name', value)`
2. Verify JavaScript calls `model.save_changes()` after set
3. Check if Python traitlet has `allow_none=True` if value can be None
4. Look for errors in Jupyter notebook console

---

## 10. Best Practices for Maintainers

### DO:

✅ **Always update params_ssot.json first** when adding parameters  
✅ **Add docstrings to all new functions/classes**  
✅ **Write tests for new functionality**  
✅ **Use snake_case in Python, let auto-conversion handle camelCase**  
✅ **Validate inputs before passing to widget**  
✅ **Document breaking changes prominently**  
✅ **Keep Arrow IPC format for data transfer** (efficient)  
✅ **Cache expensive operations** (e.g., serialization)  
✅ **Register new widget instances** for global config updates  

### DON'T:

❌ **Don't bypass SSOT** - always update params_ssot.json  
❌ **Don't forget .tag(sync=True)** on traitlets  
❌ **Don't use hardcoded values** - make them configurable  
❌ **Don't skip validation** - prevent errors early  
❌ **Don't break backward compatibility** without major version bump  
❌ **Don't ignore type annotations** - they enable better tooling  
❌ **Don't use JSON for large data** - Arrow IPC is far more efficient  

---

## 11. Key Files Reference

### Must-Read Files for Maintainers

| File | Purpose | When to Modify |
|------|---------|----------------|
| `data/params_ssot.json` | Parameter definitions (SSOT) | Adding any new parameter |
| `widget/__init__.py` | Cosmograph widget class | Adding traitlets, methods, observers |
| `base.py` | User-facing functions | Changing API, adding wrapper functions |
| `util.py` | Utilities, signature generation | Changing parameter handling |
| `validation.py` | Input validation | Adding validation rules |
| `widget/utils.py` | Arrow serialization | Changing data transfer format |
| `js/widget.tsx` (source) | JavaScript widget code | Adding JS functionality, event handlers |

### Build Files

| File | Purpose |
|------|---------|
| `widget/static/widget-<hash>.js` | Compiled JavaScript (DO NOT edit directly) |
| `widget/static/meta.json` | Build metadata (maps to JS/CSS files) |
| `widget/static/widget.css` | Styling |

---

## 12. Version Alignment

### Keeping JS and Python Aligned

**Challenge**: Cosmograph JS library evolves independently

**Strategy**:

1. **Monitor Cosmograph JS releases**
   - Watch GitHub repository
   - Check for new parameters/methods in releases

2. **Version tracking**
   - Document which JS Cosmograph version py_cosmograph wraps
   - Add to `__about__.py` or README

3. **Parameter auditing**
   ```bash
   # Periodically check:
   # - All params in params_ssot.json exist in JS
   # - No new JS params are missing in Python
   ```

4. **Update cycle**
   ```
   JS Cosmograph release
     ↓
   Review changelog
     ↓
   Add new parameters to params_ssot.json
     ↓
   Add traitlets
     ↓
   Update JS widget code if needed
     ↓
   Test
     ↓
   Release new py_cosmograph version
   ```

5. **Testing alignment**
   - Create comprehensive test that exercises all parameters
   - Verify no JS console errors about unknown parameters
   - Check JS doesn't expose parameters Python doesn't wrap

---

## Summary

This document provides the essential information for maintaining and extending py_cosmograph. The key takeaways:

1. **Communication**: Three mechanisms (traitlets sync, Arrow IPC, custom messages)
2. **Data Flow**: DataFrame → Arrow → bytes → JS → Cosmograph
3. **Adding Features**: Always start with params_ssot.json
4. **Validation**: Check types, names, column references, ranges
5. **Testing**: Unit tests + manual Jupyter testing
6. **Alignment**: Monitor JS Cosmograph releases and sync changes

By following this documentation, maintainers can confidently extend the package while maintaining consistency and quality.
