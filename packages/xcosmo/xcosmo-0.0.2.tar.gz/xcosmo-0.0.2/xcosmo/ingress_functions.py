"""
Collection of ready-to-use ingress functions organized by category.

Categories:
1. Validation Ingresses - validate inputs before deeper transformations
2. Data Resolution Ingresses - convert/load external data sources
3. Parameter Resolution Ingresses - fill missing parameters using heuristics
4. Data Transformation Ingresses - mutate or enrich dataframes
5. Side-Effect Ingresses - logging, metrics, caching

"""

from typing import Dict, Any, Optional, Union
import logging
from functools import wraps

from xcosmo.ingress_framework import (
    CosmoKwargs,
    as_ingress,
    INGRESS_REGISTRY,
)

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

try:
    from tabled import get_table

    HAS_TABLED = True
except ImportError:
    HAS_TABLED = False
    get_table = None


# --------------------------------------------------------------------------------------
# Category 1: Validation Ingresses
# --------------------------------------------------------------------------------------


@as_ingress(register=True, category="validation")
def check_points_and_links_format(kwargs: CosmoKwargs) -> CosmoKwargs:
    """Validate that points and links are pandas DataFrames if present."""
    if not HAS_PANDAS:
        return kwargs

    points = kwargs.get("points")
    links = kwargs.get("links")

    if points is not None and not isinstance(points, pd.DataFrame):
        raise TypeError(
            f"points must be a pandas DataFrame, got {type(points).__name__}"
        )

    if links is not None and not isinstance(links, pd.DataFrame):
        raise TypeError(f"links must be a pandas DataFrame, got {type(links).__name__}")

    return kwargs


@as_ingress(register=True, category="validation")
def verify_by_params_reference_existing_columns(kwargs: CosmoKwargs) -> CosmoKwargs:
    """Check that all *_by parameters refer to existing columns in points/links."""
    if not HAS_PANDAS:
        return kwargs

    points = kwargs.get("points")
    links = kwargs.get("links")

    # List of point-related *_by parameters
    point_by_params = [
        "point_x_by",
        "point_y_by",
        "point_size_by",
        "point_color_by",
        "point_label_by",
        "point_id_by",
        "point_index_by",
        "point_label_weight_by",
        "point_cluster_by",
        "point_cluster_strength_by",
        "point_timeline_by",
    ]

    # List of link-related *_by parameters
    link_by_params = [
        "link_source_by",
        "link_target_by",
        "link_color_by",
        "link_width_by",
        "link_arrow_by",
        "link_strength_by",
        "link_timeline_by",
    ]

    errors = []

    # Check point parameters
    if points is not None and isinstance(points, pd.DataFrame):
        point_cols = set(points.columns)
        for param in point_by_params:
            value = kwargs.get(param)
            if value is not None and value not in point_cols:
                errors.append(
                    f"Parameter '{param}' references column '{value}' "
                    f"which doesn't exist in points. Available: {list(point_cols)}"
                )

    # Check link parameters
    if links is not None and isinstance(links, pd.DataFrame):
        link_cols = set(links.columns)
        for param in link_by_params:
            value = kwargs.get(param)
            if value is not None and value not in link_cols:
                errors.append(
                    f"Parameter '{param}' references column '{value}' "
                    f"which doesn't exist in links. Available: {list(link_cols)}"
                )

    if errors:
        raise ValueError("\n".join(errors))

    return kwargs


@as_ingress(register=True, category="validation")
def ensure_links_have_sources_and_targets(kwargs: CosmoKwargs) -> CosmoKwargs:
    """Validate that links have source and target columns specified."""
    if not HAS_PANDAS:
        return kwargs

    links = kwargs.get("links")

    if links is not None and isinstance(links, pd.DataFrame):
        # Check if source and target columns are specified
        link_source_by = kwargs.get("link_source_by")
        link_target_by = kwargs.get("link_target_by")

        if link_source_by is None:
            # Try to infer default source column
            if "source" in links.columns:
                kwargs["link_source_by"] = "source"
                logger.info("Auto-detected 'source' column for links")
            else:
                raise ValueError(
                    "links DataFrame provided but 'link_source_by' not specified "
                    "and 'source' column not found"
                )

        if link_target_by is None:
            # Try to infer default target column
            if "target" in links.columns:
                kwargs["link_target_by"] = "target"
                logger.info("Auto-detected 'target' column for links")
            else:
                raise ValueError(
                    "links DataFrame provided but 'link_target_by' not specified "
                    "and 'target' column not found"
                )

    return kwargs


