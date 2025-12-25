# Ingress Framework for Cosmograph

A modular, composable framework for transforming and validating cosmograph arguments.

## Overview

The ingress framework provides a clean, functional way to process and transform the keyword arguments passed to `cosmo()` before they reach the Cosmograph widget. Think of it as a data pipeline that:

1. **Validates** inputs to catch errors early
2. **Resolves** data sources (files, URLs, raw data)
3. **Infers** missing parameters using smart heuristics
4. **Transforms** data for better visualization
5. **Logs** transformations for debugging

## Architecture

```
*outer_args, **outer_kwargs
            │
            ▼
┌──────────────────────────┐
│   IngressPipeline        │
│   (compose ingresses)    │
└──────────────────────────┘
            │
            ▼
     transformed_kwargs
            │
            ▼
┌──────────────────────────┐
│   validate_kwargs        │
└──────────────────────────┘
            │
            ▼
┌──────────────────────────┐
│   Cosmograph()           │
└──────────────────────────┘
```

## Quick Start

### Using Pre-built Pipelines

```python
from xcosmo import cosmo, create_smart_defaults_pipeline

# Let the framework infer parameters automatically
pipeline = create_smart_defaults_pipeline()

graph = cosmo(
    points=my_dataframe,
    links=my_links,
    ingress=pipeline,  # That's it!
)
```

### Composing Custom Pipelines

```python
from xcosmo import (
    compose_ingresses,
    guess_point_xy_columns,
    infer_color_by_from_clusters,
    check_points_and_links_format,
)

my_pipeline = compose_ingresses(
    check_points_and_links_format,
    guess_point_xy_columns,
    infer_color_by_from_clusters,
    name="my_custom_pipeline"
)

graph = cosmo(points=df, ingress=my_pipeline)
```

### Creating Custom Ingress Functions

```python
from xcosmo import as_ingress

@as_ingress(register=True, category="custom")
def add_node_degree(kwargs):
    """Calculate node degree from links."""
    points = kwargs.get('points')
    links = kwargs.get('links')
    
    if points is not None and links is not None:
        # ... compute degree ...
        points['degree'] = degree_values
    
    return kwargs

# Use it in a pipeline
pipeline = compose_ingresses(
    create_smart_defaults_pipeline(),
    add_node_degree,
)
```

## Core Components

### 1. IngressPipeline

A composable chain of ingress functions with validation and logging.

```python
from xcosmo import IngressPipeline

pipeline = IngressPipeline(
    [ingress1, ingress2, ingress3],
    name="my_pipeline",
    log_transforms=True,  # Enable logging
)

# Use it
transformed = pipeline(kwargs)

# Compose pipelines
pipeline3 = pipeline1 + pipeline2
```

### 2. @as_ingress Decorator

Convert any function into a proper ingress:

```python
@as_ingress(register=True, category="validation", name="my_validator")
def validate_something(kwargs):
    # validate...
    return kwargs
```

### 3. Registry System

Store and retrieve ingress functions by name:

```python
from xcosmo import INGRESS_REGISTRY, get_ingress, list_ingresses

# List available ingresses
all_ingresses = list_ingresses()
validators = list_ingresses(category="validation")

# Get by name
my_ingress = get_ingress("smart_defaults")
```

## Built-in Ingress Functions

### Validation Category

- `check_points_and_links_format`: Ensure DataFrames are valid
- `verify_by_params_reference_existing_columns`: Check column references
- `ensure_links_have_sources_and_targets`: Validate link structure

### Resolution Category

- `resolve_data_sources`: Load data from files/URLs using `tabled`
- `convert_series_to_dataframe`: Convert Series to DataFrame
- `ensure_dataframes_have_index`: Add index columns if missing

### Parameter Resolution Category

- `guess_point_xy_columns`: Infer x/y columns from names
- `infer_color_by_from_clusters`: Use cluster columns for coloring
- `set_default_label_column`: Choose label from common names
- `infer_size_from_numeric_columns`: Detect size/weight columns

### Transformation Category

- `normalize_numeric_columns`: Scale values to [0, 1]
- `add_point_ids_if_missing`: Generate sequential IDs

### Side-Effect Category

- `track_dataframe_shapes`: Log DataFrame dimensions
- `warn_on_large_datasets`: Performance warnings

## Advanced Usage

### Conditional Ingress

```python
from xcosmo import conditional_ingress

# Only apply if condition is met
large_dataset_handler = conditional_ingress(
    condition=lambda kw: len(kw.get('points', [])) > 10000,
    ingress=downsample_points,
)
```

### Debugging

```python
from xcosmo import debug_ingress, IngressPipeline

# Add debug points in your pipeline
debug_pipeline = IngressPipeline(
    [
        debug_ingress,
        your_ingress,
        debug_ingress,
    ],
    log_transforms=True,  # Detailed logging
)
```

### Using with tabled

The framework integrates seamlessly with `tabled` for data loading:

```python
from xcosmo import cosmo, resolve_data_sources

# Pass file paths or URLs directly
graph = cosmo(
    points="path/to/points.csv",
    links="https://example.com/links.json",
    ingress=[resolve_data_sources],  # Automatically loads data
)
```

## Design Patterns

### Chain of Responsibility

Each ingress function handles one concern, passing kwargs to the next:

```python
kwargs → validate → resolve → infer → transform → kwargs
```

### Functional Composition

Combine simple functions into complex pipelines:

```python
pipeline = f1 ∘ f2 ∘ f3  # Mathematically pure
# Implemented as:
pipeline = compose_ingresses(f1, f2, f3)
```

### Observer Pattern

Side-effect ingresses observe without modifying:

```python
@as_ingress
def log_state(kwargs):
    logger.info(f"Current keys: {list(kwargs.keys())}")
    return kwargs  # Unchanged
```

## Best Practices

1. **Start with Smart Defaults**: Use `create_smart_defaults_pipeline()` as a base
2. **Validate Early**: Put validation ingresses first in the pipeline
3. **Keep It Pure**: Ingress functions should be deterministic and side-effect free (except logging)
4. **Log During Development**: Enable `log_transforms=True` for debugging
5. **Register Reusable Ingresses**: Use `@as_ingress(register=True)` for common transforms
6. **Document Your Ingresses**: Add clear docstrings explaining what each ingress does

## Integration with i2

The framework uses patterns from `i2.signatures` and `i2.wrapper`:

- **Signature validation** ensures ingresses are well-formed
- **kwargs_trans** pattern for functional transformations
- **call_forgivingly** for flexible argument matching

## Examples

See `misc/ingress_framework_tutorial.ipynb` for comprehensive examples covering:

- Basic usage with smart defaults
- Composing custom pipelines
- Creating custom ingress functions
- Debugging with logging
- Using the registry
- Conditional ingress
- Integration with tabled

## Testing

Run tests with:

```bash
pytest tests/test_ingress_framework.py
```

## Contributing

To add new ingress functions:

1. Implement in `xcosmo/ingress_functions.py`
2. Use `@as_ingress(register=True, category="...")`
3. Add to appropriate category
4. Include docstring and examples
5. Add tests

## License

Same as xcosmo/cosmograph.
