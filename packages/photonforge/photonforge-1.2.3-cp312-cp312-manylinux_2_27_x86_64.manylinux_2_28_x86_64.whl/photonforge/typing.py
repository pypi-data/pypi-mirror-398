import typing as _typ
from collections.abc import Sequence as _Sequence

import tidy3d as _td

from . import extension as _ext


# We cannot use a dataclass here because sphinx autodoc will not respect the custom __repr__
# implementation
class _Metadata:
    __slots__ = (
        "brand",
        "deprecated",
        "description",
        "exclusiveMaximum",
        "exclusiveMinimum",
        "kwargs_for",
        "label",
        "maxItems",
        "maxLength",
        "maximum",
        "minItems",
        "minLength",
        "minimum",
        "optional",
        "units",
    )

    def __init__(
        self,
        brand: str | None = None,
        deprecated: bool = False,
        description: str | None = None,
        exclusiveMaximum: float | int | None = None,
        exclusiveMinimum: float | int | None = None,
        kwargs_for: str | None = None,
        label: str | None = None,
        maxItems: int | None = None,
        maxLength: int | None = None,
        maximum: float | int | None = None,
        minItems: int | None = None,
        minLength: int | None = None,
        minimum: float | int | None = None,
        optional: bool = False,
        units: str | None = None,
    ):
        object.__setattr__(self, "brand", brand)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "exclusiveMaximum", exclusiveMaximum)
        object.__setattr__(self, "exclusiveMinimum", exclusiveMinimum)
        object.__setattr__(self, "kwargs_for", kwargs_for)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "maxItems", maxItems)
        object.__setattr__(self, "maxLength", maxLength)
        object.__setattr__(self, "maximum", maximum)
        object.__setattr__(self, "minItems", minItems)
        object.__setattr__(self, "minLength", minLength)
        object.__setattr__(self, "minimum", minimum)
        object.__setattr__(self, "optional", optional)
        object.__setattr__(self, "units", units)
        object.__setattr__(self, "deprecated", deprecated)

    def items(self):
        return (
            ("brand", self.brand),
            ("deprecated", self.deprecated),
            ("description", self.description),
            ("exclusiveMaximum", self.exclusiveMaximum),
            ("exclusiveMinimum", self.exclusiveMinimum),
            ("kwargs_for", self.kwargs_for),
            ("label", self.label),
            ("maxItems", self.maxItems),
            ("maxLength", self.maxLength),
            ("maximum", self.maximum),
            ("minItems", self.minItems),
            ("minLength", self.minLength),
            ("minimum", self.minimum),
            ("optional", self.optional),
            ("units", self.units),
        )

    def values(self):
        return (
            self.brand,
            self.deprecated,
            self.description,
            self.exclusiveMaximum,
            self.exclusiveMinimum,
            self.kwargs_for,
            self.label,
            self.maxItems,
            self.maxLength,
            self.maximum,
            self.minItems,
            self.minLength,
            self.minimum,
            self.optional,
            self.units,
        )

    def non_optional_copy(self):
        return _Metadata(
            brand=self.brand,
            deprecated=self.deprecated,
            description=self.description,
            exclusiveMaximum=self.exclusiveMaximum,
            exclusiveMinimum=self.exclusiveMinimum,
            kwargs_for=self.kwargs_for,
            label=self.label,
            maxItems=self.maxItems,
            maxLength=self.maxLength,
            maximum=self.maximum,
            minItems=self.minItems,
            minLength=self.minLength,
            minimum=self.minimum,
            optional=False,
            units=self.units,
        )

    def __setattr__(self, _n, _v):
        raise RuntimeError("Immutable object.")

    def __delattr__(self, _n):
        raise RuntimeError("Immutable object.")

    def __repr__(self):
        skip = ("brand", "label", "description", "kwargs_for", "optional", "deprecated")
        values = [f"{k}={v!r}" for k, v in self.items() if v is not None and k not in skip]
        return "_" if len(values) == 0 else ", ".join(values)

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.values() == other.values()

    def __hash__(self):
        return hash(self.values())


def annotate(field, **kwargs):
    """Annotate a type with metadata.

    Args:
        field: Type to be annotated.
        kwargs: Type metadata. See below.

    Return:
        Annotated type.

    Type metadata closely resembles specifications for JSON Schema DRAFT7
    with a few additions. A few commonly used keywords are: ``label``,
    ``description``, ``units``, ``maximum``, ``minimum``,
    ``exclusiveMaximum``, ``exclusiveMinimum``, ``maxItems``, ``minItems``,
    ``maxLength``, and ``minLength``.
    """
    orig = _typ.get_origin(field)
    args = _typ.get_args(field)
    if orig is _typ.Annotated and len(args) == 2 and isinstance(args[1], _Metadata):
        field = args[0]
        metadata = dict(args[1].items())
        metadata.update(kwargs)
    else:
        metadata = kwargs
    return _typ.Annotated[field, _Metadata(**metadata)]


