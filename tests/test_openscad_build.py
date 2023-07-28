from pathlib import Path
from types import ModuleType
from typing import Callable

from openscad_logs import read_log_file
from pytest import raises


def test_variable_name(openscad_build_module: ModuleType):
    variable_name: Callable = openscad_build_module.variable_name

    assert variable_name("foo-bar") == "foo_bar"


def test_get_modules(openscad_build_module: ModuleType, root_path: Path):
    get_modules: Callable = openscad_build_module.get_modules
    sub_path = root_path / "sub-dir"

    assert get_modules(sub_path).keys() == {"baz", "sub-dir"}
    assert get_modules(root_path).keys() == {
        "baz",
        "foo-bar",
        "root",
        "sub-dir",
    }


def test_get_modules__no_scad_files(openscad_build_module: ModuleType, tmp_path: Path):
    get_modules: Callable = openscad_build_module.get_modules

    assert len(list(tmp_path.iterdir())) == 0

    with raises(ValueError) as error:
        get_modules(tmp_path)
    assert error.match("No OpenSCAD files found")

    with open(tmp_path / "not-an-scad-file.txt", "w+") as f:
        f.write("Hello world!")

    assert len(list(tmp_path.iterdir())) == 1

    with raises(ValueError) as error:
        get_modules(tmp_path)
    assert error.match("No OpenSCAD files found")


def test_get_modules__incorrect_module_name(
    openscad_build_module: ModuleType, root_path: Path
):
    get_modules: Callable = openscad_build_module.get_modules

    with open(root_path / "foo-bar.scad", "w+") as f:
        f.write("module incorrect_name() sphere();")

    with raises(ValueError) as error:
        get_modules(root_path)
    assert error.match("Expected module")


def test_get_modules__incorrect_subassembly_name(
    openscad_build_module: ModuleType, root_path: Path
):
    get_modules: Callable = openscad_build_module.get_modules

    with open(root_path / "__subassembly__.scad", "w+") as f:
        f.write("module incorrect_name() sphere();")

    with raises(ValueError) as error:
        get_modules(root_path)
    assert error.match("Expected module")


def test_get_modules__duplicate_modules(
    openscad_build_module: ModuleType, root_path: Path
):
    get_modules: Callable = openscad_build_module.get_modules
    sub_path = root_path / "sub-dir"

    with open(sub_path / "foo-bar.scad", "w+") as f:
        f.write("module foo_bar() sphere();")

    with raises(ValueError) as error:
        get_modules(root_path)
    assert error.match("Duplicate modules found")


def test_write_main(openscad_build_module: ModuleType, root_path: Path):
    write_main: Callable = openscad_build_module.write_main
    main_file = root_path.parent / "main.scad"

    assert not main_file.exists()
    write_main(root_path)
    assert main_file.exists()

    with open(main_file) as f:
        main_lines = list(filter(None, map(str.strip, f.readlines())))

    assert sum(line.startswith("$fn = ") for line in main_lines) == 1
    assert sum(line.startswith("part = ") for line in main_lines) == 1

    for scad_file in (
        "root/__subassembly__.scad",
        "root/foo-bar.scad",
        "root/sub-dir/__subassembly__.scad",
        "root/sub-dir/baz.scad",
    ):
        assert f"use <{scad_file}>" in main_lines

    for part_name, variable_name in (
        ("baz", "baz"),
        ("foo-bar", "foo_bar"),
        ("root", "root"),
        ("sub-dir", "sub_dir"),
    ):
        assert f'if (part == "{part_name}") {variable_name}();' in main_lines


def test_render(
    openscad_build_module: ModuleType, root_path: Path, render_config: Path
):
    render: Callable = openscad_build_module.render

    assert len(list(render_config.parent.glob("*.stl"))) == 0
    render(render_config)
    stl_stems = {file.stem for file in render_config.parent.glob("*.stl")}
    assert stl_stems == {"sub-dir", "foo-bar"}


def test_render__logs(
    openscad_build_module: ModuleType, root_path: Path, render_config: Path
):
    render: Callable = openscad_build_module.render

    assert len(list(render_config.parent.glob("*.log"))) == 0
    render(render_config, log=True)
    log_stems = {file.stem for file in render_config.parent.glob("*.log")}
    assert log_stems == {"sub-dir", "foo-bar"}

    log_data = read_log_file(render_config.parent / "sub-dir.log")
    expected_data = {
        "Geometries in cache": 1,
        "Geometry cache size in bytes": 728,
        "CGAL Polyhedrons in cache": 0,
        "CGAL cache size in bytes": 0,
        "Top level object is a 3D object": "",
        "Facets": 6,
    }
    for key, value in expected_data.items():
        assert log_data[key] == value

    log_data = read_log_file(render_config.parent / "foo-bar.log")
    expected_data = {
        "Geometries in cache": 1,
        "Geometry cache size in bytes": 70808,
        "CGAL Polyhedrons in cache": 0,
        "CGAL cache size in bytes": 0,
        "Top level object is a 3D object": "",
        "Facets": 962,
    }
    for key, value in expected_data.items():
        assert log_data[key] == value