# --------------------------------------------------------------------------------------
# Category 2: Data Resolution Ingresses
# --------------------------------------------------------------------------------------


@as_ingress(register=True, category="resolution")
def resolve_data_sources(kwargs: CosmoKwargs) -> CosmoKwargs:
    """Convert file paths, URLs, or bytes to DataFrames using tabled.get_table()."""
    if not HAS_TABLED or not HAS_PANDAS:
        return kwargs

    for key in ["points", "links"]:
        value = kwargs.get(key)
        if value is None:
            continue

        # If it's already a DataFrame, skip
        if isinstance(value, pd.DataFrame):
            continue

        # If it's a string (path or URL) or bytes, try to load it
        if isinstance(value, (str, bytes)):
            try:
                df = get_table(value)
                kwargs[key] = df
                logger.info(f"Loaded {key} from {type(value).__name__}")
            except Exception as e:
                logger.warning(f"Could not load {key} from {value}: {e}")

    return kwargs


@as_ingress(register=True, category="resolution")
def convert_series_to_dataframe(kwargs: CosmoKwargs) -> CosmoKwargs:
    """Convert pandas Series to single-column DataFrame."""
    if not HAS_PANDAS:
        return kwargs

    for key in ["points", "links"]:
        value = kwargs.get(key)
        if isinstance(value, pd.Series):
            # Convert to DataFrame with series name as column name
            col_name = value.name or "value"
            kwargs[key] = value.to_frame(name=col_name)
            logger.info(f"Converted {key} from Series to DataFrame")

    return kwargs


@as_ingress(register=True, category="resolution")
def ensure_dataframes_have_index(kwargs: CosmoKwargs) -> CosmoKwargs:
    """Ensure DataFrames have a proper index column for point/link identification."""
    if not HAS_PANDAS:
        return kwargs

    points = kwargs.get("points")
    if points is not None and isinstance(points, pd.DataFrame):
        # If index doesn't have a name, reset it to get a column
        if points.index.name is None and "id" not in points.columns:
            points = points.reset_index(drop=False)
            points = points.rename(columns={"index": "id"})
            kwargs["points"] = points
            # Set point_id_by if not already set
            if kwargs.get("point_id_by") is None:
                kwargs["point_id_by"] = "id"
                logger.info("Added 'id' column to points and set point_id_by='id'")

    return kwargs


# --------------------------------------------------------------------------------------
# Category 3: Parameter Resolution Ingresses
# --------------------------------------------------------------------------------------


@as_ingress(register=True, category="parameter_resolution")
def guess_point_xy_columns(kwargs: CosmoKwargs) -> CosmoKwargs:
    """Infer point_x_by and point_y_by from column names if not specified."""
    if not HAS_PANDAS:
        return kwargs

    points = kwargs.get("points")
    if points is None or not isinstance(points, pd.DataFrame):
        return kwargs

    cols = list(points.columns)
    lower_cols = [c.lower() if isinstance(c, str) else str(c).lower() for c in cols]

    # Try to guess x column
    if kwargs.get("point_x_by") is None:
        x_candidates = ["x", "x_pos", "pos_x", "longitude", "lon", "lng"]
        for candidate in x_candidates:
            if candidate in lower_cols:
                idx = lower_cols.index(candidate)
                kwargs["point_x_by"] = cols[idx]
                logger.info(f"Auto-detected point_x_by='{cols[idx]}'")
                break

    # Try to guess y column
    if kwargs.get("point_y_by") is None:
        y_candidates = ["y", "y_pos", "pos_y", "latitude", "lat"]
        for candidate in y_candidates:
            if candidate in lower_cols:
                idx = lower_cols.index(candidate)
                kwargs["point_y_by"] = cols[idx]
                logger.info(f"Auto-detected point_y_by='{cols[idx]}'")
                break

    return kwargs


