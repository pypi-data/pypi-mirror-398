"""
hypersonic_heygen.hya

CLI: hya
- Creates HeyGen_avatar.ipynb in current folder (or --output path)
- Ensures ./images/app-key.png exists next to the notebook by copying from package assets

Industry-practice behavior:
- Try to scaffold a self-contained demo folder (notebook + images)
- If user environment blocks folder creation, do NOT fail; print a helpful message.
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

try:
    # Python 3.9+
    import importlib.resources as pkg_resources
except Exception:  # pragma: no cover
    pkg_resources = None


DEFAULT_NOTEBOOK_NAME = "HeyGen_avatar.ipynb"
IMAGES_DIRNAME = "images"
APP_KEY_FILENAME = "app-key.png"


def _copy_asset_app_key_png(target_images_dir: Path) -> tuple[bool, str]:
    """
    Copy packaged app-key.png into target_images_dir/app-key.png.

    Returns (ok, message).
    """
    try:
        target_images_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return (False, f"Cannot create folder '{target_images_dir}': {e}")

    dest = target_images_dir / APP_KEY_FILENAME

    # If already exists, keep it (avoid overwriting user-customized image)
    if dest.exists():
        return (True, f"Image already exists: {dest}")

    # Preferred: importlib.resources (works with wheels)
    if pkg_resources is None:
        return (False, "importlib.resources unavailable; cannot load packaged asset reliably.")

    try:
        # Our packaged path: hypersonic_heygen/assets/images/app-key.png
        # Note: use files() API for modern importlib.resources
        asset_path = (
            pkg_resources.files("hypersonic_heygen")
            / "assets"
            / "images"
            / APP_KEY_FILENAME
        )

        # In some environments asset_path is a Traversable; copy bytes out
        with asset_path.open("rb") as fsrc, open(dest, "wb") as fdst:
            shutil.copyfileobj(fsrc, fdst)

        return (True, f"Copied image → {dest}")
    except Exception as e:
        return (False, f"Failed to copy packaged image: {e}")


def _write_notebook_bytes(output_path: Path) -> tuple[bool, str]:
    """
    Write packaged LiveAvatar_v2.ipynb to output_path.
    Returns (ok, message).
    """
    if pkg_resources is None:
        return (False, "importlib.resources unavailable; cannot load packaged notebook reliably.")

    try:
        nb_asset = (
            pkg_resources.files("hypersonic_heygen")
            / "assets"
            / "LiveAvatar_v2.ipynb"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Don't overwrite existing file silently
        if output_path.exists():
            return (False, f"Notebook already exists: {output_path} (delete it or choose a different --output)")

        with nb_asset.open("rb") as fsrc, open(output_path, "wb") as fdst:
            shutil.copyfileobj(fsrc, fdst)

        return (True, f"Notebook created: {output_path}")
    except Exception as e:
        return (False, f"Failed to write notebook: {e}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hya",
        description="Create the HeyGen LiveAvatar v2 demo notebook in the current folder (and copy ./images/app-key.png).",
    )
    # Keep it simple: default output is current working dir / HeyGen_avatar.ipynb
    parser.add_argument(
        "--output",
        default=DEFAULT_NOTEBOOK_NAME,
        help="Output notebook path (default: HeyGen_avatar.ipynb in current folder).",
    )

    args = parser.parse_args(argv)

    out_path = Path(args.output).expanduser().resolve()

    ok_nb, msg_nb = _write_notebook_bytes(out_path)
    if not ok_nb:
        print(f"[hya] ❌ {msg_nb}")
        return 1

    print(f"[hya] ✅ {msg_nb}")

    # Now ensure ./images/app-key.png exists next to the notebook
    images_dir = out_path.parent / IMAGES_DIRNAME
    ok_img, msg_img = _copy_asset_app_key_png(images_dir)

    if ok_img:
        print(f"[hya] ✅ {msg_img}")
    else:
        # Do not fail the command; notebook creation succeeded.
        print(f"[hya] ⚠️  {msg_img}")
        print(f"[hya] ⚠️  If your notebook shows a broken image, create '{images_dir}' and copy '{APP_KEY_FILENAME}' there.")
        print(f"[hya] ⚠️  (Corporate folder protection can block folder creation in some directories.)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
