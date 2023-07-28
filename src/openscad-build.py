#!/usr/local/bin/python

from collections import Counter
from pathlib import Path
from string import ascii_letters, digits
from subprocess import STDOUT, check_output
from tempfile import NamedTemporaryFile
from typing import Optional, Union

from fire import Fire  # type: ignore[import]
from pydantic import BaseModel, Field
from yaml import safe_load

SUBASSEMBLY_STEM = "__subassembly__"


class PartConfig(BaseModel):
    render_quality: int = Field(alias="render-quality", default=32)
    log: bool = False


class RenderConfig(BaseModel):
    root_dir: Path = Field(alias="root-dir")
    parts: dict[str, PartConfig]


def is_subassembly(file: Path) -> bool:
    return file.stem.lower() == SUBASSEMBLY_STEM.lower()


def variable_name(name: str) -> str:
    if len(name) == 1:
        return name if name in ascii_letters + digits + "_" else "_"

    return "".join(map(variable_name, name))


def get_modules(root_dir: Path, sort: bool = True) -> dict[str, Path]:
    modules = dict()
    names = list()

    for file in root_dir.rglob("*.scad"):
        with open(file) as f:
            lines = f.readlines()

        module = file.parent.stem if is_subassembly(file) else file.stem
        name = variable_name(module)

        if not any(line.startswith(f"module {name}(") for line in lines):
            raise ValueError(f"Expected module '{name}' in '{file}'")

        modules[module] = file.absolute()
        names.append(name)

    if len(modules) == 0:
        raise ValueError(f"No OpenSCAD files found in '{root_dir}'")

    if len(counts := Counter(names)) != len(names):
        raise ValueError(
            f"Duplicate modules found: {', '.join(name for name, count in counts.items() if count > 1)}"
        )

    return dict(sorted(modules.items())) if sort else modules


def get_main_lines(
    modules: dict[str, Path],
    default_part: Optional[str] = None,
) -> list[str]:
    default_part = default_part or next(iter(modules))

    return [
        "$fn = 32;  // [16:128]\n",
        "\n",
        *(f"use <{file}>\n" for file in modules.values()),
        "\n",
        f"part = '{default_part}';  // {list(modules)}\n".replace("'", '"'),
        "\n",
        *(
            f'if (part == "{module}") {variable_name(module)}();\n'
            for module in modules
        ),
    ]


def write_main(
    root_dir: Union[Path, str],
    output_file: Optional[Union[Path, str]] = None,
    sort_modules: bool = True,
) -> None:
    root_dir = Path(root_dir)
    output_file = output_file or root_dir.parent / "main.scad"
    output_file = Path(output_file)

    modules = get_modules(root_dir, sort=sort_modules)
    lines = get_main_lines(modules)

    with open(output_file, "w+") as f:
        f.writelines(lines)


def render(
    render_config_path: Union[Path, str],
    output_dir: Optional[Union[Path, str]] = None,
    render_quality: Optional[int] = None,
    log: Optional[bool] = None,
) -> None:
    render_config_path = Path(render_config_path)
    output_dir = output_dir or render_config_path.parent
    output_dir = Path(output_dir)

    try:
        with open(render_config_path) as f:
            render_config = RenderConfig(**safe_load(f))
    except TypeError:
        raise ValueError(f"Error reading {render_config_path}")

    tmp_main = NamedTemporaryFile().name

    write_main(
        render_config_path.parent / render_config.root_dir,
        output_file=tmp_main,
    )

    for part, part_config in render_config.parts.items():
        output = check_output(
            [
                "openscad",
                *("-o", str(output_dir / f"{part}.stl")),
                *("-D", f"$fn={render_quality or part_config.render_quality}"),
                *("-D", f'part="{part}"'),
                tmp_main,
            ],
            stderr=STDOUT,
        )

        if log if log is not None else part_config.log:
            with open(output_dir / f"{part}.log", "wb+") as f:
                f.write(output)


if __name__ == "__main__":
    try:
        Fire(
            {
                "write-main": write_main,
                "render": render,
            }
        )
    except Exception as error:
        print(f"{Path(__file__).stem}: {error}")
        exit(1)
