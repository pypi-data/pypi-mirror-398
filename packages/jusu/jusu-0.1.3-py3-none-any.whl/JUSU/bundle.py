"""Bundle export helpers (zipping) for JUSU components."""
from __future__ import annotations

import os
import zipfile


def export_zip(html_path: str, css_path: str, zip_path: str) -> str:
    """Create a zip archive containing the HTML and CSS files and return path."""
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(html_path, os.path.basename(html_path))
        zf.write(css_path, os.path.basename(css_path))
    return zip_path
