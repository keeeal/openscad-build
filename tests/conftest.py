from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from shutil import copyfile, copytree
from sys import modules
from types import ModuleType

from pytest import fixture


@fixture
def src_path() -> Path:
    return Path("/src")


@fixture
def tests_path() -> Path:
    return Path("/tests")


@fixture
def assets_path(tests_path: Path) -> Path:
    return tests_path / "assets"


@fixture
def render_config(tmp_path: Path, assets_path: Path) -> Path:
    return copyfile(assets_path / "render.yaml", tmp_path / "render.yaml")


@fixture
def root_path(tmp_path: Path, assets_path: Path) -> Path:
    return copytree(assets_path / "root", tmp_path / "root")


@fixture
def openscad_build_module(src_path: Path) -> ModuleType:
    module_name = "openscad-build"
    module_location = src_path / "openscad-build.py"
    module_spec = spec_from_file_location(module_name, module_location)

    if module_spec is None:
        raise ValueError(f"Module location not found: '{module_location}'")

    module = module_from_spec(module_spec)
    modules[module_name] = module

    if module_spec.loader is None:
        raise ValueError(f"Error loading module at: '{module_location}'")

    module_spec.loader.exec_module(module)

    return module
