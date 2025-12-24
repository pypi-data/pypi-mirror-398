import json
from pathlib import Path
from typing import ClassVar, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, PositiveInt, RootModel


def fix_refs(j):
    if isinstance(j, list):
        for i in range(len(j)):
            fix_refs(j[i])

    if isinstance(j, dict):
        if "$ref" in j:
            s = j["$ref"]
            if "flexcompute" not in s:
                cls = globals()[s[s.rfind("/") + 1 :]]
                j["$ref"] = cls.ref_schema()
        for k in j:
            fix_refs(j[k])


def fix_fields(j):
    if "title" in j:
        del j["title"]

    if "$defs" in j:
        del j["$defs"]

    if "prefixItems" in j:
        j["items"] = j["prefixItems"]
        del j["prefixItems"]

    jp = j.get("properties")
    if jp:
        j["additionalProperties"] = False
        for k in jp:
            fix_fields(jp[k])


class AbstractBase(BaseModel):
    _version: ClassVar[str] = "1.0.0"

    @classmethod
    def ref_schema(cls):
        return f"https://flexcompute.com/schemas/{cls._version}/{cls.__name__}.json"

    @classmethod
    def fixed_json_schema(cls, *args, **kwargs):
        j = cls.model_json_schema(*args, **kwargs)
        fix_fields(j)
        fix_refs(j)
        return j

    @classmethod
    def from_json(cls, obj):
        return cls.model_validate(obj)

    @classmethod
    def from_python(cls, obj):
        return cls(obj)

    @property
    def to_python(self):
        return self.root


def remove_default(j):
    del j["default"]


class Null(AbstractBase, RootModel):
    root: None = Field(None, json_schema_extra=remove_default)


class Integer(AbstractBase, RootModel):
    root: int


class NegativeInteger(AbstractBase, RootModel):
    root: int = Field(..., lt=0)


class PositiveInteger(AbstractBase, RootModel):
    root: int = Field(..., gt=0)


class NonPositiveInteger(AbstractBase, RootModel):
    root: int = Field(..., le=0)


class NonNegativeInteger(AbstractBase, RootModel):
    root: int = Field(..., ge=0)


class Float64(AbstractBase, RootModel):
    root: float


class NegativeFloat64(AbstractBase, RootModel):
    root: float = Field(..., lt=0)


class PositiveFloat64(AbstractBase, RootModel):
    root: float = Field(..., gt=0)


class NonPositiveFloat64(AbstractBase, RootModel):
    root: float = Field(..., le=0)


class NonNegativeFloat64(AbstractBase, RootModel):
    root: float = Field(..., ge=0)


class UnitIntervalFloat64(AbstractBase, RootModel):
    root: float = Field(..., ge=0, le=1)


class UnitBallIntervalFloat64(AbstractBase, RootModel):
    root: float = Field(..., ge=-1, le=1)


class CenteredUnitIntervalFloat64(AbstractBase, RootModel):
    root: float = Field(..., ge=-0.5, le=0.5)


class ComplexNumberJson(AbstractBase, RootModel):
    root: tuple[float, float]

    @classmethod
    def from_python(cls, obj):
        z = complex(obj)
        return cls((z.real, z.imag))

    @property
    def to_python(self):
        return self.root[0] + 1j * self.root[1]


def fix_shape(j):
    if "maxItems" in j:
        del j["maxItems"]
    if "minItems" in j:
        del j["minItems"]
    items = j["prefixItems"]
    for i in range(len(items)):
        if items[i].get("exclusiveMinimum") == 0:
            items[i]["minimum"] = 1
            del items[i]["exclusiveMinimum"]


MatrixScalar = (
    float
    | CenteredUnitIntervalFloat64
    | Float64
    | NegativeFloat64
    | NegativeInteger
    | NonNegativeFloat64
    | NonPositiveFloat64
    | PositiveFloat64
    | UnitBallIntervalFloat64
    | UnitIntervalFloat64
    | Integer
    | NonNegativeInteger
    | NonPositiveInteger
    | PositiveInteger
)


