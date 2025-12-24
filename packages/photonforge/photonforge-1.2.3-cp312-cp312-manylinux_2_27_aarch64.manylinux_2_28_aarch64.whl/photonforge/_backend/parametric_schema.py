import collections
import inspect
import json
import logging
import pathlib
import re
import types
import typing
from multiprocessing import current_process
from typing import Annotated, Union, get_args, get_origin

import numpy as np
import tidy3d

import photonforge
from photonforge._backend.schema import (
    AbstractBase,
    BaseMatrices,
    ComplexMatrices,
    ComplexNumberJson,
    Float64,
    MatrixScalar,
    schema_lib,
)
from photonforge.typing import _Metadata

td = tidy3d
pf = photonforge

logger = logging.getLogger(f"photonforge.server.worker.{current_process().name}.parametric")

_constraint_keys = (
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "minItems",
    "maxItems",
    "minLength",
    "maxLength",
)

_warning_cache = set()

_array_types = (list, tuple, typing.Sequence, typing.Tuple, typing.List, collections.abc.Sequence)  # noqa: UP006


def match_schema(schema, cls):
    num = len(schema)
    matches = []
    for name, (_, target, _) in schema_lib.items():
        if all(schema.get(k) == v for k, v in target.items()):
            constraints = [k for k in _constraint_keys if k in schema]
            num_constraints = sum(k in target for k in constraints)
            if num_constraints == 0 or num_constraints == len(constraints):
                matches.append((num - len(target), name))

    if len(matches) > 0:
        matches.sort()
        score, name = matches[0]
        cls, target, ref = schema_lib[name]
        if len(matches) > 1 and matches[1][0] == score:
            raise RuntimeError(
                f"Multiple schema matches for {schema}:\n"
                + "\n".join(f"- {r}" for s, r, _ in matches if s == score)
            )
        extra_properties = {k: v for k, v in schema.items() if k not in target}
        schema = {"$ref": ref}
        if len(extra_properties) > 0:
            if "$units" in extra_properties:
                schema["$units"] = extra_properties.pop("$units")
            if len(extra_properties) > 0:
                schema = {"allOf": [schema, extra_properties]}

    return schema, cls


def indented_after(s, n):
    for c in s:
        if c.isspace():
            n -= 1
            if n < 0:
                return True
        else:
            return False
    return False


def parse_docstring(fn_or_cls):
    arg_line = re.compile(r"(\s*)([a-zA-Z0-9_]*)( \([^\)]+\))?:\s?(.*)")
    obj_spec = re.compile(r":(class|func|attr):`([a-zA-Z0-9_.]+\.)*([a-zA-Z0-9_]+)`")
    math_spec = re.compile(r":math:`([^`]+)`")

    doc = fn_or_cls.__doc__
    if not isinstance(doc, str):
        return {}, {}

    lines = doc.splitlines()
    cur = 0
    end = len(lines)

    # Look for arguments section
    while cur < end and lines[cur].strip() != "Args:":
        cur += 1
    cur += 1

    # Skip blank lines
    while cur < end and len(lines[cur].strip()) == 0:
        cur += 1

    # Start parsing arguments until blank line
    descriptions = {}
    annotations = {}
    while cur < end and len(lines[cur].strip()) != 0:
        m = arg_line.match(lines[cur])
        cur += 1
        if m is not None:
            indent, name, annotation, tooltip = m.groups()
            indent = len(indent)
            while cur < end and indented_after(lines[cur], indent):
                tooltip += " " + lines[cur].strip()
                cur += 1
            while m := obj_spec.search(tooltip):
                tooltip = tooltip[: m.start()] + m.group(3) + tooltip[m.end() :]
            while m := math_spec.search(tooltip):
                tooltip = "$".join((tooltip[: m.start()], m.group(1), tooltip[m.end() :]))
            tooltip = tooltip.replace("``", "")
            i = tooltip.find(".")
            if i > 0:
                tooltip = tooltip[: i + 1]
            descriptions[name] = tooltip
            if annotation is not None:
                annotations[name] = typing.ForwardRef(annotation[2:-1])

    return descriptions, annotations


def find_target(target):
    target = target.split(".")
    match = globals().get(target[0])
    if match is None:
        for obj in globals().values():
            if type(obj) is types.ModuleType and getattr(obj, "__name__", None) == target[0]:
                match = obj
                break
    for key in target[1:]:
        if match is None:
            break
        match = getattr(match, key, None)
    return match


pf_type_names = {n for n in dir(pf) if n[0].isupper() and type(getattr(pf, n)) is type}
pf_types = tuple(getattr(pf, n) for n in pf_type_names)