@as_ingress(register=True, category="parameter_resolution")
def infer_color_by_from_clusters(kwargs: CosmoKwargs) -> CosmoKwargs:
    """If point_color_by not given, infer from columns matching 'cluster*'."""
    if not HAS_PANDAS:
        return kwargs

    if kwargs.get("point_color_by") is not None:
        return kwargs

    points = kwargs.get("points")
    if points is None or not isinstance(points, pd.DataFrame):
        return kwargs

    # Look for cluster-related columns
    cluster_cols = [
        col
        for col in points.columns
        if isinstance(col, str) and col.lower().startswith("cluster")
    ]

    if cluster_cols:
        # Use the first cluster column
        kwargs["point_color_by"] = cluster_cols[0]
        logger.info(f"Auto-detected point_color_by='{cluster_cols[0]}'")

    return kwargs


@as_ingress(register=True, category="parameter_resolution")
def set_default_label_column(kwargs: CosmoKwargs) -> CosmoKwargs:
    """Choose a label column like 'title', 'name', 'label' if available."""
    if not HAS_PANDAS:
        return kwargs

    if kwargs.get("point_label_by") is not None:
        return kwargs

    points = kwargs.get("points")
    if points is None or not isinstance(points, pd.DataFrame):
        return kwargs

    cols = list(points.columns)
    lower_cols = [c.lower() if isinstance(c, str) else str(c).lower() for c in cols]

    # Label candidates in order of preference
    label_candidates = ["title", "name", "label", "id", "key"]

    for candidate in label_candidates:
        if candidate in lower_cols:
            idx = lower_cols.index(candidate)
            kwargs["point_label_by"] = cols[idx]
            logger.info(f"Auto-detected point_label_by='{cols[idx]}'")
            break

    return kwargs


@as_ingress(register=True, category="parameter_resolution")
def infer_size_from_numeric_columns(kwargs: CosmoKwargs) -> CosmoKwargs:
    """Infer point_size_by from numeric columns with 'size' or 'weight' in name."""
    if not HAS_PANDAS:
        return kwargs

    if kwargs.get("point_size_by") is not None:
        return kwargs

    points = kwargs.get("points")
    if points is None or not isinstance(points, pd.DataFrame):
        return kwargs

    # Look for numeric columns with size/weight in name
    for col in points.columns:
        if not isinstance(col, str):
            continue
        col_lower = col.lower()
        if (
            "size" in col_lower or "weight" in col_lower
        ) and pd.api.types.is_numeric_dtype(points[col]):
            kwargs["point_size_by"] = col
            logger.info(f"Auto-detected point_size_by='{col}'")
            break

    return kwargs


# --------------------------------------------------------------------------------------
# Category 4: Data Transformation Ingresses
# --------------------------------------------------------------------------------------


@as_ingress(register=True, category="transformation")
def normalize_numeric_columns(kwargs: CosmoKwargs) -> CosmoKwargs:
    """Normalize numeric columns to [0, 1] range for better visualization.

    Note: This modifies the DataFrames in-place, creating normalized copies of columns.
    """
    if not HAS_PANDAS:
        return kwargs

    points = kwargs.get("points")
    if points is not None and isinstance(points, pd.DataFrame):
        # Only normalize columns that are used for size or other visual properties
        cols_to_normalize = []
        if kwargs.get("point_size_by"):
            cols_to_normalize.append(kwargs["point_size_by"])

        for col in cols_to_normalize:
            if col in points.columns and pd.api.types.is_numeric_dtype(points[col]):
                min_val = points[col].min()
                max_val = points[col].max()
                if max_val > min_val:
                    normalized = (points[col] - min_val) / (max_val - min_val)
                    norm_col_name = f"{col}_normalized"
                    points[norm_col_name] = normalized
                    logger.info(f"Normalized column '{col}' -> '{norm_col_name}'")

    return kwargs


