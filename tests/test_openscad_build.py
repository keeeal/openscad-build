from pathlib import Path
from types import ModuleType
from typing import Callable

from pytest import raises


def test_variable_name(src_module: ModuleType):
    variable_name: Callable = src_module.variable_name

    assert variable_name("foo-bar") == "foo_bar"


def test_get_modules(src_module: ModuleType, root_dir: Path):
    get_modules: Callable = src_module.get_modules
    sub_dir = root_dir / "sub-dir"

    assert list(get_modules(sub_dir, sort=True)) == ["baz", "sub-dir"]
    assert list(get_modules(root_dir, sort=True)) == [
        "baz",
        "foo-bar",
        "root",
        "sub-dir",
    ]


def test_get_modules__no_scad_files(src_module: ModuleType, tmp_dir: Path):
    get_modules: Callable = src_module.get_modules

    assert len(list(tmp_dir.iterdir())) == 0

    with raises(ValueError) as error:
        get_modules(tmp_dir)
    assert error.match("No OpenSCAD files found")

    with open(tmp_dir / "not-an-scad-file.txt", "w+") as f:
        f.write("Hello world!")

    assert len(list(tmp_dir.iterdir())) == 1

    with raises(ValueError) as error:
        get_modules(tmp_dir)
    assert error.match("No OpenSCAD files found")


def test_get_modules__incorrect_module_name(src_module: ModuleType, root_dir: Path):
    get_modules: Callable = src_module.get_modules

    with open(root_dir / "foo-bar.scad", "w+") as f:
        f.write("module incorrect_name() sphere();")

    with raises(ValueError) as error:
        get_modules(root_dir)
    assert error.match("Expected module")


def test_get_modules__incorrect_subassembly_name(
    src_module: ModuleType, root_dir: Path
):
    get_modules: Callable = src_module.get_modules

    with open(root_dir / "__subassembly__.scad", "w+") as f:
        f.write("module incorrect_name() sphere();")

    with raises(ValueError) as error:
        get_modules(root_dir)
    assert error.match("Expected module")


def test_get_modules__duplicate_modules(src_module: ModuleType, root_dir: Path):
    get_modules: Callable = src_module.get_modules
    sub_dir = root_dir / "sub-dir"

    with open(sub_dir / "foo-bar.scad", "w+") as f:
        f.write("module foo_bar() sphere();")

    with raises(ValueError) as error:
        get_modules(root_dir)
    assert error.match("Duplicate modules found")


def test_write_main(src_module: ModuleType, root_dir: Path):
    write_main: Callable = src_module.write_main
    main_file = root_dir.parent / "main.scad"

    assert not main_file.exists()
    write_main(root_dir)
    assert main_file.exists()

    with open(main_file) as f:
        main_lines = list(filter(None, map(str.strip, f.readlines())))

    assert sum(line.startswith("$fn = ") for line in main_lines) == 1
    assert sum(line.startswith("part = ") for line in main_lines) == 1

    for scad_file in (
        "__subassembly__.scad",
        "foo-bar.scad",
        "sub-dir/__subassembly__.scad",
        "sub-dir/baz.scad",
    ):
        assert f"use <{root_dir / scad_file}>" in main_lines

    for part_name, variable_name in (
        ("baz", "baz"),
        ("foo-bar", "foo_bar"),
        ("root", "root"),
        ("sub-dir", "sub_dir"),
    ):
        assert f'if (part == "{part_name}") {variable_name}();' in main_lines


def test_render(src_module: ModuleType, root_dir: Path, render_config: Path):
    render: Callable = src_module.render

    assert len(list(render_config.parent.glob("*.stl"))) == 0
    render(render_config)
    stl_stems = {file.stem for file in render_config.parent.glob("*.stl")}
    assert stl_stems == {"sub-dir", "foo-bar"}