def make_serializable(obj, cls=None):
    if obj is not None:
        if isinstance(cls, type) and issubclass(cls, AbstractBase):
            return cls.from_python(obj).model_dump()

        elif (
            isinstance(cls, tuple)
            and hasattr(obj, "__iter__")
            and hasattr(obj, "__len__")
            and len(obj) > 0
        ):
            if len(cls) == 1:
                return [make_serializable(x, cls[0]) for x in obj]
            elif len(cls) == len(obj):
                return [make_serializable(x, c) for x, c in zip(obj, cls, strict=False)]

        elif isinstance(cls, list):
            for c in cls:
                if c is not None:
                    try:
                        return make_serializable(obj, c)
                    except Exception:
                        pass

    if isinstance(obj, complex):
        return [obj.real, obj.imag]

    if isinstance(obj, pf_types):
        return obj._id

    if isinstance(obj, td.components.base.Tidy3dBaseModel):
        return obj._json()

    if isinstance(obj, (list, tuple, set, frozenset)):
        return [make_serializable(x) for x in obj]

    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}

    if isinstance(obj, pathlib.Path):
        return str(obj)

    if isinstance(obj, np.generic):
        obj = obj.item()
        if isinstance(obj, complex):
            obj = (obj.real, obj.imag)
        return obj

    if isinstance(obj, np.ndarray):
        if np.iscomplex(obj).any():
            obj = np.stack((obj.real, obj.imag), axis=-1)
        return obj.tolist()

    return obj


def check_abstract_matrix(schema, cls, metadata):
    items = schema.get("items")
    if (
        schema.get("type") == "array"
        and isinstance(items, dict)
        and isinstance(cls, tuple)
        and len(cls) == 1
        and (cls[0] is ComplexNumberJson or cls[0] in typing.get_args(MatrixScalar))
    ):
        if cls[0] is ComplexNumberJson:
            cls = ComplexMatrices[0]
            items = {"$ref": Float64.ref_schema()}
            shape_items = [
                {"type": "integer", "minimum": 1},
                {"type": "integer", "minimum": 1},
                {"type": "number", "const": 2},
            ]
        else:
            cls = BaseMatrices[0]
            shape_items = [{"type": "integer", "minimum": 1}, {"type": "integer", "minimum": 1}]

        if "minItems" in schema and schema["minItems"] > 1:
            shape_items[1]["minimum"] = schema["minItems"]
        if "maxItems" in schema and schema["maxItems"] > 0:
            shape_items[1]["maximum"] = schema["maxItems"]

        minimum = metadata.get("minItems")
        if minimum is not None:
            del metadata["minItems"]
            if minimum > 1:
                shape_items[0]["minimum"] = minimum
        maximum = metadata.get("maxItems")
        if maximum is not None:
            del metadata["maxItems"]
            if maximum > 0:
                shape_items[0]["maximum"] = maximum

        schema = {"allOf": [{"$ref": cls.ref_schema()}, {"properties": {"data": {"items": items}}}]}
        if ("maximum" in shape_items[0] or shape_items[0]["minimum"] > 1) or (
            "maximum" in shape_items[1] or shape_items[1]["minimum"] > 1
        ):
            schema["allOf"][1]["properties"]["shape"] = {"type": "array", "items": shape_items}

    elif cls in BaseMatrices[:-1] or cls in ComplexMatrices[:-1]:
        is_complex = cls in ComplexMatrices[:-1]
        if is_complex:
            i = ComplexMatrices.index(cls)
            cls = ComplexMatrices[i + 1]
        else:
            i = BaseMatrices.index(cls)
            cls = BaseMatrices[i + 1]

        items = schema["allOf"][1]["properties"]["data"]["items"]
        shape = schema["allOf"][1]["properties"].get("shape")

        shape_item = {"type": "integer", "minimum": 1}
        minimum = metadata.get("minItems")
        if minimum is not None:
            del metadata["minItems"]
            if minimum > 1:
                shape_item["minimum"] = minimum
        maximum = metadata.get("maxItems")
        if maximum is not None:
            del metadata["maxItems"]
            if maximum > 0:
                shape_item["maximum"] = maximum

        schema = {"allOf": [{"$ref": cls.ref_schema()}, {"properties": {"data": {"items": items}}}]}
        if "maximum" in shape_item or shape_item["minimum"] > 1 or shape:
            if not shape:
                shape = {
                    "type": "array",
                    "items": [{"type": "integer", "minimum": 1}] * (i + 2),
                }
                if is_complex:
                    shape["items"].append({"type": "number", "const": 2})
            shape["items"].insert(0, shape_item)
            schema["allOf"][1]["properties"]["shape"] = shape

    else:
        schema = {"type": "array", "items": schema}
        cls = (cls,)  # tuple, len 1 == single class for whole array
    return schema, cls


