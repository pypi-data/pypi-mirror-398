"""Dynaconf validator helpers for SoCX configuration."""

from itertools import chain
from typing import ClassVar
from pathlib import Path
from collections.abc import Iterable

from dynaconf import LazySettings
from dynaconf.validator import empty


__all__ = (
    "Validator",
    "PathValidator",
    "ValidationError",
)


from dynaconf.validator import Validator as Validator
from dynaconf.validator import ValidationError as ValidationError


class PathValidator:
    """Validate include/exclude path configuration for converters."""

    src: ClassVar[Path]
    target: ClassVar[Path]

    @classmethod
    def source_validator(cls, src: str | Path) -> bool:
        """Validate that ``src`` points to an existing directory."""
        if not isinstance(src, Path):
            src = Path(src)
        return src.exists() and src.is_dir()

    @classmethod
    def target_validator(cls, target: str | Path) -> bool:
        """Ensure target either does not exist or resolves to a directory."""
        if not isinstance(target, Path):
            target = Path(target)
        return target.is_dir() or not target.exists()

    @classmethod
    def includes_validator(
        cls, src: Path, includes: Iterable[str], excludes: Iterable[str]
    ) -> bool:
        """Validate include patterns resolve to files once exclusions apply."""
        if not includes:
            return False
        if not isinstance(src, Path):
            src = Path(src)
        if not isinstance(includes, list | set | tuple):
            return False
        paths = cls._extract_includes(src, includes, excludes)
        return bool(paths) and all(path.is_file() for path in paths)

    @classmethod
    def _extract_includes(
        cls, src: Path, includes: Iterable[str], excludes: Iterable[str]
    ) -> set[Path]:
        """Resolve include/exclude patterns into a set of concrete paths."""
        paths: set[Path] = set()
        globpaths: set[Path] = set()

        if not isinstance(src, Path):
            src = Path(src)

        for include in includes:
            if "*" not in include:
                paths.add(Path(src / include))
            else:
                globpaths = globpaths.union(set(src.glob(str(include))))

        for exclude in excludes:
            if "*" not in exclude:
                paths.discard(Path(src / exclude))
            else:
                globpaths.difference_update(set(src.glob(str(exclude))))

        return paths.union(globpaths)


def _convert_validators(settings: LazySettings) -> Iterable[Validator]:
    """Build validators related to converter configuration blocks."""

    def _source_validator(lang: str) -> Validator:
        yield Validator(
            f"convert.{lang}.source",
            condition=PathValidator.source_validator,
            must_exist=True,
            ne=empty,
        )

    def _target_validator(lang: str) -> Validator:
        yield Validator(
            f"convert.{lang}.target",
            condition=PathValidator.target_validator,
            must_exist=True,
            ne=empty,
        )

    def _source_validators(settings: LazySettings) -> Iterable[Validator]:
        yield from (_source_validator(lang) for lang in settings.convert)

    def _target_validators(settings: LazySettings) -> Iterable[Validator]:
        yield from (_target_validator(lang) for lang in settings.convert)

    yield from chain(_source_validator(settings), _target_validator(settings))


def get_validators(settings: LazySettings):
    """Yield all validators expected for the provided ``settings``."""
    yield from _convert_validators(settings)


def validate_all(settings: LazySettings, register: bool = False) -> None:
    """Run validation against all registered validators."""
    if register:
        settings.validators.register(get_validators(settings))

    settings.validators.validate_all()
