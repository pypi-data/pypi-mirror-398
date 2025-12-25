"""Extensions for cosmograph"""

import cosmograph

# Import the ingress framework and functions
from xcosmo.ingress_framework import (
    IngressPipeline,
    IngressProtocol,
    compose_ingresses,
    chain,
    as_ingress,
    INGRESS_REGISTRY,
    get_ingress,
    list_ingresses,
    log_ingress_call,
    debug_ingress,
    conditional_ingress,
)

from xcosmo.ingress_functions import (
    # Validation
    check_points_and_links_format,
    verify_by_params_reference_existing_columns,
    ensure_links_have_sources_and_targets,
    # Resolution
    resolve_data_sources,
    convert_series_to_dataframe,
    ensure_dataframes_have_index,
    # Parameter resolution
    guess_point_xy_columns,
    infer_color_by_from_clusters,
    set_default_label_column,
    infer_size_from_numeric_columns,
    # Transformation
    normalize_numeric_columns,
    add_point_ids_if_missing,
    # Side effects
    track_dataframe_shapes,
    warn_on_large_datasets,
    # Composite pipelines
    create_smart_defaults_pipeline,
    create_validation_pipeline,
)

# Import cosmo function
from xcosmo.cosmograph import cosmo
