"""
Real-world example: Social network analysis with smart ingress pipeline.

This example shows how to use the ingress framework to analyze a social network
with minimal manual parameter specification.
"""

import pandas as pd
import numpy as np
from xcosmo import (
    cosmo,
    compose_ingresses,
    create_smart_defaults_pipeline,
    as_ingress,
)


# --------------------------------------------------------------------------------------
# Create sample social network data
# --------------------------------------------------------------------------------------


def create_social_network_data(n_users=100, n_connections=300):
    """Create synthetic social network data."""
    np.random.seed(42)

    # Create users with various attributes
    users = pd.DataFrame(
        {
            "user_id": range(n_users),
            "name": [f"User_{i}" for i in range(n_users)],
            "x": np.random.randn(n_users) * 10,  # Position x
            "y": np.random.randn(n_users) * 10,  # Position y
            "cluster_community": np.random.randint(0, 5, n_users),  # Community
            "follower_count": np.random.randint(10, 10000, n_users),  # Popularity
            "account_age_days": np.random.randint(1, 1000, n_users),
            "is_verified": np.random.choice([True, False], n_users, p=[0.1, 0.9]),
        }
    )

    # Create connections (friendships/follows)
    connections = pd.DataFrame(
        {
            "source": np.random.randint(0, n_users, n_connections),
            "target": np.random.randint(0, n_users, n_connections),
            "interaction_count": np.random.randint(1, 100, n_connections),
            "connection_strength": np.random.uniform(0, 1, n_connections),
        }
    )

    # Remove self-loops
    connections = connections[connections["source"] != connections["target"]]

    return users, connections


# --------------------------------------------------------------------------------------
# Custom ingress functions for social network analysis
# --------------------------------------------------------------------------------------


@as_ingress(register=True, category="social_network")
def calculate_network_metrics(kwargs):
    """Calculate network metrics: degree, betweenness approximation."""
    points = kwargs.get("points")
    links = kwargs.get("links")

    if points is None or links is None:
        return kwargs

    # Get source/target columns
    source_col = kwargs.get("link_source_by", "source")
    target_col = kwargs.get("link_target_by", "target")

    if source_col not in links.columns or target_col not in links.columns:
        return kwargs

    # Calculate degree (number of connections)
    out_degree = links[source_col].value_counts()
    in_degree = links[target_col].value_counts()

    # Ensure points have an ID column
    id_col = kwargs.get("point_id_by", "user_id")
    if id_col not in points.columns:
        return kwargs

    # Add metrics to points
    points["out_degree"] = points[id_col].map(out_degree).fillna(0)
    points["in_degree"] = points[id_col].map(in_degree).fillna(0)
    points["total_degree"] = points["out_degree"] + points["in_degree"]

    print(
        f"✓ Added network metrics: "
        f"avg degree={points['total_degree'].mean():.1f}, "
        f"max degree={points['total_degree'].max():.0f}"
    )

    return kwargs


@as_ingress(register=True, category="social_network")
def identify_influencers(kwargs, *, top_n=10):
    """Mark top influencers (high degree + high follower count)."""
    points = kwargs.get("points")

    if points is None or "total_degree" not in points.columns:
        return kwargs

    # Composite influence score
    if "follower_count" in points.columns:
        # Normalize both metrics
        degree_norm = (
            points["total_degree"] / points["total_degree"].max()
            if points["total_degree"].max() > 0
            else 0
        )
        follower_norm = (
            points["follower_count"] / points["follower_count"].max()
            if points["follower_count"].max() > 0
            else 0
        )

        points["influence_score"] = (degree_norm + follower_norm) / 2

        # Mark top influencers
        threshold = points["influence_score"].nlargest(top_n).min()
        points["is_influencer"] = points["influence_score"] >= threshold

        n_influencers = points["is_influencer"].sum()
        print(f"✓ Identified {n_influencers} influencers (top {top_n})")

    return kwargs


@as_ingress(register=True, category="social_network")
def enhance_visualization_params(kwargs):
    """Set smart visualization parameters for social networks."""

    # Use degree for node size
    if "total_degree" in kwargs.get("points", pd.DataFrame()).columns:
        if kwargs.get("point_size_by") is None:
            kwargs["point_size_by"] = "total_degree"
            print("✓ Using 'total_degree' for point sizes")

    # Use community for coloring
    if "cluster_community" in kwargs.get("points", pd.DataFrame()).columns:
        if kwargs.get("point_color_by") is None:
            kwargs["point_color_by"] = "cluster_community"
            print("✓ Using 'cluster_community' for point colors")

    # Show arrows on directed links
    if kwargs.get("link_arrows") is None:
        kwargs["link_arrows"] = True
        print("✓ Enabled link arrows for directed graph")

    # Use connection strength for link width
    if "connection_strength" in kwargs.get("links", pd.DataFrame()).columns:
        if kwargs.get("link_width_by") is None:
            kwargs["link_width_by"] = "connection_strength"
            print("✓ Using 'connection_strength' for link widths")

    return kwargs


