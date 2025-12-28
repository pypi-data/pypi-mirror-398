"""A custom build hook that handles versioning AND Cython compilation."""

from __future__ import annotations

from collections.abc import Callable  # noqa: TC003
import os
from pathlib import Path
import shutil
import sys
from typing import TYPE_CHECKING, Any, NamedTuple, Self

from dunamai import Version  # pyright: ignore[reportMissingImports]
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from jinja2 import Template
from uv_dynamic_versioning import schemas  # pyright: ignore[reportMissingImports] # noqa: TC002
from uv_dynamic_versioning.base import BasePlugin  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from setuptools import Extension  # pyright: ignore[reportMissingModuleSource]


class Context(NamedTuple):
    version: str
    commit: str
    major: int
    minor: int
    patch: int

    @classmethod
    def from_string(cls, version_str: str) -> tuple[int, int, int]:  # noqa: D102
        def part_check[T](n: int, data: tuple, expected_type: Callable[[str], T] = int) -> tuple[T, ...]:
            if len(data) != n:
                raise ValueError(f"Version string must have {n} parts: {data!r}")
            values = []
            for i, part in enumerate(data):
                try:
                    values.append(expected_type(part))
                except ValueError as e:
                    raise TypeError(f"Part {i} must be of type {expected_type.__name__}: {part}") from e
            return tuple(values)

        try:
            if "-" in version_str:
                version_str = version_str.split("-")[0]
            if "+" in version_str:
                version_str = version_str.split("+")[0]
            major, minor, patch = part_check(n=3, data=tuple(version_str.split(".")))
            return int(major), int(minor), int(patch)
        except ValueError as e:
            raise ValueError(
                f"Invalid version string format: {version_str}. Expected integers for major, minor, and patch."
            ) from e

    @classmethod
    def from_version(cls, version) -> Self:  # noqa: ANN001, D102
        ver: tuple[int, int, int] = cls.from_string(version.base)
        return cls(version=version.base, commit=version.commit or "", major=ver[0], minor=ver[1], patch=ver[2])


def _get_version(config: schemas.UvDynamicVersioning) -> dict[str, int | str]:
    try:
        value: Version = Version.from_vcs(
            config.vcs,
            latest_tag=config.latest_tag,
            strict=config.strict,
            tag_branch=config.tag_branch,
            tag_dir=config.tag_dir,
            full_commit=config.full_commit,
            ignore_untracked=config.ignore_untracked,
            pattern=config.pattern,
            pattern_prefix=config.pattern_prefix,
            commit_length=config.commit_length,
        )
        return Context.from_version(value)._asdict()
    except RuntimeError:
        if config.fallback_version:
            return Context.from_version(Version(config.fallback_version))._asdict()
        raise


def err_print(*msg: Any, **kwargs: Any) -> None:
    print(*msg, file=sys.stderr, **kwargs)


def find_package_root(name: str) -> Path:
    """Find package root - handles both src layout and flat layout (from sdist)."""
    if Path(f"src/{name}").exists():
        return Path("src")
    if Path(name).exists():
        return Path(".")
    raise FileNotFoundError("Cannot find package directory")


NOT_FOUND = object()


class CythonArgs(NamedTuple):
    include_dirs: list[str]
    library_dirs: list[str]
    libraries: list[str]
    extra_compile_args: list[str]
    extra_link_args: list[str]