def schema_from_type(
    field, default=inspect.Parameter.empty, ignore_optional=False, full_output=False
):
    orig = get_origin(field)
    args = get_args(field)

    # ignore the first optional level in field
    if ignore_optional and orig is Union and types.NoneType in args:
        args = tuple(t for t in args if t is not types.NoneType)
        if len(args) == 1:
            field = args[0]
            orig = get_origin(field)
            args = get_args(field)
        else:
            field = orig.__getitem__(args)

    # split metadata, if any
    metadata = _Metadata()
    if orig is Annotated and len(args) > 1:
        field = args[0]
        for arg in args[1:]:
            if isinstance(arg, _Metadata):
                metadata = arg
                break

    if metadata.optional:
        # Force optional (only makes sense for ignore_optional, but still valid otherwise)
        field = Annotated[field, metadata.non_optional_copy()] | None
        metadata = _Metadata()

    if isinstance(field, typing.ForwardRef):
        try:
            field = field._evaluate(None, None, type_params=(), recursive_guard=frozenset())
        except NameError:
            localns = {
                **{k: getattr(typing, k) for k in dir(typing) if k[0] != "_"},
                **{k: getattr(pf, k) for k in dir(pf) if k[0] != "_"},
                **{k: getattr(td, k) for k in dir(td) if k[0] != "_"},
            }
            try:
                field = field._evaluate(
                    localns=localns, globalns=None, type_params=(), recursive_guard=frozenset()
                )
            except NameError:
                logger.warning(f"Unable to evaluate {field!r}.")

    args = get_args(field)
    field = get_origin(field) or field

    metadata = dict(metadata.items())

    label = metadata.pop("label")

    not_found = ({}, default, None, label, None) if full_output else {}

    if metadata.pop("deprecated"):
        return not_found

    units = metadata.pop("units")
    if units is not None:
        metadata["$units"] = units

    kwargs_for = metadata.pop("kwargs_for")
    if kwargs_for is not None:
        target = kwargs_for
        kwargs_for = find_target(target)
        if kwargs_for is None:
            logger.warning(f"Kwargs target '{target}' not found in registries.")

    brand = metadata.pop("brand")
    optional = metadata.pop("optional")
    cls = None
    if brand is None:
        if field is types.NoneType:
            schema = {"type": "null"}
            optional = True
        elif field is bool:
            schema = {"type": "boolean"}
        elif field is int:
            schema = {"type": "integer"}
        elif field is float:
            schema = {"type": "number"}
        elif field is str:
            schema = {"type": "string"}
        # elif field is bytes:
        #     schema = {"type": "string"}
        elif field is complex:
            cls, _, ref = schema_lib["ComplexNumberJson"]
            schema = {"$ref": ref}
        elif field in _array_types and len(args) > 0:
            if all(x == args[0] for x in args[1:]):
                schema, _, _, _, cls = schema_from_type(args[0], full_output=True)
                schema, cls = check_abstract_matrix(schema, cls, metadata)
            else:
                results = [schema_from_type(x, full_output=True) for x in args]
                schema = {"type": "array", "items": [r[0] for r in results]}
                # tuple == one class per item
                cls = tuple(r[4] for r in results)
        elif (field is Union or field is types.UnionType) and len(args) > 0:
            results = [schema_from_type(x, full_output=True) for x in args]
            schema = {"anyOf": [r[0] for r in results if len(r[0]) > 0]}
            # list == optional classes for single item
            cls = [r[4] for r in results if len(r[0]) > 0]
            optional = optional or any(r[2] for r in results if len(r[0]) > 0)
        elif field is typing.Literal and len(args) > 0 and all(isinstance(x, str) for x in args):
            schema = {"type": "string", "enum": list(args)}
        elif (
            field is typing.Literal
            and len(args) > 0
            and all(isinstance(x, (int, float)) for x in args)
        ):
            schema = {"type": "number", "enum": list(args)}
        elif field in (dict, typing.Mapping, collections.abc.Mapping) and kwargs_for is not None:
            schema, _ = inspect_parameters(kwargs_for)
        # elif (
        #     field in (dict, typing.Mapping, collections.abc.Mapping)
        #     and len(args) > 0
        #     and args[0] is str
        # ):
        #     schema = {"type": "null"}
        elif field in pf_types:
            brand = f"PhotonForge{field.__name__}"
            if brand not in schema_lib:
                return not_found
            cls, _, ref = schema_lib[brand]
            schema = {"$ref": ref}
        elif isinstance(field, type) and issubclass(field, td.components.base.Tidy3dBaseModel):
            brand = f"Tidy3d{field.__name__}"
            if brand not in schema_lib:
                return not_found
            cls, _, ref = schema_lib[brand]
            schema = {"$ref": ref}
        else:
            return not_found
    else:
        if brand not in schema_lib:
            return not_found
        cls, _, ref = schema_lib[brand]
        schema = {"$ref": ref}

    if "allOf" in schema and "$ref" in schema["allOf"][0]:
        # Matrix composition
        schema["allOf"][0].update({x for x in metadata.items() if x[1] is not None})
    else:
        schema.update({x for x in metadata.items() if x[1] is not None})
        if "$ref" not in schema:
            schema, cls = match_schema(schema, cls)

    # None set as a flag for config defaults, but not valid
    if not optional and default is None:
        default = inspect.Parameter.empty
    elif default is not inspect.Parameter.empty:
        default = make_serializable(default, cls)

    return (schema, default, optional, label, cls) if full_output else schema