# --------------------------------------------------------------------------------------
# Create the social network analysis pipeline
# --------------------------------------------------------------------------------------


def create_social_network_pipeline():
    """Create a complete pipeline for social network visualization."""
    return compose_ingresses(
        create_smart_defaults_pipeline(),  # Smart defaults (validation, inference)
        calculate_network_metrics,  # Calculate degree, etc.
        identify_influencers,  # Mark influencers
        enhance_visualization_params,  # Set viz params
        name="social_network_analysis",
    )


# --------------------------------------------------------------------------------------
# Main example
# --------------------------------------------------------------------------------------


def main():
    """Run the social network example."""
    print("=" * 70)
    print("Social Network Analysis with Ingress Framework")
    print("=" * 70)

    # Create data
    print("\n1. Creating synthetic social network data...")
    users, connections = create_social_network_data(n_users=100, n_connections=300)
    print(f"   Users: {len(users)}, Connections: {len(connections)}")
    print(f"   User columns: {list(users.columns)}")

    # Create the pipeline
    print("\n2. Creating social network analysis pipeline...")
    pipeline = create_social_network_pipeline()
    print(f"   Pipeline: {pipeline}")
    print(f"   Ingresses: {pipeline.ingress_names}")

    # Visualize with minimal code
    print("\n3. Creating visualization (automatic parameter inference)...")
    print("-" * 70)

    graph = cosmo(
        points=users,
        links=connections,
        ingress=pipeline,
        # That's it! No need to specify:
        # - point_x_by, point_y_by (inferred from 'x', 'y')
        # - point_label_by (inferred from 'name')
        # - point_color_by (set to 'cluster_community')
        # - point_size_by (set to 'total_degree')
        # - link_source_by, link_target_by (inferred from 'source', 'target')
        # - link_width_by (set to 'connection_strength')
        # - link_arrows (enabled)
    )

    print("-" * 70)
    print("\n4. Graph created successfully!")
    print(
        f"   Points have {len(users.columns)} columns " f"(including computed metrics)"
    )
    print(f"   Check 'total_degree', 'influence_score', 'is_influencer'")

    # Show what the pipeline inferred
    print("\n5. Inferred parameters:")
    test_kwargs = {"points": users, "links": connections}
    result = pipeline(test_kwargs)

    inferred = {
        k: v
        for k, v in result.items()
        if k.startswith(("point_", "link_")) and v is not None
    }
    for key, val in sorted(inferred.items()):
        print(f"   {key} = {val}")

    return graph


# --------------------------------------------------------------------------------------
# Comparison: With vs Without Ingress Framework
# --------------------------------------------------------------------------------------


def comparison_example():
    """Show the difference between manual and automatic parameter specification."""

    users, connections = create_social_network_data(50, 100)

    print("\n" + "=" * 70)
    print("COMPARISON: Manual vs Automatic")
    print("=" * 70)

    # Manual way (OLD)
    print("\n❌ Manual way (lots of boilerplate):")
    print(
        """
    graph = cosmo(
        points=users,
        links=connections,
        point_x_by='x',
        point_y_by='y',
        point_label_by='name',
        point_color_by='cluster_community',
        point_size_by='follower_count',
        link_source_by='source',
        link_target_by='target',
        link_width_by='connection_strength',
        link_arrows=True,
    )
    """
    )

    # Automatic way (NEW)
    print("\n✅ Automatic way (clean and smart):")
    print(
        """
    pipeline = create_social_network_pipeline()
    
    graph = cosmo(
        points=users,
        links=connections,
        ingress=pipeline,
    )
    """
    )

    print(
        "\nResult: Same visualization, but with automatic parameter inference,\n"
        "        computed metrics (degree, influence), and validated data!\n"
    )


if __name__ == "__main__":
    # Run the main example
    graph = main()

    # Show comparison
    comparison_example()

    print("\n" + "=" * 70)
    print("✓ Example completed! Check the graph object above.")
    print("=" * 70)
