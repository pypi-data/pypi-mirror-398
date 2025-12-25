from abc import ABC, abstractmethod
from dataclasses import fields, MISSING
from inspect import signature
from logging import getLogger
from types import UnionType, NoneType
from typing import Callable, Type, get_origin, Union, get_args, Any, TypedDict, Literal, TypeAliasType, Iterable
from urllib.parse import parse_qs, unquote

from edri.dataclass.directive import ResponseDirective
from edri.dataclass.event import Event
from edri.dataclass.injection import Injection
from edri.utility.function import camel2snake


class BaseDirectiveHandlerDict[T](TypedDict):
    pass


class BaseHandler[T: ResponseDirective](ABC):
    _directive_handlers: dict[Type[T], BaseDirectiveHandlerDict[T]] = {}

    def __init__(self,
                 scope: dict,
                 receive: Callable,
                 send: Callable):
        super().__init__()
        self.send = send
        self.scope = scope
        self.receive = receive
        self.scope = scope
        self.logger = getLogger(__name__)

        self.parameters: dict[str, Any] = self.parse_url_parameters()

    @classmethod
    def directive_handlers(cls) -> dict[Type[ResponseDirective], BaseDirectiveHandlerDict]:
        handlers = {}
        for class_obj in reversed(cls.mro()):
            if hasattr(class_obj, "_directive_handlers"):
                # noinspection PyProtectedMember
                handlers.update(class_obj._directive_handlers)
        return handlers

    @abstractmethod
    async def response(self, status: Any, data: Any, *args, **kwargs) -> None:
        pass

    @abstractmethod
    async def response_error(self, status: Any, response: Any, *args, **kwargs) -> None:
        pass

    def check_parameters(self, event_constructor: Type[Event]) -> None:
        check_parameters = {}
        for name, annotation in ((f.name, f.type) for f in fields(event_constructor)):
            if name.startswith("_") or name == "method" or name == "response":
                continue
            try:
                value = self.parameters.pop(name)
            except KeyError:
                raise ValueError(f"Missing value for parameter {name}")
            try:
                value = self.convert_type(value, annotation)
            except TypeError:
                raise ValueError(f"Wrong type {type(value)} for {name}:{annotation}")
            except Exception:
                raise ValueError("Unknown error during type checking")
            check_parameters[name] = value
        if self.parameters:
            raise ValueError(f"Unknown parameters: {self.parameters}")
        self.parameters = check_parameters

    def create_event(self, event_constructor: Type[Event]) -> Event:
        self.insert_default_parameters(event_constructor)
        self.check_parameters(event_constructor)
        event = event_constructor(**self.parameters)
        event._timing.stamp(self.__class__.__name__, "Created")
        return event

    def convert_type(self, value: Any, annotation: type) -> Any:
        """
        Validates and converts input values to the specified annotation type,
        supporting:
          - basic types
          - Optional / Union / |
          - list / tuple / dict with type args
          - Literal
          - list-like subclasses (e.g. ListValidation[int])
          - Injection of validation classes (e.g. Injection((ListValidation[int],), {...}))
        """
        annotation = self._normalize_annotation(annotation)

        # Any
        if annotation is Any:
            return value

        # Injection (chain of validation classes)
        if isinstance(annotation, Injection):
            return self._convert_injection(value, annotation)

        # Unions / Optional
        if self._is_union(annotation):
            return self._convert_union(value, annotation)

        origin = get_origin(annotation)

        # Generics: list, tuple, dict, Literal, ListValidation[int], ...
        if origin is not None:
            return self._convert_generic(value, annotation, origin)

        # Non-generic simple types (including bare ListValidation, bool, etc.)
        return self._convert_simple(value, annotation)

    def _normalize_annotation(self, annotation: type) -> type:
        """Unwrap TypeAliasType and other simple normalizations."""
        if isinstance(annotation, TypeAliasType):
            return annotation.__value__
        return annotation

    def _is_union(self, annotation: type) -> bool:
        """Check if annotation is a Union / Optional / | type."""
        return isinstance(annotation, UnionType) or get_origin(annotation) is Union

    def _convert_injection(self, value: Any, injection: Injection) -> Any:
        """
        Run all validation classes in an Injection.

        Each `cls` in `injection.classes` is:
          - either a plain validation class (e.g. ListValidation),
          - or a GenericAlias like ListValidation[int].

        For list-like generics (e.g. ListValidation[int]) we:
          - convert each element of `value` using the inner type (int here),
          - then instantiate the validation class with filtered params.
        """
        try:
            for cls in injection.classes:
                # Determine underlying class and optional inner type
                item_type = None

                origin = get_origin(cls)
                if origin is not None:
                    args = get_args(cls)  # e.g. (int,)
                    target_cls = origin

                    # list-like validation class: ListValidation[int], MyListValidator[str], ...
                    if issubclass(origin, list) and args:
                        item_type = args[0]
                else:
                    target_cls = cls

                # Filter parameters to those that target_cls.__init__ actually accepts
                sig = signature(target_cls)
                param_names = [
                    p.name for p in sig.parameters.values()
                    if p.name != "self"
                ]
                filtered_params = {
                    k: v for k, v in injection.parameters.items()
                    if k in param_names
                }

                if origin is not None:
                    filtered_params["generics"] = args

                # If this is a list-like validator with an inner type -> convert elements first
                if item_type is not None:
                    if (not isinstance(value, Iterable)) or isinstance(value, (str, bytes)):
                        raise TypeError(
                            f"Value '{value}' is not a valid iterable for validator {cls}"
                        )

                    converted_items = [
                        self.convert_type(item, item_type) for item in value
                    ]
                    value = target_cls(converted_items, **filtered_params)
                else:
                    # Any other validation class: just feed the (possibly already converted) value
                    value = target_cls(value, **filtered_params)

            return value

        except ValueError:
            # Your original contract: map validator ValueError -> TypeError
            raise TypeError(f"Value '{value}' cannot be converted to type {injection}")

    def _convert_union(self, value: Any, annotation: type) -> Any:
        """Handle Union/Optional annotations."""
        annotations = get_args(annotation)

        # Handle Optional[...] where None is allowed
        if value is None:
            if NoneType in annotations:
                return None
            raise TypeError(f"Value '{value}' cannot be converted to type {annotation}")

        # Try each type in the Union
        last_error: Exception | None = None
        for ann in annotations:
            try:
                return self.convert_type(value, ann)
            except TypeError as e:
                last_error = e
                continue

        raise TypeError(f"Value '{value}' cannot be converted to type {annotation}") from last_error

    def _convert_generic(self, value: Any, annotation: type, origin: type) -> Any:
        """
        Handle generics like:
          - list[T] and list-like subclasses (ListValidation[T])
          - tuple[X, Y, ...]
          - dict[K, V]
          - Literal[...]
        """
        args = get_args(annotation)

        # list[T] and list-like subclasses (e.g. ListValidation[int])
        if isinstance(origin, type) and issubclass(origin, list):
            if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
                raise TypeError(f"Value '{value}' is not a valid iterable for type {annotation}")

            item_type = args[0] if args else Any
            converted_items = [self.convert_type(item, item_type) for item in value]

            if origin is list:
                return converted_items

            # Subclass of list, e.g. ListValidation[int]
            try:
                return origin(converted_items)
            except Exception as e:
                raise TypeError(
                    f"Value '{value}' cannot be converted to list-like type {annotation}"
                ) from e

        # ---- tuple[X, Y, ...] ----
        if origin is tuple:
            if not isinstance(value, tuple):
                raise TypeError(f"Value '{value}' is not a tuple for type {annotation}")
            return tuple(self.convert_type(v, a) for v, a in zip(value, args))

        # ---- dict[K, V] ----
        if origin is dict:
            if not isinstance(value, dict):
                raise TypeError(f"Value '{value}' is not a dict for type {annotation}")
            if len(args) != 2:
                raise TypeError("Key and value types for dict must be specified")
            key_type, value_type = args
            return {
                self.convert_type(k, key_type): self.convert_type(v, value_type)
                for k, v in value.items()
            }

        # ---- Literal["a", "b", ...] ----
        if origin is Literal:
            literal_values = args
            if value in literal_values:
                return value
            raise TypeError(
                f"Value '{value}' is not one of the allowed Literal values {literal_values}"
            )

        # Unknown generic
        raise TypeError(f"Value '{value}' cannot be converted to type {annotation}")

    def _convert_simple(self, value: Any, annotation: type) -> Any:
        """
        Handle non-generic types: bool, dataclasses, custom classes,
        and bare list subclasses like ListValidation.
        """
        # Already correct type
        if isinstance(value, annotation):
            return value

        # Support bare list-like subclasses (e.g. annotation is ListValidation without [T])
        try:
            is_list_subclass = isinstance(annotation, type) and issubclass(annotation, list)
        except TypeError:
            is_list_subclass = False

        if is_list_subclass and not isinstance(value, (str, bytes)) and isinstance(value, Iterable):
            try:
                return annotation(value)
            except Exception as e:
                raise TypeError(
                    f"Value '{value}' cannot be converted to list-like type {annotation}"
                ) from e

        # Special case: string "false" -> False for bool
        if isinstance(value, str) and value.lower() == "false" and annotation is bool:
            return False

        # Normal constructor-based conversion
        try:
            return annotation(value)
        except Exception:
            # Try fromisoformat if available (e.g., datetime, date)
            if hasattr(annotation, "fromisoformat"):
                try:
                    return annotation.fromisoformat(value)
                except Exception:
                    raise TypeError(
                        "Value '%s' cannot be converted from isoformat to type %s"
                        % (value, annotation)
                    )
            raise TypeError(f"Value '{value}' cannot be converted to type {annotation}")

    @abstractmethod
    def handle_directives(self, directives: list[ResponseDirective]) -> ...:
        pass

    def insert_default_parameters(self, event_constructor: Type[Event]) -> None:
        for field in fields(event_constructor):
            if field.name.startswith("_") or field.name in ("response", "method"):
                continue
            if field.name in self.parameters:
                continue
            if field.default is not MISSING:
                self.parameters[field.name] = field.default
                continue
            if field.default_factory is not MISSING:
                self.parameters[field.name] = field.default_factory()
                continue

    def parse_url_parameters(self) -> dict[str, Any]:
        url_parameters = parse_qs(unquote(self.scope["query_string"].decode()), keep_blank_values=True)
        return {
            camel2snake(key.strip("[]")): value if key.endswith("[]") else value[-1] for key, value in
            url_parameters.items()
        }