class AbstractMatrix(AbstractBase):
    data: list[MatrixScalar] = Field(min_length=1)

    @classmethod
    def from_python(cls, obj):
        array = np.array(obj)
        return cls(data=array.flatten(order="F").tolist(), shape=array.shape)

    @property
    def to_python(self):
        return np.array(self.data).reshape(self.shape, order="F")


class BaseMatrix2D(AbstractMatrix):
    shape: tuple[PositiveInt, PositiveInt] = Field(json_schema_extra=fix_shape)


class BaseMatrix3D(AbstractMatrix):
    shape: tuple[PositiveInt, PositiveInt, PositiveInt] = Field(json_schema_extra=fix_shape)


class BaseMatrix4D(AbstractMatrix):
    shape: tuple[PositiveInt, PositiveInt, PositiveInt, PositiveInt] = Field(
        json_schema_extra=fix_shape
    )


class BaseMatrix5D(AbstractMatrix):
    shape: tuple[PositiveInt, PositiveInt, PositiveInt, PositiveInt, PositiveInt] = Field(
        json_schema_extra=fix_shape
    )


BaseMatrices = (BaseMatrix2D, BaseMatrix3D, BaseMatrix4D, BaseMatrix5D)


def complex_matrix_from_base(j):
    shape = j["properties"]["shape"]
    shape["items"] = shape["prefixItems"]
    del shape["prefixItems"]
    del shape["title"]
    base = BaseMatrices[len(shape["items"]) - 2]
    j.clear()
    j["allOf"] = [
        {"$ref": base.ref_schema()},
        {
            "type": "object",
            "properties": {"shape": shape},
            "required": ["shape"],
            "additionalProperties": False,
        },
    ]


class AbstractComplexMatrix(AbstractBase):
    data: list[float] = Field(min_length=1)

    model_config = ConfigDict(json_schema_extra=complex_matrix_from_base)

    @classmethod
    def from_python(cls, obj):
        array = np.array(obj, dtype=complex)
        array = np.stack((array.real, array.imag), axis=0)
        return cls(data=array.flatten(order="F").tolist(), shape=array.shape)

    @property
    def to_python(self):
        array = np.array(self.data).reshape(self.shape, order="F")
        return array[0] + 1j * array[1]


class Matrix2DComplexNumber(AbstractComplexMatrix):
    shape: tuple[PositiveInt, PositiveInt, Literal[2.0]] = Field(json_schema_extra=fix_shape)


class Matrix3DComplexNumber(AbstractComplexMatrix):
    shape: tuple[PositiveInt, PositiveInt, PositiveInt, Literal[2.0]] = Field(
        json_schema_extra=fix_shape
    )


class Matrix4DComplexNumber(AbstractComplexMatrix):
    shape: tuple[PositiveInt, PositiveInt, PositiveInt, PositiveInt, Literal[2.0]] = Field(
        json_schema_extra=fix_shape
    )


ComplexMatrices = (Matrix2DComplexNumber, Matrix3DComplexNumber, Matrix4DComplexNumber)

schema_lib = {}
for cls in (
    Null,
    Integer,
    NegativeInteger,
    PositiveInteger,
    NonPositiveInteger,
    NonNegativeInteger,
    Float64,
    NegativeFloat64,
    PositiveFloat64,
    NonPositiveFloat64,
    NonNegativeFloat64,
    UnitIntervalFloat64,
    UnitBallIntervalFloat64,
    CenteredUnitIntervalFloat64,
    ComplexNumberJson,
    BaseMatrix2D,
    BaseMatrix3D,
    BaseMatrix4D,
    BaseMatrix5D,
    Matrix2DComplexNumber,
    Matrix3DComplexNumber,
    Matrix4DComplexNumber,
):
    schema_lib[cls.__name__] = (cls, cls.fixed_json_schema(), cls.ref_schema())


def make_validator(json_repo: str):
    from jsonschema import Draft7Validator  # noqa: PLC0415
    from referencing import Registry, Resource  # noqa: PLC0415
    from referencing.jsonschema import DRAFT7  # noqa: PLC0415

    schema_path = Path(json_repo).expanduser()
    registry = Registry()

    for f in schema_path.glob("**/*.json"):
        if f.name == "schemas-index.json":
            continue

        schema = json.loads(f.read_text())

        if f.name == "property-composition-schema.json":
            composition_schema = schema

        resource = Resource(contents=schema, specification=DRAFT7)
        registry = registry.with_resource(uri=schema["$id"], resource=resource)

    return Draft7Validator(composition_schema, registry=registry)


