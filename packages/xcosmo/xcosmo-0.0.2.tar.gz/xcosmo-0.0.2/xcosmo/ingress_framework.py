"""
Framework for defining, composing, and validating ingress functions.

An ingress function is a transformation applied to the kwargs dictionary before
it's passed to the cosmograph constructor. This module provides:

1. Protocol and type definitions for ingress functions
2. IngressPipeline for composing and executing ingress chains
3. Utilities for wrapping normal functions as ingress functions
4. A registry system for reusable ingress functions
5. Validation and logging capabilities

Architecture:

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

"""

from typing import (
    Dict,
    Any,
    Callable,
    Protocol,
    Sequence,
    TypeVar,
    Union,
    Optional,
    runtime_checkable,
)
from collections.abc import Iterable, Mapping
from functools import wraps, partial, reduce
from inspect import signature, Parameter
import logging

from i2.signatures import Sig, call_forgivingly
from i2.wrapper import Ingress as I2Ingress, kwargs_trans

# Type definitions
CosmoKwargs = Dict[str, Any]
T = TypeVar("T")

# Configure logging
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------------------
# Core Protocol and Types


@runtime_checkable
class IngressProtocol(Protocol):
    """Protocol for ingress functions: kwargs -> kwargs transformations."""

    def __call__(self, kwargs: CosmoKwargs) -> CosmoKwargs:
        """Transform kwargs dictionary.

        Args:
            kwargs: Input keyword arguments dictionary

        Returns:
            Transformed keyword arguments dictionary
        """
        ...


# Union type for various ingress-like inputs
IngressLike = Union[IngressProtocol, Callable[[CosmoKwargs], CosmoKwargs]]


# --------------------------------------------------------------------------------------
# IngressPipeline: Composable chain of ingress functions


class IngressPipeline:
    """A composable pipeline of ingress transformations.

    Provides:
    - Sequential execution of ingress functions
    - Validation of ingress chain
    - Optional logging and debugging
    - Composition via + operator

    Example:
        >>> pipeline = IngressPipeline([
        ...     resolve_data_sources,
        ...     validate_columns,
        ...     guess_defaults,
        ... ])
        >>> transformed = pipeline(kwargs)
    """

    def __init__(
        self,
        ingresses: Sequence[IngressLike] = (),
        *,
        name: Optional[str] = None,
        validate: bool = True,
        log_transforms: bool = False,
    ):
        """Initialize ingress pipeline.

        Args:
            ingresses: Sequence of ingress functions to apply in order
            name: Optional name for this pipeline (for debugging)
            validate: Whether to validate each ingress function
            log_transforms: Whether to log each transformation
        """
        self.ingresses = list(ingresses)
        self.name = name or f"Pipeline[{len(self.ingresses)}]"
        self.validate = validate
        self.log_transforms = log_transforms

        if validate:
            self._validate_ingresses()

    def _validate_ingresses(self):
        """Validate that all ingresses are callable and have reasonable signatures."""
        for i, ingress in enumerate(self.ingresses):
            if not callable(ingress):
                raise TypeError(
                    f"Ingress {i} in pipeline '{self.name}' is not callable: {ingress}"
                )

            # Try to check signature
            try:
                sig = Sig(ingress)
                # Should accept at least one argument (the kwargs dict)
                if len(sig.names) < 1:
                    logger.warning(
                        f"Ingress {i} ({ingress.__name__}) has no parameters. "
                        f"Expected at least one for kwargs."
                    )
            except (ValueError, TypeError):
                # If we can't get signature, just log a warning
                logger.debug(f"Could not validate signature of ingress {i}: {ingress}")

    def __call__(self, kwargs: CosmoKwargs) -> CosmoKwargs:
        """Apply all ingress transformations in sequence.

        Args:
            kwargs: Input keyword arguments

        Returns:
            Transformed keyword arguments after all ingresses applied
        """
        if self.log_transforms:
            logger.info(
                f"Starting pipeline '{self.name}' with kwargs keys: {list(kwargs.keys())}"
            )

        for i, ingress in enumerate(self.ingresses):
            if self.log_transforms:
                before_keys = set(kwargs.keys())

            kwargs = ingress(kwargs)

            if not isinstance(kwargs, dict):
                raise TypeError(
                    f"Ingress {i} in pipeline '{self.name}' did not return a dict. "
                    f"Got {type(kwargs)}: {kwargs}"
                )

            if self.log_transforms:
                after_keys = set(kwargs.keys())
                added = after_keys - before_keys
                removed = before_keys - after_keys
                ingress_name = getattr(ingress, "__name__", repr(ingress))
                logger.info(
                    f"  [{i}] {ingress_name}: "
                    f"added={list(added)}, removed={list(removed)}"
                )

        if self.log_transforms:
            logger.info(
                f"Finished pipeline '{self.name}'. Final keys: {list(kwargs.keys())}"
            )

        return kwargs

    def __add__(
        self, other: Union["IngressPipeline", IngressLike]
    ) -> "IngressPipeline":
        """Compose pipelines using + operator.

        Args:
            other: Another pipeline or ingress function

        Returns:
            New pipeline with combined ingresses
        """
        if isinstance(other, IngressPipeline):
            return IngressPipeline(
                self.ingresses + other.ingresses,
                name=f"{self.name}+{other.name}",
                validate=self.validate,
                log_transforms=self.log_transforms,
            )
        elif callable(other):
            return IngressPipeline(
                self.ingresses + [other],
                name=f"{self.name}+1",
                validate=self.validate,
                log_transforms=self.log_transforms,
            )
        else:
            return NotImplemented

    def __repr__(self):
        return f"IngressPipeline(name='{self.name}', n_ingresses={len(self.ingresses)})"

    @property
    def ingress_names(self):
        """Get names of all ingresses in the pipeline."""
        return [getattr(ing, "__name__", repr(ing)) for ing in self.ingresses]


