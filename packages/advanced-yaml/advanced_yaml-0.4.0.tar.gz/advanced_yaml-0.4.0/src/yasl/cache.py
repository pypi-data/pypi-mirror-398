import logging
from enum import Enum
from types import MappingProxyType
from typing import Any, Optional

from pydantic import BaseModel


class YaslRegistry:
    """
    Singleton registry for YASL type definitions and enumerations.
    Supports registration and lookup by name and optional namespace.
    """

    _instance: Optional["YaslRegistry"] = None

    def __new__(cls) -> "YaslRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_registry()
        return cls._instance

    def _init_registry(self) -> None:
        self.yasl_type_defs: dict[tuple[str, str | None], BaseModel] = {}
        self.yasl_enumerations: dict[tuple[str, str | None], Enum] = {}
        self.unique_values_store: dict[tuple[str, str | None], dict[str, set]] = {}

    def register_type(self, name: str, type_def: BaseModel, namespace: str) -> None:
        key = (name, namespace)
        log = logging.getLogger("yasl")
        if key in self.yasl_type_defs:
            raise ValueError(f"Type '{name}' already exists in namespace '{namespace}'")
        self.yasl_type_defs[key] = type_def
        log.debug(f"Registered type '{name}' in namespace '{namespace}'")

    def get_types(self) -> MappingProxyType[tuple[str, str | None], BaseModel]:
        # Return a read-only view of the registered types
        return MappingProxyType(self.yasl_type_defs)

    def get_type(
        self,
        name: str,
        namespace: str | None = None,
        default_namespace: str | None = None,
    ) -> BaseModel | None:
        log = logging.getLogger("yasl")
        log.debug(
            f"Looking up type '{name}' in namespace '{namespace}' with default namespace '{default_namespace}'"
        )
        if namespace is not None:
            key = (name, namespace)
            if key in self.yasl_type_defs:
                return self.yasl_type_defs[key]
            return None
        matches = [v for (n, ns), v in self.yasl_type_defs.items() if n == name]
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]
        elif default_namespace is not None:
            log.debug(
                f"Trying default namespace '{default_namespace}' for type '{name}'"
            )
            key = (name, default_namespace)
            if key in self.yasl_type_defs:
                return self.yasl_type_defs[key]
        raise ValueError(
            f"Ambiguous type name '{name}': found in multiple namespaces {matches}. Specify a namespace."
        )

    def register_enum(self, name: str, enum_def: Enum, namespace: str) -> None:
        log = logging.getLogger("yasl")
        key = (name, namespace)
        if key in self.yasl_enumerations:
            raise ValueError(f"Enum '{name}' already exists in namespace '{namespace}'")
        self.yasl_enumerations[key] = enum_def
        log.debug(f"Registered enum '{name}' in namespace '{namespace}'")

    def get_enums(self) -> list[tuple[str, str | None]]:
        return [(n, ns) for (n, ns) in self.yasl_enumerations.keys()]

    def get_enum(
        self,
        name: str,
        namespace: str | None = None,
        default_namespace: str | None = None,
    ) -> Enum | None:
        log = logging.getLogger("yasl")
        log.debug(
            f"Looking up enum '{name}' in namespace '{namespace}' with default namespace '{default_namespace}'"
        )
        if namespace is not None:
            key = (name, namespace)
            if key in self.yasl_enumerations:
                return self.yasl_enumerations[key]
            return None
        matches = [v for (n, ns), v in self.yasl_enumerations.items() if n == name]
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]
        elif default_namespace is not None:
            key = (name, default_namespace)
            if key in self.yasl_enumerations:
                return self.yasl_enumerations[key]
        raise ValueError(
            f"Ambiguous enum name '{name}': found in multiple namespaces {matches}. Specify a namespace."
        )

    def register_unique_value(
        self,
        type_name: str,
        property_name: str,
        value: Any,
        type_namespace: str | None = None,
    ) -> None:
        if (type_name, type_namespace) not in self.unique_values_store:
            self.unique_values_store[type_name, type_namespace] = {}
        if property_name not in self.unique_values_store[type_name, type_namespace]:
            self.unique_values_store[type_name, type_namespace][property_name] = set()
        if value in self.unique_values_store[type_name, type_namespace][property_name]:
            raise ValueError(
                f"Duplicate unique value '{value}' for property '{property_name}' in type '{type_name}'"
            )
        self.unique_values_store[type_name, type_namespace][property_name].add(value)

    def unique_value_exists(
        self,
        type_name: str,
        property_name: str,
        value: Any,
        type_namespace: str | None = None,
    ) -> bool:
        if type_namespace is None:
            matches = [
                (tn, ns)
                for (tn, ns) in self.unique_values_store.keys()
                if tn == type_name
            ]
            if not matches:
                return False
            if len(matches) == 1:
                type_namespace = matches[0][1]
            else:
                raise ValueError(
                    f"Ambiguous type name '{type_name}': found in multiple namespaces. Specify a namespace."
                )

        return (
            (type_name, type_namespace) in self.unique_values_store
            and property_name in self.unique_values_store[type_name, type_namespace]
            and value
            in self.unique_values_store[type_name, type_namespace][property_name]
        )

    def clear_caches(self) -> None:
        """Clean up global stores after validation."""
        self.unique_values_store.clear()
        self.yasl_type_defs.clear()
        self.yasl_enumerations.clear()

    def export_schema(self) -> str:
        """
        Export all registered types and enums as a YASL schema string in YAML format.
        Groups definitions by namespace.
        """
        from io import StringIO
        from typing import Annotated, Union, get_args, get_origin

        from pydantic_core import PydanticUndefined
        from ruamel.yaml import YAML

        yaml = YAML()
        yaml.preserve_quotes = True

        # Structure to hold the schema
        schema: dict[str, Any] = {"definitions": {}}

        # Helper to ensure namespace structure exists
        def ensure_namespace(ns: str):
            if ns not in schema["definitions"]:
                schema["definitions"][ns] = {}

        # 1. Process Enums
        for key, enum_cls in self.yasl_enumerations.items():
            name, namespace = key
            if namespace is None:
                namespace = "default"

            ensure_namespace(namespace)

            if "enums" not in schema["definitions"][namespace]:
                schema["definitions"][namespace]["enums"] = {}

            enum_def = {"values": [e.value for e in enum_cls]}  # type: ignore
            # Add description if we can find one
            if enum_cls.__doc__ and enum_cls.__doc__ != "An enumeration.":
                enum_def["description"] = enum_cls.__doc__  # type: ignore

            schema["definitions"][namespace]["enums"][name] = enum_def

        # 2. Process Types (Pydantic Models)
        for key, model_cls in self.yasl_type_defs.items():
            name, namespace = key
            if namespace is None:
                namespace = "default"

            ensure_namespace(namespace)

            if "types" not in schema["definitions"][namespace]:
                schema["definitions"][namespace]["types"] = {}

            type_def: dict[str, Any] = {"properties": {}}

            if model_cls.__doc__:
                type_def["description"] = model_cls.__doc__

            for field_name, field in model_cls.model_fields.items():
                if field_name == "yaml_line":
                    continue

                prop_def: dict[str, Any] = {}

                # Determine YASL type from Python type annotation
                def py_type_to_yasl(t, ns=namespace):
                    # Check if Annotated is wrapped due to Pydantic internals
                    # Sometimes Pydantic might wrap things or resolve them
                    origin = get_origin(t)
                    args = get_args(t)

                    # Handle Annotated types for References
                    if origin is Annotated:
                        from yasl.primitives import ReferenceMarker

                        for arg in args:
                            if isinstance(arg, ReferenceMarker):
                                return f"ref[{arg.target}]"
                        # If no ReferenceMarker found, continue with the underlying type
                        return py_type_to_yasl(args[0], ns)

                    if t is int:
                        return "int"
                    if t is str:
                        return "str"
                    if t is bool:
                        return "bool"
                    if t is float:
                        return "float"
                    if t is dict:
                        return "map[str, str]"  # Fallback generic

                    if origin is list:
                        return f"{py_type_to_yasl(args[0], ns)}[]"

                    if origin is dict:
                        return f"map[{py_type_to_yasl(args[0], ns)}, {py_type_to_yasl(args[1], ns)}]"

                    if origin is Union:
                        # Handle Optional[T] which is Union[T, NoneType]
                        non_none = [a for a in args if a is not type(None)]
                        if len(non_none) == 1:
                            return py_type_to_yasl(non_none[0], ns)

                    if isinstance(t, type):
                        # It might be a registered Enum or Model
                        # We need to find its registered name and namespace

                        # Check enums
                        for (ename, ens), ecls in self.yasl_enumerations.items():
                            if ecls is t:
                                if ens == ns:
                                    return ename
                                return f"{ens}.{ename}" if ens else ename

                        # Check types
                        for (tname, tns), tcls in self.yasl_type_defs.items():
                            if tcls is t:
                                if tns == ns:
                                    return tname
                                return f"{tns}.{tname}" if tns else tname

                        # Fallback to name if not found in registry (e.g. primitive wrapped)
                        if issubclass(t, Enum):
                            return t.__name__
                        if issubclass(t, BaseModel):
                            return t.__name__

                    return str(t)

                # Check for metadata first (Pydantic v2 moves Annotated args to metadata for top-level fields)
                yasl_type = None
                from yasl.primitives import ReferenceMarker

                if field.metadata:
                    for meta in field.metadata:
                        if isinstance(meta, ReferenceMarker):
                            yasl_type = f"ref[{meta.target}]"
                            break

                if yasl_type is None:
                    yasl_type = py_type_to_yasl(field.annotation)

                prop_def["type"] = yasl_type

                # Description
                if field.description:
                    prop_def["description"] = field.description

                # Presence
                if field.is_required():
                    prop_def["presence"] = "required"
                else:
                    prop_def["presence"] = "optional"
                    # Add default if it exists and is not None/PydanticUndefined
                    if (
                        field.default is not None
                        and field.default is not Ellipsis
                        and field.default is not PydanticUndefined
                    ):
                        # We need to be careful with Enum defaults, we want the value
                        if isinstance(field.default, Enum):
                            prop_def["default"] = field.default.value
                        else:
                            prop_def["default"] = field.default

                type_def["properties"][field_name] = prop_def

            schema["definitions"][namespace]["types"][name] = type_def

        stream = StringIO()
        yaml.dump(schema, stream)
        return stream.getvalue()


# Singleton instance
yasl_registry = YaslRegistry()


def get_yasl_registry() -> YaslRegistry:
    """Get the singleton YaslRegistry instance."""
    return yasl_registry