if __name__ == "__main__":
    import sys

    def cleanup(j):
        if isinstance(j, list):
            for i in range(len(j)):
                cleanup(j[i])

        if isinstance(j, dict):
            if j.get("minimum") == -9007199254740991:
                del j["minimum"]
            if j.get("maximum") == 9007199254740991:
                del j["maximum"]

            for k in j:
                cleanup(j[k])

    def print_diff(a, b, prefix="-"):
        if a == b:
            return
        if type(a) is not type(b):
            print(f"{prefix} type mismatch: {type(a)!r} != {type(b)!r}")
        elif isinstance(a, dict):
            for k in b:
                if k not in a:
                    print(f"{prefix} {k!r} missing in first dictionary")
            for k in a:
                if k not in b:
                    print(f"{prefix} {k!r} missing in second dictionary")
            for k in a:
                if k in b:
                    print_diff(a[k], b[k], f"{prefix}[{k!r}]")
        elif isinstance(a, (list, tuple)):
            if len(a) != len(b):
                print(f"{prefix} different lengths: {len(a)} != {len(b)}")
            for i in range(min(len(a), len(b))):
                print_diff(a[i], b[i], f"{prefix}[{i}]")
        else:
            print(f"{prefix} difference: {a!r} != {b!r}")

    schema_path = Path(sys.argv[1]).expanduser()

    # Not used in photonforge
    skipped = {
        "AlphaString",
        "AlphanumericString",
        "Base58UuidV4",
        "ISO8601DateTime",
        "LowercaseAlphaString",
        "Matrix2AffineTransform",
        "Matrix2BasicTransform",
        "Matrix2DFloat64",
        "Matrix2DPositiveInteger",
        "Matrix2Json",
        "Matrix2RowMajorJson",
        "Matrix3DFloat64",
        "Matrix3DPositiveInteger",
        "Matrix3Json",
        "Matrix3RowMajorJson",
        "Matrix4Json",
        "Matrix4RowMajorJson",
        "Matrix4x3AffineJson",
        "NonEmptyString",
        "NonNullQuaternionJson",
        "NonNullVector2Json",
        "NonNullVector3Json",
        "NonNullVector4Json",
        "PropertyCompositionSchema",
        "QuaternionJson",
        "RegExpPattern",
        "SemanticVersion",
        "SemanticVersionSpec",
        "Sha256",
        "TrimmedString",
        "UnitQuaternionJson",
        "UnitVector2Json",
        "UnitVector3Json",
        "UnitVector4Json",
        "UnitsDSL",
        "UppercaseAlphaString",
        "UuidV4",
        "UuidV5",
        "Vector2Json",
        "Vector3Json",
        "Vector4Json",
    }

    frontend_lib = {}
    index_keys = []
    for f in schema_path.glob("**/*.json"):
        schema = json.loads(f.read_text())

        if f.name == "schemas-index.json":
            index_keys = sorted(set(schema["schemas"]) - skipped)
            continue

        ref = schema.pop("$id")
        if not isinstance(ref, str):
            continue

        brand = schema.pop("title")
        # Generic schemas that should only be matched by brand, not here
        if brand in skipped:
            continue

        # Unused for matching
        schema.pop("$schema")
        cleanup(schema)

        frontend_lib[brand] = schema

    print_diff(index_keys, sorted(frontend_lib))

    for key, schema in frontend_lib.items():
        if key not in schema_lib:
            print(f"Missing {key}")
            continue

        if schema_lib[key][1] != schema:
            print(f"Schema error in {key}:")
            print("- Zod:", json.dumps(schema, indent=2, ensure_ascii=False))
            print("- Lib:", json.dumps(schema_lib[key][1], indent=2, ensure_ascii=False))
            print_diff(schema, schema_lib[key][1])