class CustomBuildHook(BasePlugin, BuildHookInterface):
    PLUGIN_NAME = "custom"

    def _output_version(self, version: dict[str, int | str], output_path: Path) -> None:
        template_str: str = self._get_value("template")
        template = Template(template_str)
        rendered_content: str = template.render(**version)
        output_path.write_text(rendered_content)

    def _get_value[T](self, key: str, default: Any = NOT_FOUND) -> T:  # pyright: ignore[reportInvalidTypeVarUse]
        value: T | None = self.config.get(key, NOT_FOUND)
        if value is NOT_FOUND:
            value = default
        return value  # pyright: ignore[reportReturnType]

    def get_compile_args(self) -> tuple[list[str], list[str]]:
        """Get platform-specific compile and link arguments."""
        compile_args = "extra_compile_args_windows" if sys.platform == "win32" else "extra_compile_args"
        link_args = "extra_link_args_windows" if sys.platform == "win32" else "extra_link_args"
        return (self._get_value(compile_args, default=[]), self._get_value(link_args, default=[]))

    def _get_extensions(self, pyx_files: list[Path], pkg_root: Path, name: str) -> list[Extension]:
        from setuptools import Extension  # pyright: ignore[reportMissingModuleSource]  # noqa: PLC0415

        extensions: list[Extension] = []
        base_include_dirs: list[str] = [str(pkg_root), str(pkg_root / name)]
        extra_include_dirs: list[str] = self._get_value("include_dirs", default=[])
        library_dirs: list[str] = self._get_value("library_dirs", default=[])
        libraries: list[str] = self._get_value("libraries", default=[])
        extra_compile_args, extra_link_args = self.get_compile_args()

        for pyx_file in pyx_files:
            parts: tuple[str, ...] = pyx_file.with_suffix("").parts
            if parts[0] == "src":
                parts = parts[1:]
            extensions.append(
                Extension(
                    ".".join(parts),
                    include_dirs=[*base_include_dirs, *extra_include_dirs],
                    library_dirs=library_dirs,
                    libraries=libraries,
                    sources=[str(pyx_file)],
                    extra_compile_args=extra_compile_args,
                    extra_link_args=extra_link_args,
                ),
            )
        return extensions

    def _get_files(self, pkg_root: Path, ext: str) -> list[Path]:
        pyx_files: list[Path] = []
        for dirpath, _, filenames in os.walk(str(pkg_root)):
            for filename in filenames:
                if filename.endswith(ext):
                    pyx_files.append(Path(dirpath) / filename)
        return pyx_files

    def _compile_cython(self, build_data: dict[str, Any], name: str) -> None:
        """Compile all .pyx files found in the source directory."""
        pkg_root: Path = find_package_root(name)
        pyx_files: list[Path] = self._get_files(pkg_root, ext=".pyx")

        if not pyx_files:
            err_print("No .pyx files found to compile.")
            return

        err_print(f"Compiling {len(pyx_files)} Cython file(s)...")
        from Cython.Build import cythonize  # noqa: PLC0415
        from setuptools import Distribution  # pyright: ignore[reportMissingModuleSource]  # noqa: PLC0415
        from setuptools.command.build_ext import build_ext  # pyright: ignore[reportMissingModuleSource] # noqa: PLC0415

        ext_modules: Any = cythonize(
            module_list=self._get_extensions(pyx_files, pkg_root, name),
            annotate=self._get_value("annotate", default=False),
            compiler_directives=self._get_value("compiler_directives", default={}),
        )

        dist = Distribution({"ext_modules": ext_modules})
        cmd = build_ext(dist)
        cmd.ensure_finalized()
        cmd.run()

        build_lib = Path(cmd.build_lib)

        lib_files: list[str] = self._get_value("lib_files", default=[])
        files: list[Path] = []
        if lib_files:
            for pattern in lib_files:
                files.extend(self._get_files(build_lib, ext=pattern))

        for file in files:
            relative: Path = file.relative_to(build_lib)
            dest: Path = pkg_root / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, dest)
            err_print(f"    Copied: {file} -> {dest}")

            artifact_path = str(dest)
            if "artifacts" not in build_data:
                build_data["artifacts"] = []
            build_data["artifacts"].append(artifact_path)
            err_print(f"    Registered artifact: {artifact_path}")

        err_print("✓ Cython compilation successful")
        build_data["pure_python"] = False
        build_data["infer_tag"] = True

    def initialize(self, version: Any, build_data: dict[str, Any]) -> None:
        """Initialize the build hook."""
        output_path: Path = Path(self._get_value("output"))
        name: str = self._get_value("name")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        version = _get_version(self.project_config)
        self._output_version(version, output_path)
        self._compile_cython(build_data, name)
