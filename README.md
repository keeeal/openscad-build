# OpenSCAD Build
A hierarchical OpenSCAD build system in a docker container.

![pipeline](https://github.com/keeeal/openscad-build/actions/workflows/tests.yaml/badge.svg)

## What openscad-build is:

- A way of structuring a project consisting of multiple OpenSCAD files into
  subassemblies based on folder structure, with the goal of simplifying large
  OpenSCAD projects.
- A tool to generate a `main.scad` file for the project, allowing each part and
  subassembly to be easily viewed in OpenSCAD.
- A way of specifying which parts to render into STL files, with per-part
  settings like render quality.

## What openscad-build is not:

- A build system which considers each OpenSCAD module to be a part.
  OpenSCAD Build treats each file as a part. Files may have more than
  one module.
- A batch exporter for generating multiple STL files per OpenSCAD file with
  different settings (See [OSBS](https://github.com/ridercz/OSBS)).
- An tool for running OpenSCAD builds in parallel (See
  [OpenSCAD-Parallel-Build](https://github.com/TheJKM/OpenSCAD-Parallel-Build)).
- An autoplater for 3D printing (See
  [scad-build](https://github.com/unjordy/scad-build)).
- A download page generator for rendered STL files (See
  [openscad-makefile](https://github.com/mofosyne/openscad-makefile))
- An OpenSCAD wrapper for Python (See
  [SolidPython](https://github.com/SolidCode/SolidPython)) or any other
  language.
