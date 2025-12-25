import os
import time
import zipfile
from pathlib import Path

import tomllib

with zipfile.ZipFile(assets_src := Path(__file__).with_name("_static") / "assets.zip") as zf:
    assets_dst, modification_time_tuples = assets_src.parent, {}
    for zi in zf.infolist():
        if not (target := assets_dst / zi.filename).exists():
            zf.extract(zi, assets_dst)
            modification_time_tuples[target] = zi.date_time
    # Set the modification and access times of the extracted files to what the
    # archive reports. This must be done in a separate loop because the
    # modification time of a directory gets updated when a file is extracted
    # into it.
    for target, modification_time_tuple in modification_time_tuples.items():
        modification_timestamp = time.mktime((*modification_time_tuple, 0, 0, -1))
        os.utime(target, (modification_timestamp, modification_timestamp))

with open(Path(__file__).parents[1] / "pyproject.toml", "rb") as reader:
    metadata = tomllib.load(reader)["project"]
author = metadata["authors"][0]["name"]
copyright = f"2025, {author}"
release = metadata["version"]
project = metadata["name"] + " " + release

extensions = ["myst_parser"]
source_suffix = [".md", ".rst"]
exclude_patterns = ["_build"]

html_css_files = ["styles/custom.css"]
html_favicon = "_static/images/favicon.svg"
html_logo = "_static/images/logo.svg"
html_static_path = ["_static"]
html_theme = "furo"
html_theme_options = {
    "light_css_variables": {
        "font-stack": "Signika pysorteddict, system-ui, sans-serif, Apple Color Emoji, Segoe UI Emoji",
        "font-stack--headings": "Signika pysorteddict, system-ui, sans-serif, Apple Color Emoji, Segoe UI Emoji",
        "font-stack--monospace": "JetBrainsMono pysorteddict, Consolas, Monaco, Liberation Mono, monospace",
    },
    "source_branch": "main",
    "source_directory": "docs",
    "source_repository": metadata["urls"]["Repository"],
}
html_title = project
html_use_index = False

myst_heading_anchors = 4
templates_path = ["_templates"]
