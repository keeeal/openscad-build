from pathlib import Path
from types import ModuleType
from typing import Callable

from openscad_logs import read_log_file


def test_variable_name(openscad_build_module: ModuleType):
    variable_name: Callable = openscad_build_module.variable_name

    assert variable_name("foo-bar") == "foo_bar"


def test_get_modules(openscad_build_module: ModuleType, root_path: Path):
    get_modules: Callable = openscad_build_module.get_modules
    sub_path = root_path / "sub-dir"

    assert get_modules(sub_path) == {
        sub_path / "__subassembly__.scad": "sub_dir",
        sub_path / "baz.scad": "baz",
    }
    assert get_modules(root_path) == {
        root_path / "__subassembly__.scad": "root",
        root_path / "foo-bar.scad": "foo_bar",
        root_path / "sub-dir" / "__subassembly__.scad": "sub_dir",
        root_path / "sub-dir" / "baz.scad": "baz",
    }


def test_get_modules__no_scad_files(openscad_build_module: ModuleType, tmp_path: Path):
    get_modules: Callable = openscad_build_module.get_modules

    assert len(list(tmp_path.iterdir())) == 0
    assert len(get_modules(tmp_path)) == 0

    with open(tmp_path / "not-an-scad-file.txt", "w+") as f:
        f.write("Hello world!")

    assert len(list(tmp_path.iterdir())) == 1
    assert len(get_modules(tmp_path)) == 0


def test_get_modules__ignore_openscad_file(
    openscad_build_module: ModuleType, root_path: Path
):
    get_modules: Callable = openscad_build_module.get_modules

    with open(root_path / "foo-bar.scad", "w+") as f:
        f.write("module incorrect_name() sphere();")

    assert get_modules(root_path) == {
        root_path / "__subassembly__.scad": "root",
        root_path / "sub-dir" / "__subassembly__.scad": "sub_dir",
        root_path / "sub-dir" / "baz.scad": "baz",
    }


def test_get_modules__ignore_subassembly_file(
    openscad_build_module: ModuleType, root_path: Path
):
    get_modules: Callable = openscad_build_module.get_modules

    with open(root_path / "__subassembly__.scad", "w+") as f:
        f.write("module incorrect_name() sphere();")

    assert get_modules(root_path) == {
        root_path / "foo-bar.scad": "foo_bar",
        root_path / "sub-dir" / "__subassembly__.scad": "sub_dir",
        root_path / "sub-dir" / "baz.scad": "baz",
    }


def test_write_main(openscad_build_module: ModuleType, root_path: Path):
    write_main: Callable = openscad_build_module.write_main
    main_file = root_path.parent / "main.scad"

    assert not main_file.exists()
    write_main(root_path)
    assert main_file.exists()

    with open(main_file) as f:
        lines = list(filter(None, map(str.strip, f.readlines())))

    assert sum(line.startswith("$fn = ") for line in lines) == 1
    assert sum(line.startswith("part = ") for line in lines) == 1

    for scad_file in (
        "root/__subassembly__.scad",
        "root/foo-bar.scad",
        "root/sub-dir/__subassembly__.scad",
        "root/sub-dir/baz.scad",
    ):
        assert f"use <{scad_file}>" in lines

    for part_name, variable_name in (
        ("root", "root"),
        ("├─ foo-bar", "foo_bar"),
        ("├─ sub-dir", "sub_dir"),
        ("│  ├─ baz", "baz"),
    ):
        assert f'if (part == "{part_name}") {variable_name}();' in lines


def test_write_main__flatten(openscad_build_module: ModuleType, root_path: Path):
    write_main: Callable = openscad_build_module.write_main
    main_file = root_path.parent / "main.scad"

    assert not main_file.exists()
    write_main(root_path, flatten=True)
    assert main_file.exists()

    with open(main_file) as f:
        lines = list(filter(None, map(str.strip, f.readlines())))

    assert sum(line.startswith("$fn = ") for line in lines) == 1
    assert sum(line.startswith("part = ") for line in lines) == 1

    for scad_file in (
        "root/__subassembly__.scad",
        "root/foo-bar.scad",
        "root/sub-dir/__subassembly__.scad",
        "root/sub-dir/baz.scad",
    ):
        assert f"use <{scad_file}>" in lines

    for part_name, variable_name in (
        ("root", "root"),
        ("foo-bar", "foo_bar"),
        ("sub-dir", "sub_dir"),
        ("baz", "baz"),
    ):
        assert f'if (part == "{part_name}") {variable_name}();' in lines


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