def inspect_parameters(fn_or_cls, kwargs={}):
    ignore_optional = fn_or_cls.__module__ == "photonforge.parametric"
    descriptions, annotations = parse_docstring(fn_or_cls)
    parameters = {}
    signature = inspect.signature(fn_or_cls)
    all_required = []
    classes = {}
    for parameter in signature.parameters.values():
        field = (
            annotations.get(parameter.name)
            if parameter.annotation is inspect.Parameter.empty
            else parameter.annotation
        )
        default = kwargs[parameter.name] if parameter.name in kwargs else parameter.default
        schema, default, optional, label, cls = schema_from_type(
            field, default, ignore_optional, True
        )
        if len(schema) == 0:
            if field not in _warning_cache:
                _warning_cache.add(field)
                logger.warning(
                    f"No schema for '{parameter.name}: {field}' in '{fn_or_cls.__qualname__}'."
                )
            continue
        schema["title"] = label or parameter.name.replace("_", " ").title()
        if default is not inspect.Parameter.empty:
            schema["default"] = default
        if parameter.name in descriptions:
            schema["description"] = descriptions[parameter.name]
        parameters[parameter.name] = schema
        classes[parameter.name] = cls
        if not optional:
            all_required.append(parameter.name)
    schema = {"type": "object", "properties": parameters}
    if len(all_required) > 0:
        schema["required"] = all_required
    return schema, classes


def deserialize(value, cls):
    valid = False
    if isinstance(cls, list):
        # list == optional classes for single item
        for c in cls:
            value, valid = deserialize(value, c)
            if valid:
                break
    elif isinstance(cls, tuple) and isinstance(value, (list, tuple)):
        result = [None] * len(value)
        if len(cls) == 1:
            c = cls[0]
            # tuple, len 1 == single class for whole array
            for i, v in enumerate(value):
                result[i], valid = deserialize(v, c)
                if not valid:
                    break
        elif len(cls) == len(value):
            # tuple == one class per item
            for i, (v, c) in enumerate(zip(value, cls, strict=False)):
                result[i], valid = deserialize(v, c)
                if not valid:
                    break
        if valid:
            value = result
    elif isinstance(cls, type) and issubclass(cls, AbstractBase):
        try:
            model = cls.from_json(value)
            value = model.to_python
            valid = True
        except Exception:
            pass
    else:
        try:
            value = cls(value)
            valid = True
        except Exception:
            pass
    return value, valid


def kwargs_from_schema(schema, classes):
    result = {}
    for parameter_name, value in schema.items():
        result[parameter_name], _ = deserialize(value, classes.get(parameter_name))
    return result


def pretty_json(obj):
    if not isinstance(obj, (dict, list, tuple)):
        obj, _ = inspect_parameters(obj)
    return json.dumps(obj, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    import sys

    from photonforge._backend.schema import make_validator

    logging.basicConfig()

    validator = make_validator(sys.argv[1]) if len(sys.argv) > 1 else None

    path = pathlib.Path(__file__).parent / "../../example_schemas/types"
    path.mkdir(exist_ok=True, parents=True)
    for file in path.glob("*.json"):
        file.unlink()

    for n in dir(pf.typing):
        if not n[0].isupper():
            continue
        s = schema_from_type(getattr(pf.typing, n))
        if validator:
            validator.validate(s)
        (path / f"{n}.json").write_text(pretty_json(s))

    path = pathlib.Path(__file__).parent / "../../example_schemas/parametric"
    path.mkdir(exist_ok=True, parents=True)
    for file in path.glob("*.json"):
        file.unlink()

    for n in dir(pf):
        if n[0] == "_" or not n.endswith("Model"):
            continue
        cls = getattr(pf, n)
        if cls is pf.Model or not isinstance(cls, type) or not issubclass(cls, pf.Model):
            continue
        if validator:
            validator.validate(s)
        s, _ = inspect_parameters(cls)
        (path / f"{n}.json").write_text(pretty_json(s))

    for n in dir(pf.parametric):
        if n[0] == "_" or n.startswith("route"):
            continue
        fn = getattr(pf.parametric, n)
        s, _ = inspect_parameters(fn)
        if validator:
            validator.validate(s)
        (path / f"{n}.json").write_text(pretty_json(s))