# --------------------------------------------------------------------------------------
# Composition utilities


def compose_ingresses(
    *ingresses: IngressLike, name: Optional[str] = None
) -> IngressPipeline:
    """Compose multiple ingress functions into a pipeline.

    Args:
        *ingresses: Ingress functions to compose
        name: Optional name for the pipeline

    Returns:
        IngressPipeline that applies all ingresses in sequence

    Example:
        >>> my_ingress = compose_ingresses(
        ...     resolve_data,
        ...     validate_columns,
        ...     guess_defaults,
        ...     name="my_custom_ingress"
        ... )
    """
    return IngressPipeline(ingresses, name=name)


def chain(*ingresses: IngressLike) -> Callable[[CosmoKwargs], CosmoKwargs]:
    """Create a simple function that chains ingress functions.

    Unlike IngressPipeline, this returns a plain function without validation
    or logging capabilities.

    Args:
        *ingresses: Ingress functions to chain

    Returns:
        A function that applies all ingresses in sequence
    """

    def chained(kwargs: CosmoKwargs) -> CosmoKwargs:
        return reduce(lambda kw, ing: ing(kw), ingresses, kwargs)

    return chained


# --------------------------------------------------------------------------------------
# Ingress Registry


class IngressRegistry:
    """Central registry for named ingress functions.

    Allows registration and lookup of reusable ingress functions by name.
    """

    def __init__(self):
        self._registry: Dict[str, IngressLike] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        ingress: IngressLike,
        *,
        category: Optional[str] = None,
        description: Optional[str] = None,
        overwrites_allowed: bool = False,
    ):
        """Register an ingress function.

        Args:
            name: Name to register under
            ingress: The ingress function
            category: Optional category (validation, resolution, transformation, etc.)
            description: Optional description
            overwrites_allowed: Whether to allow overwriting existing registrations
        """
        if name in self._registry and not overwrites_allowed:
            raise ValueError(f"Ingress '{name}' already registered")

        self._registry[name] = ingress
        self._metadata[name] = {
            "category": category,
            "description": description or getattr(ingress, "__doc__", ""),
        }

        logger.debug(f"Registered ingress '{name}' in category '{category}'")

    def get(self, name: str) -> IngressLike:
        """Get an ingress by name.

        Args:
            name: Name of the ingress

        Returns:
            The ingress function

        Raises:
            KeyError: If ingress not found
        """
        return self._registry[name]

    def list_names(self, category: Optional[str] = None) -> list[str]:
        """List registered ingress names.

        Args:
            category: If provided, only list ingresses in this category

        Returns:
            List of ingress names
        """
        if category is None:
            return list(self._registry.keys())
        return [
            name
            for name, meta in self._metadata.items()
            if meta.get("category") == category
        ]

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for an ingress.

        Args:
            name: Name of the ingress

        Returns:
            Metadata dictionary
        """
        return self._metadata.get(name, {})

    def __contains__(self, name: str) -> bool:
        return name in self._registry

    def __getitem__(self, name: str) -> IngressLike:
        return self.get(name)


# Global registry instance
INGRESS_REGISTRY = IngressRegistry()


# --------------------------------------------------------------------------------------
# Decorators and utilities


def as_ingress(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    register: bool = False,
    category: Optional[str] = None,
):
    """Decorator to convert a function into an ingress function.

    Can handle two function signatures:
    1. kwargs -> kwargs (already an ingress)
    2. (points, links, **kwargs) -> modified kwargs (needs wrapping)

    Args:
        func: Function to convert
        name: Optional name for registration
        register: Whether to register in global registry
        category: Category for registration

    Example:
        >>> @as_ingress(register=True, category="validation")
        ... def check_columns(kwargs):
        ...     points = kwargs.get('points')
        ...     if points is not None:
        ...         # validate columns...
        ...     return kwargs
    """

    def decorator(f):
        # Check if function is already ingress-like (takes kwargs dict)
        sig = Sig(f)

        if len(sig.names) == 1:
            # Assume it's already an ingress (kwargs -> kwargs)
            ingress_func = f
        else:
            # Need to wrap it
            ingress_func = _wrap_as_ingress(f)

        # Add metadata
        if name:
            ingress_func.__name__ = name

        # Register if requested
        if register:
            reg_name = name or f.__name__
            INGRESS_REGISTRY.register(
                reg_name, ingress_func, category=category, description=f.__doc__
            )

        return ingress_func

    if func is None:
        # Used with arguments: @as_ingress(register=True)
        return decorator
    else:
        # Used without arguments: @as_ingress
        return decorator(func)


def _wrap_as_ingress(func: Callable) -> Callable[[CosmoKwargs], CosmoKwargs]:
    """Wrap a function with signature (points, links, **kwargs) as an ingress.

    The wrapped function extracts relevant args from kwargs, calls the original
    function, and returns the modified kwargs.
    """
    sig = Sig(func)

    # If first param is 'kwargs', it's already an ingress-like, just call it directly
    if sig.names and sig.names[0] == 'kwargs':
        return func

    @wraps(func)
    def ingress_wrapper(kwargs: CosmoKwargs) -> CosmoKwargs:
        # Extract arguments that the function expects
        try:
            # Use call_forgivingly to handle partial argument matching
            result = call_forgivingly(func, **kwargs)

            # If result is a dict, use it as new kwargs
            if isinstance(result, dict):
                return result
            # If None, return original kwargs unchanged
            elif result is None:
                return kwargs
            # Otherwise, something went wrong
            else:
                raise TypeError(
                    f"Function {func.__name__} returned {type(result)}, "
                    f"expected dict or None"
                )
        except Exception as e:
            logger.error(f"Error in ingress {func.__name__}: {e}")
            raise

    return ingress_wrapper


def validate_ingress(ingress: IngressLike) -> bool:
    """Validate that a function is a proper ingress.

    Args:
        ingress: Function to validate

    Returns:
        True if valid, raises TypeError otherwise
    """
    if not callable(ingress):
        raise TypeError(f"Ingress must be callable, got {type(ingress)}")

    # Try to validate signature
    try:
        sig = Sig(ingress)
        if len(sig.names) < 1:
            raise ValueError(f"Ingress must accept at least one argument (kwargs dict)")
    except Exception as e:
        logger.warning(f"Could not fully validate ingress signature: {e}")

    return True


# --------------------------------------------------------------------------------------
# Helper utilities for ingress development


def log_ingress_call(name: Optional[str] = None):
    """Create a logging ingress (side-effect, returns kwargs unchanged).

    Args:
        name: Optional name for the log message

    Returns:
        An ingress that logs and passes through kwargs
    """

    def logger_ingress(kwargs: CosmoKwargs) -> CosmoKwargs:
        prefix = f"[{name}] " if name else ""
        logger.info(f"{prefix}kwargs keys: {list(kwargs.keys())}")
        return kwargs

    if name:
        logger_ingress.__name__ = f"log_{name}"

    return logger_ingress


def debug_ingress(kwargs: CosmoKwargs) -> CosmoKwargs:
    """Debug ingress that prints kwargs and returns them unchanged."""
    print(f"DEBUG: kwargs = {list(kwargs.keys())}")
    if "points" in kwargs:
        print(f"  points shape: {getattr(kwargs['points'], 'shape', 'N/A')}")
    if "links" in kwargs:
        print(f"  links shape: {getattr(kwargs['links'], 'shape', 'N/A')}")
    return kwargs


def conditional_ingress(
    condition: Callable[[CosmoKwargs], bool], ingress: IngressLike
) -> Callable[[CosmoKwargs], CosmoKwargs]:
    """Create an ingress that only applies if condition is met.

    Args:
        condition: Function that returns True if ingress should be applied
        ingress: The ingress to conditionally apply

    Returns:
        A new ingress that checks condition first
    """

    @wraps(ingress)
    def conditional(kwargs: CosmoKwargs) -> CosmoKwargs:
        if condition(kwargs):
            return ingress(kwargs)
        return kwargs

    return conditional


# --------------------------------------------------------------------------------------
# Convenience functions


def get_ingress(name: str) -> IngressLike:
    """Get an ingress from the global registry by name.

    Args:
        name: Name of the ingress

    Returns:
        The ingress function
    """
    return INGRESS_REGISTRY.get(name)


def list_ingresses(category: Optional[str] = None) -> list[str]:
    """List available ingresses in the global registry.

    Args:
        category: Optional category filter

    Returns:
        List of ingress names
    """
    return INGRESS_REGISTRY.list_names(category)
