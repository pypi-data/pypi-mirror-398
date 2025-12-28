from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from packaging._tokenizer import ParserSyntaxError
from packaging.requirements import InvalidRequirement, Requirement, _parse_requirement
from packaging.specifiers import Specifier, SpecifierSet
from tomlkit import array, dumps, loads, string
from tomlkit.items import Array, Table
from utilities.text import strip_and_dedent

from actions import __version__
from actions.logging import LOGGER

if TYPE_CHECKING:
    from collections.abc import Iterator

    from utilities.types import PathLike


_MODIFICATIONS: set[Path] = set()


def format_requirements(*paths: PathLike) -> None:
    LOGGER.info(
        strip_and_dedent("""
            Running '%s' (version %s) with settings:
             - paths = %s
        """),
        format_requirements.__name__,
        __version__,
        paths,
    )
    for path in paths:
        _format_path(path)
    if len(_MODIFICATIONS) >= 1:
        LOGGER.info(
            "Exiting due to modifications: %s",
            ", ".join(map(repr, map(str, sorted(_MODIFICATIONS)))),
        )
        sys.exit(1)


def _format_path(path: PathLike, /) -> None:
    path = Path(path)
    current = path.read_text()
    expected = _get_formatted(path)
    if current != expected:
        _ = path.write_text(expected)
        _MODIFICATIONS.add(path)


def _get_formatted(path: PathLike, /) -> str:
    path = Path(path)
    doc = loads(path.read_text())
    if isinstance(dep_grps := doc.get("dependency-groups"), Table):
        for key, value in dep_grps.items():
            if isinstance(value, Array):
                dep_grps[key] = _format_array(value)
    if isinstance(project := doc["project"], Table):
        if isinstance(deps := project["dependencies"], Array):
            project["dependencies"] = _format_array(deps)
        if isinstance(optional := project.get("optional-dependencies"), Table):
            for key, value in optional.items():
                if isinstance(value, Array):
                    optional[key] = _format_array(value)
    return dumps(doc).rstrip("\n") + "\n"


def _format_array(dependencies: Array, /) -> Array:
    new = array().multiline(multiline=True)
    new.extend(map(_format_item, dependencies))
    return new


def _format_item(item: Any, /) -> Any:
    if not isinstance(item, str):
        return item
    return string(str(_CustomRequirement(item)))


class _CustomRequirement(Requirement):
    @override
    def __init__(self, requirement_string: str) -> None:
        super().__init__(requirement_string)
        try:
            parsed = _parse_requirement(requirement_string)
        except ParserSyntaxError as e:
            raise InvalidRequirement(str(e)) from e
        self.specifier = _CustomSpecifierSet(parsed.specifier)

    @override
    def _iter_parts(self, name: str) -> Iterator[str]:
        yield name
        if self.extras:
            formatted_extras = ",".join(sorted(self.extras))
            yield f"[{formatted_extras}]"
        if self.specifier:
            yield f" {self.specifier}"
        if self.url:
            yield f"@ {self.url}"
            if self.marker:
                yield " "
        if self.marker:
            yield f"; {self.marker}"


class _CustomSpecifierSet(SpecifierSet):
    @override
    def __str__(self) -> str:
        specs = sorted(self._specs, key=self._key)
        return ", ".join(map(str, specs))

    def _key(self, spec: Specifier, /) -> int:
        return [">=", "<"].index(spec.operator)


__all__ = ["format_requirements"]