def kwargs_for(fn_or_cls, **annotations):
    """Type that represents keyword arguments for a function or class.

    Args:
        fn_or_cls: Target function or class.

    Return:
        Data type.
    """
    full_name = f"{fn_or_cls.__module__}.{fn_or_cls.__qualname__}"
    return annotate(dict[str, _typ.Any], kwargs_for=full_name, **annotations)


def array(dtype, ndims, ndims_max=None):
    """Type for arrays with specified number of dimensions.

    Args:
        dtype: Scalar type for the array elements.
        ndims: Number of dimensions for the array.
        ndims_max: If set, maximal number of dimensions for the array. Any
          dimensions between ``ndims`` and ``ndims_max`` (inclusive) are
          valid.

    Return:
        Array type.
    """
    if ndims_max is None:
        ndims_max = ndims

    if ndims < 0 or ndims_max < ndims:
        raise RuntimeError(
            "'ndims' cannot be negative and 'ndims_max' cannot be less than 'ndims'."
        )

    field = dtype
    for _ in range(ndims):
        field = _Sequence[field]

    if ndims_max > ndims:
        u = field
        for _ in range(ndims, ndims_max):
            field = _Sequence[field]
            u = u | field
        field = u

    return field


def expression(num_variables, min_expressions):
    """Type for :class:`Expression` with a minimal number of values.

    Args:
        num_variables: Required number of independent variables.
        min_expressions: Minimal number of required expressions.

    Return:
        Expression type.
    """
    return annotate(
        str | _ext.Expression,
        brand="Expression",
        # TODO independentVariables=num_variables,
        # TODO minExpressions=min_expressions,
    )


PositiveInt = annotate(int, exclusiveMinimum=0)  #:
NonNegativeInt = annotate(int, minimum=0)  #:
NegativeInt = annotate(int, exclusiveMaximum=0)  #:
NonPositiveInt = annotate(int, maximum=0)  #:

PositiveFloat = annotate(float, exclusiveMinimum=0)  #:
NonNegativeFloat = annotate(float, minimum=0)  #:
NegativeFloat = annotate(float, exclusiveMaximum=0)  #:
NonPositiveFloat = annotate(float, maximum=0)  #:

Fraction = annotate(float, minimum=0, maximum=1)  #:

Coordinate = annotate(float, units="μm")  #:
Dimension = annotate(NonNegativeFloat, units="μm")  #:
PositiveDimension = annotate(PositiveFloat, units="μm")  #:

Coordinate2D = annotate(_Sequence[Coordinate], minItems=2, maxItems=2)  #:
Dimension2D = annotate(_Sequence[Dimension], minItems=2, maxItems=2)  #:
PositiveDimension2D = annotate(_Sequence[PositiveDimension], minItems=2, maxItems=2)  #:

Angle = annotate(float, units="°")  #:

Frequency = annotate(float, minimum=0, units="Hz")  #:

Time = annotate(float, units="s")  #:
TimeDelay = annotate(float, minimum=0, units="s")  #:

Temperature = annotate(float, minimum=0, units="K")  #:

Voltage = annotate(float, units="V")  #:
Impedance = annotate(complex, units="Ω")  #:

Power = annotate(float, minimum=0, units="W")  #:

Loss = annotate(float, minimum=0, units="dB")  #:
PropagationLoss = annotate(float, minimum=0, units="dB/μm")  #:

Dispersion = annotate(float, units="s/μm²")  #:
DispersionSlope = annotate(float, units="s/μm³")  #:

Layer = annotate(str | tuple[int, int], brand="PhotonForgeLayer")  #:

PortSpecOrName = annotate(str | _ext.PortSpec, brand="PhotonForgePortSpecOrName")  #:

PortReference = annotate(
    tuple[_ext.Reference, str] | tuple[_ext.Reference, str, int],
    brand="PhotonForgePortReference",
)  #:

TerminalReference = annotate(
    tuple[_ext.Reference, str] | tuple[_ext.Reference, str, int],
    brand="PhotonForgeTerminalReference",
)  #:

Medium = annotate(_td.components.medium.MediumType3D, brand="Tidy3dAnyMedium")  #:
