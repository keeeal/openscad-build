from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from shutil import copyfile, copytree
from sys import modules
from tempfile import TemporaryDirectory
from types import ModuleType

from pytest import fixture


@fixture
def src_dir() -> Path:
    return Path("/src")


@fixture
def tests_dir() -> Path:
    return Path("/tests")


@fixture
def assets_dir(tests_dir: Path) -> Path:
    return tests_dir / "assets"


@fixture
def tmp_dir() -> Path:
    with TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@fixture
def render_config(tmp_dir: Path, assets_dir: Path) -> Path:
    return copyfile(assets_dir / "render.yaml", tmp_dir / "render.yaml")


@fixture
def root_dir(tmp_dir: Path, assets_dir: Path) -> Path:
    return copytree(assets_dir / "root", tmp_dir / "root")


@fixture
def src_module(src_dir: Path) -> ModuleType:
    module_name = "src"
    spec = spec_from_file_location(module_name, src_dir / "openscad-build.py")
    src = module_from_spec(spec)
    modules[module_name] = src
    spec.loader.exec_module(src)

    return src
