#!/usr/local/bin/python

from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import timedelta
from os.path import relpath
from pathlib import Path
from string import ascii_letters, digits
from subprocess import STDOUT, check_output
from tempfile import NamedTemporaryFile
from time import time
from typing import Optional, Union

from fire import Fire  # type: ignore[import]
from loguru import logger
from pydantic import BaseModel, Field
from yaml import safe_load

SUBASSEMBLY_STEM = "__subassembly__"


class PartConfig(BaseModel):
    render_quality: int = Field(alias="render-quality", default=32)
    save_log: bool = False


class RenderConfig(BaseModel):
    root_dir: Path = Field(alias="root-dir")
    parts: dict[str, PartConfig]


def is_subassembly(path: Path) -> bool:
    return path.is_file() and path.stem.lower() == SUBASSEMBLY_STEM.lower()


def tree(path: Path) -> str:
    return " ".join(
        len(path.parts[:-2]) * ["│ "]
        + min(len(path.parts) - 1, 1) * ["├─"]
        + [path.stem]
    )


def variable_name(name: str) -> str:
    if len(name) == 1:
        return name if name in ascii_letters + digits + "_" else "_"

    return "".join(map(variable_name, name))


def get_modules(root_dir: Path) -> dict[Path, str]:
    modules: dict[Path, str] = dict()

    for path in sorted(root_dir.rglob("*.scad")):
        module = variable_name(path.parent.stem if is_subassembly(path) else path.stem)

        with open(path) as f:
            lines = f.readlines()

        if not any(line.startswith(f"module {module}(") for line in lines):
            continue

        modules[path] = module

    return modules


def write_main(
    root_dir: Union[Path, str],
    output_file: Optional[Union[Path, str]] = None,
    flatten: bool = False,
) -> None:
    root_dir = Path(root_dir)
    output_file = Path(output_file or root_dir.parent / "main.scad")
    modules = get_modules(root_dir)

    if len(modules) == 0:
        raise ValueError(f"No modules found in '{root_dir}'")

    if len(counts := Counter(modules.values())) != len(modules):
        raise ValueError(
            f"Duplicate modules found: {', '.join(k for k, n in counts.items() if n > 1)}"
        )

    def part_name(path: Path) -> str:
        path = path.parent if is_subassembly(path) else path
        path = path.relative_to(root_dir.parent)

        return path.stem if flatten else tree(path)

    parts = {part_name(path): module for path, module in modules.items()}

    lines = [
        "$fn = 32;  // [16:128]\n",
        "\n",
        *(f"use <{relpath(path, output_file.parent)}>\n" for path in modules),
        "\n",
        f"part = '{next(iter(parts))}';  // {list(parts)}\n".replace("'", '"'),
        "\n",
        *(f'if (part == "{part}") {module}();\n' for part, module in parts.items()),
    ]

    with open(output_file, "w+") as f:
        f.writelines(lines)


def render_part(
    output_dir: Union[Path, str],
    main_path: Union[Path, str],
    part: str,
    render_quality: int,
    save_log: bool,
):
    output_dir = Path(output_dir)

    start = time()
    output = check_output(
        [
            "openscad",
            *("-o", str(output_dir / f"{part}.stl")),
            *("-D", f"$fn={render_quality}"),
            *("-D", f'part="{part}"'),
            str(main_path),
        ],
        stderr=STDOUT,
    )

    logger.success(f"Rendered {part} in {timedelta(seconds=time() - start)}")

    if save_log:
        with open(output_dir / f"{part}.log", "wb+") as f:
            f.write(output)


def render(
    render_config_path: Union[Path, str],
    output_dir: Optional[Union[Path, str]] = None,
    render_quality: Optional[int] = None,
    save_logs: Optional[bool] = None,
) -> None:
    render_config_path = Path(render_config_path)
    output_dir = output_dir or render_config_path.parent
    output_dir = Path(output_dir)

    try:
        with open(render_config_path) as f:
            render_config = RenderConfig(**safe_load(f))
    except TypeError:
        raise ValueError(f"Error reading {render_config_path}")

    tmp_main = NamedTemporaryFile(suffix=".scad").name

    write_main(
        root_dir=render_config_path.parent / render_config.root_dir,
        output_file=tmp_main,
        flatten=True,
    )

    logger.info(f"Rendering...")

    with ProcessPoolExecutor() as pool:
        for part, part_config in render_config.parts.items():
            pool.submit(
                render_part,
                output_dir=output_dir,
                main_path=tmp_main,
                part=part,
                render_quality=render_quality or part_config.render_quality,
                save_log=save_logs if save_logs is not None else part_config.save_log,
            )


if __name__ == "__main__":
    try:
        Fire(
            {
                "write-main": write_main,
                "render": render,
            }
        )
    except Exception as error:
        logger.error(str(error))
        exit(1)
