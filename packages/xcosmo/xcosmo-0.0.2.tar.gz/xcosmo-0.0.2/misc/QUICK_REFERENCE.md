# Ingress Framework Quick Reference

## One-Line Use Cases

```python
from xcosmo import cosmo, create_smart_defaults_pipeline

# Just add ingress=create_smart_defaults_pipeline() 
graph = cosmo(points=df, ingress=create_smart_defaults_pipeline())
```

## Common Patterns

### Pattern 1: Use Smart Defaults
```python
pipeline = create_smart_defaults_pipeline()
graph = cosmo(points=df, links=links_df, ingress=pipeline)
```

### Pattern 2: Add Custom Logic
```python
from xcosmo import compose_ingresses, create_smart_defaults_pipeline, as_ingress

@as_ingress
def my_transform(kwargs):
    # Your logic here
    return kwargs

pipeline = compose_ingresses(
    create_smart_defaults_pipeline(),
    my_transform,
)
```

### Pattern 3: Selective Ingresses
```python
from xcosmo import guess_point_xy_columns, infer_color_by_from_clusters

pipeline = compose_ingresses(
    guess_point_xy_columns,
    infer_color_by_from_clusters,
)
```

### Pattern 4: Registry Lookup
```python
from xcosmo import get_ingress

validator = get_ingress('check_points_and_links_format')
graph = cosmo(points=df, ingress=[validator])
```

## Available Ingresses by Category

### Validation
- `check_points_and_links_format`
- `verify_by_params_reference_existing_columns`
- `ensure_links_have_sources_and_targets`

### Resolution
- `resolve_data_sources` - Load from files/URLs
- `convert_series_to_dataframe`
- `ensure_dataframes_have_index`

### Smart Defaults
- `guess_point_xy_columns`
- `infer_color_by_from_clusters`
- `set_default_label_column`
- `infer_size_from_numeric_columns`

### Transformation
- `normalize_numeric_columns`
- `add_point_ids_if_missing`

### Debug/Logging
- `track_dataframe_shapes`
- `warn_on_large_datasets`
- `debug_ingress` - Print state
- `log_ingress_call(name)` - Log with custom name

## Creating Custom Ingresses

### Simple (kwargs → kwargs)
```python
from xcosmo import as_ingress

@as_ingress
def my_ingress(kwargs):
    # Modify kwargs
    return kwargs
```

### With Registration
```python
@as_ingress(register=True, category="custom", name="my_name")
def my_ingress(kwargs):
    return kwargs
```

### Conditional
```python
from xcosmo import conditional_ingress

conditional = conditional_ingress(
    condition=lambda kw: len(kw.get('points', [])) > 100,
    ingress=my_large_data_handler,
)
```

## Debugging

### Enable Logging
```python
pipeline = IngressPipeline(
    [ingress1, ingress2],
    log_transforms=True,  # Detailed logs
)
```

### Add Debug Points
```python
from xcosmo import debug_ingress

pipeline = compose_ingresses(
    debug_ingress,      # Print state
    your_ingress,
    debug_ingress,      # Print state again
)
```

## Pipeline Operations

### Composition
```python
# Method 1: compose_ingresses
pipeline = compose_ingresses(f1, f2, f3)

# Method 2: IngressPipeline
pipeline = IngressPipeline([f1, f2, f3])

# Method 3: Addition
pipeline = pipeline1 + pipeline2
```

### Inspection
```python
print(pipeline.ingress_names)  # List names
print(len(pipeline.ingresses))  # Count
```

## What Gets Auto-Inferred?

With `create_smart_defaults_pipeline()`:

| Parameter | Inferred From |
|-----------|---------------|
| `point_x_by` | Columns: x, x_pos, longitude, lon |
| `point_y_by` | Columns: y, y_pos, latitude, lat |
| `point_label_by` | Columns: title, name, label, id |
| `point_color_by` | Columns starting with `cluster` |
| `point_size_by` | Columns with `size` or `weight` |
| `link_source_by` | Column: source |
| `link_target_by` | Column: target |

## Integration Examples

### With tabled
```python
from xcosmo import resolve_data_sources

graph = cosmo(
    points="path/to/data.csv",  # File path
    links="https://example.com/links.json",  # URL
    ingress=[resolve_data_sources],  # Auto-loads
)
```

### With Existing Workflow
```python
# Your existing code
df = load_my_data()
df = preprocess(df)

# Add ingress at the end
graph = cosmo(
    points=df,
    ingress=create_smart_defaults_pipeline(),
)
```

## Best Practices

1. **Start with smart defaults**: `create_smart_defaults_pipeline()`
2. **Add custom logic after**: `smart_defaults + my_ingress`
3. **Validate early**: Put validation ingresses first
4. **Log during dev**: `log_transforms=True`
5. **Register reusable ingresses**: `@as_ingress(register=True)`

## Common Gotchas

❌ **Don't modify kwargs in-place without returning it**
```python
def bad_ingress(kwargs):
    kwargs['foo'] = 'bar'
    # Missing return!
```

✅ **Always return the kwargs dict**
```python
def good_ingress(kwargs):
    kwargs['foo'] = 'bar'
    return kwargs
```

❌ **Don't assume data exists**
```python
def bad_ingress(kwargs):
    points = kwargs['points']  # May not exist!
```

✅ **Check with .get()**
```python
def good_ingress(kwargs):
    points = kwargs.get('points')
    if points is None:
        return kwargs
    # ... process points ...
    return kwargs
```

## Performance Tips

- Use conditional ingress for expensive operations
- Warn on large datasets with `warn_on_large_datasets`
- Consider downsampling for visualization
- Cache loaded data sources

## More Examples

See:
- `misc/ingress_framework_tutorial.ipynb` - Interactive tutorial
- `misc/social_network_example.py` - Real-world example
- `misc/INGRESS_FRAMEWORK.md` - Full documentation
