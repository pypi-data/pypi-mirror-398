from __future__ import annotations

import builtins
from os import getenv
from typing import TYPE_CHECKING, cast, final, overload

if TYPE_CHECKING:
    from enum import Enum
    from typing import Callable, Literal, LiteralString


def _get[T](
    name: str, required: bool, default: T, converter: Callable[[str], T]
) -> T | None:
    """Internal helper to fetch and convert environment variables."""

    raw = getenv(name)
    if raw is None:
        if required:
            raise KeyError(f"Environment variable {name!r} is required but not set")
        return default

    return converter(raw)


@final
class Env:
    """A utility class for reading and validating environment variables."""

    @overload
    @staticmethod
    def str(
        name: str,
        *,
        required: Literal[False],
        default: str,
        strip: bool = False,
        allow_empty: bool = True,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> str: ...

    @overload
    @staticmethod
    def str(
        name: str,
        *,
        required: Literal[False],
        default: None = None,
        strip: bool = False,
        allow_empty: bool = True,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> str | None: ...

    @overload
    @staticmethod
    def str(
        name: str,
        *,
        required: Literal[True] = True,
        default: None = None,
        strip: bool = False,
        allow_empty: bool = True,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> str: ...

    @staticmethod
    def str(
        name: str,
        *,
        required: bool = True,
        default: str | None = None,
        strip: bool = False,
        allow_empty: bool = True,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> str | None:
        """
        Retrieve an environment variable as a string with optional validation.
        """

        if (
            min_length is not None
            and max_length is not None
            and min_length > max_length
        ):
            raise ValueError("min_length cannot be greater than max_length")

        if not allow_empty and (min_length is not None and min_length == 0):
            raise ValueError("allow_empty cannot be False when min_length is 0")
        if not allow_empty and (max_length is not None and max_length == 0):
            raise ValueError("allow_empty cannot be False when max_length is 0")

        def converter(value: str) -> str:
            if strip:
                value = value.strip()

            if not allow_empty and value == "":
                raise ValueError(f"{name!r} cannot be empty")

            if min_length is not None and len(value) < min_length:
                raise ValueError(f"{name!r} must be at least {min_length} chars")
            if max_length is not None and len(value) > max_length:
                raise ValueError(f"{name!r} must be at most {max_length} chars")
            return value

        return _get(name, required, default, converter)

    @overload
    @staticmethod
    def int(
        name: builtins.str,
        *,
        required: Literal[False],
        default: int,
        min_value: int | None = None,
        max_value: int | None = None,
    ) -> int: ...

    @overload
    @staticmethod
    def int(
        name: builtins.str,
        *,
        required: Literal[False],
        default: None = None,
        min_value: int | None = None,
        max_value: int | None = None,
    ) -> int | None: ...

    @overload
    @staticmethod
    def int(
        name: builtins.str,
        *,
        required: Literal[True] = True,
        default: None = None,
        min_value: int | None = None,
        max_value: int | None = None,
    ) -> int: ...

    @staticmethod
    def int(
        name: builtins.str,
        *,
        required: bool = True,
        default: int | None = None,
        min_value: int | None = None,
        max_value: int | None = None,
    ) -> int | None:
        """
        Retrieve an environment variable as an integer with optional range validation.
        """

        if min_value is not None and max_value is not None and min_value > max_value:
            raise ValueError("min_value cannot be greater than max_value")

        def converter(raw: str) -> int:
            try:
                value = int(raw.strip())
            except ValueError as e:
                raise ValueError(f"{name!r} must be an integer") from e

            if min_value is not None and value < min_value:
                raise ValueError(f"{name!r} must be >= {min_value}")
            if max_value is not None and value > max_value:
                raise ValueError(f"{name!r} must be <= {max_value}")
            return value

        return _get(name, required, default, converter)

    @overload
    @staticmethod
    def float(
        name: builtins.str,
        *,
        required: Literal[False],
        default: float,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> float: ...

    @overload
    @staticmethod
    def float(
        name: builtins.str,
        *,
        required: Literal[False],
        default: None = None,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> float | None: ...

    @overload
    @staticmethod
    def float(
        name: builtins.str,
        *,
        required: Literal[True] = True,
        default: None = None,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> float: ...

    @staticmethod
    def float(
        name: builtins.str,
        *,
        required: bool = True,
        default: float | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> float | None:
        """
        Retrieve an environment variable as a float with optional range validation.
        """

        if min_value is not None and max_value is not None and min_value > max_value:
            raise ValueError("min_value cannot be greater than max_value")

        def converter(raw: str) -> float:
            import math

            try:
                value = float(raw.strip())
            except ValueError as e:
                raise ValueError(f"{name!r} must be a float") from e

            if not math.isfinite(value):
                raise ValueError(f"{name!r} must be a finite float")

            if min_value is not None and value < min_value:
                raise ValueError(f"{name!r} must be >= {min_value}")
            if max_value is not None and value > max_value:
                raise ValueError(f"{name!r} must be <= {max_value}")
            return value

        return _get(name, required, default, converter)

    @overload
    @staticmethod
    def bool(
        name: builtins.str,
        *,
        required: Literal[False],
        default: bool,
    ) -> bool: ...

    @overload
    @staticmethod
    def bool(
        name: builtins.str,
        *,
        required: Literal[False],
        default: None = None,
    ) -> bool | None: ...

    @overload
    @staticmethod
    def bool(
        name: builtins.str,
        *,
        required: Literal[True] = True,
        default: None = None,
    ) -> bool: ...

    @staticmethod
    def bool(
        name: builtins.str,
        *,
        required: bool = True,
        default: bool | None = None,
    ) -> bool | None:
        """
        Retrieve an environment variable as a boolean.

        Accepts 'true', '1', 'yes', 'on' as True, and 'false', '0', 'no', 'off'
        as False (case-insensitive).
        """

        def converter(raw: str) -> bool:
            match raw.strip().lower():
                case "true" | "1" | "yes" | "on":
                    return True
                case "false" | "0" | "no" | "off":
                    return False
                case _:
                    raise ValueError(f"{name!r} must be a boolean")

        return _get(name, required, default, converter)

    @overload
    @staticmethod
    def enum[E: Enum](
        name: builtins.str,
        enum: type[E],
        *,
        required: Literal[False],
        default: E,
        case_sensitive: builtins.bool = True,
    ) -> E: ...

    @overload
    @staticmethod
    def enum[E: Enum](
        name: builtins.str,
        enum: type[E],
        *,
        required: Literal[False],
        default: None = None,
        case_sensitive: builtins.bool = True,
    ) -> E | None: ...

    @overload
    @staticmethod
    def enum[E: Enum](
        name: builtins.str,
        enum: type[E],
        *,
        required: Literal[True] = True,
        default: None = None,
        case_sensitive: builtins.bool = True,
    ) -> E: ...

    @staticmethod
    def enum[E: Enum](
        name: builtins.str,
        enum: type[E],
        *,
        required: builtins.bool = True,
        default: E | None = None,
        case_sensitive: builtins.bool = True,
    ) -> E | None:
        """
        Retrieve an environment variable and convert it to an Enum member by name.
        """

        def converter(key: str) -> E:
            key = key.strip()
            if not case_sensitive:
                insensitive_keys = {k.casefold(): k for k in enum.__members__}
                if len(insensitive_keys) < len(enum):
                    raise ValueError(
                        "Enum contains conflicting keys when case-insensitivity is applied"
                    )

                try:
                    key = insensitive_keys[key.casefold()]
                except KeyError:
                    valid = list(enum.__members__.keys())
                    raise ValueError(f"{name!r} must be one of {valid!r}")

            try:
                return enum[key]
            except KeyError:
                valid = list(enum.__members__.keys())
                raise ValueError(f"{name!r} must be one of {valid!r}")

        return _get(name, required, default, converter)

    @overload
    @staticmethod
    def literal[L: LiteralString](
        name: builtins.str,
        choices: tuple[L, ...],
        *,
        required: Literal[False],
        default: L,
        strip: builtins.bool = True,
    ) -> L: ...

    @overload
    @staticmethod
    def literal[L: LiteralString](
        name: builtins.str,
        choices: tuple[L, ...],
        *,
        required: Literal[False],
        default: None = None,
        strip: builtins.bool = True,
    ) -> L | None: ...

    @overload
    @staticmethod
    def literal[L: LiteralString](
        name: builtins.str,
        choices: tuple[L, ...],
        *,
        required: Literal[True] = True,
        default: None = None,
        strip: builtins.bool = True,
    ) -> L: ...

    @staticmethod
    def literal[L: LiteralString](
        name: builtins.str,
        choices: tuple[L, ...],
        *,
        required: builtins.bool = True,
        default: L | None = None,
        strip: builtins.bool = True,
    ) -> L | None:
        """
        Retrieve an environment variable and ensure it matches one of the provided
        literal choices.
        """

        def converter(value: str) -> L:
            if strip:
                value = value.strip()
            if value not in choices:
                raise ValueError(f"{name!r} must be one of {choices!r}")
            return cast(L, value)

        return _get(name, required, default, converter)