@as_ingress(register=True, category="transformation")
def add_point_ids_if_missing(kwargs: CosmoKwargs) -> CosmoKwargs:
    """Add sequential IDs to points if no ID column exists."""
    if not HAS_PANDAS:
        return kwargs

    points = kwargs.get("points")
    if points is not None and isinstance(points, pd.DataFrame):
        # Check if there's already an id-like column
        id_cols = [
            col
            for col in points.columns
            if isinstance(col, str) and col.lower() in ["id", "node_id", "point_id"]
        ]

        if not id_cols and kwargs.get("point_id_by") is None:
            # Add a new ID column
            points["id"] = range(len(points))
            kwargs["point_id_by"] = "id"
            logger.info("Added 'id' column to points")

    return kwargs


# --------------------------------------------------------------------------------------
# Category 5: Side-Effect Ingresses (logging, caching, metrics)
# --------------------------------------------------------------------------------------


def make_logging_ingress(name: str):
    """Factory for creating named logging ingresses."""

    @as_ingress(name=f"log_{name}")
    def logger_ingress(kwargs: CosmoKwargs) -> CosmoKwargs:
        logger.info(f"[{name}] Processing kwargs with keys: {list(kwargs.keys())}")
        return kwargs

    return logger_ingress


@as_ingress(register=True, category="side_effect")
def track_dataframe_shapes(kwargs: CosmoKwargs) -> CosmoKwargs:
    """Log the shapes of points and links DataFrames."""
    if not HAS_PANDAS:
        return kwargs

    points = kwargs.get("points")
    links = kwargs.get("links")

    if points is not None and isinstance(points, pd.DataFrame):
        logger.info(f"Points DataFrame shape: {points.shape}")

    if links is not None and isinstance(links, pd.DataFrame):
        logger.info(f"Links DataFrame shape: {links.shape}")

    return kwargs


@as_ingress(register=True, category="side_effect")
def warn_on_large_datasets(kwargs: CosmoKwargs, threshold: int = 10000) -> CosmoKwargs:
    """Warn if datasets are large (may impact performance)."""
    if not HAS_PANDAS:
        return kwargs

    points = kwargs.get("points")
    if points is not None and isinstance(points, pd.DataFrame):
        n_points = len(points)
        if n_points > threshold:
            logger.warning(
                f"Large points dataset: {n_points} rows. "
                f"Consider downsampling for better performance."
            )

    links = kwargs.get("links")
    if links is not None and isinstance(links, pd.DataFrame):
        n_links = len(links)
        if n_links > threshold * 2:
            logger.warning(
                f"Large links dataset: {n_links} rows. "
                f"Consider downsampling for better performance."
            )

    return kwargs


# --------------------------------------------------------------------------------------
# Composite ingresses (combinations of the above)
# --------------------------------------------------------------------------------------


def create_smart_defaults_pipeline():
    """Create a pipeline with common smart defaults."""
    from xcosmo.ingress_framework import IngressPipeline

    return IngressPipeline(
        [
            resolve_data_sources,
            convert_series_to_dataframe,
            check_points_and_links_format,
            add_point_ids_if_missing,
            guess_point_xy_columns,
            set_default_label_column,
            infer_color_by_from_clusters,
            infer_size_from_numeric_columns,
            ensure_links_have_sources_and_targets,
            verify_by_params_reference_existing_columns,
        ],
        name="smart_defaults",
    )


def create_validation_pipeline():
    """Create a pipeline focused on validation."""
    from xcosmo.ingress_framework import IngressPipeline

    return IngressPipeline(
        [
            check_points_and_links_format,
            verify_by_params_reference_existing_columns,
            ensure_links_have_sources_and_targets,
        ],
        name="validation",
    )


# --------------------------------------------------------------------------------------
# Register composite pipelines
# --------------------------------------------------------------------------------------

INGRESS_REGISTRY.register(
    "smart_defaults",
    create_smart_defaults_pipeline(),
    category="composite",
    description="Pipeline with smart parameter inference and validation",
)

INGRESS_REGISTRY.register(
    "validation_only",
    create_validation_pipeline(),
    category="composite",
    description="Pipeline focused on validation only",
)
