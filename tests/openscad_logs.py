from datetime import timedelta
from pathlib import Path
from typing import Any

INT_KEYS = {
    "CGAL cache size in bytes",
    "CGAL Polyhedrons in cache",
    "Edges",
    "Facets",
    "Geometries in cache",
    "Geometry cache size in bytes",
    "Halfedges",
    "Halffacets",
    "Vertices",
    "Volumes",
}

BOOL_KEYS = {
    "Simple",
}

TIMEDELTA_KEYS = {
    "Total rendering time",
}


def read_log_file(log_file: Path) -> dict[str, Any]:
    with open(log_file) as f:
        lines = [
            list(map(str.strip, line.split(":", maxsplit=1)))
            for line in f.readlines()
            if ":" in line
        ]

    data = {line[0]: (None if len(line) < 2 else line[1]) for line in lines}

    for key, value in data.items():
        if key in INT_KEYS:
            data[key] = int(value)
        elif key in BOOL_KEYS:
            data[key] = value == "yes"
        elif key in TIMEDELTA_KEYS:
            h, m, s = map(float, value.split(":"))
            data[key] = timedelta(hours=h, minutes=m, seconds=s)

    return data
