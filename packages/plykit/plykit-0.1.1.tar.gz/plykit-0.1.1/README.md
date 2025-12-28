# PLY Tools GUI

This folder provides a minimal PyQt5 GUI and a plugin system to run point-cloud processing steps from the existing scripts (`process_ply.py`, `clip_ply.py`).

Quick start

- Install dependencies (example):

  pip install -r requirements.txt

- Run the GUI:

  python3 gui.py

How it works

- Plugins are Python modules under `plugins/` which expose `get_plugin()`.
- The GUI discovers `*_plugin.py` files and shows them in the list.
- Select an input file (PLY or TXT), choose plugin, edit parameters (JSON) and click "Run Plugin".

Notes

- This is a minimal, pragmatic tool focused on functionality rather than polish.
- Existing scripts are used by the plugins; the plugins call functions in those scripts.
