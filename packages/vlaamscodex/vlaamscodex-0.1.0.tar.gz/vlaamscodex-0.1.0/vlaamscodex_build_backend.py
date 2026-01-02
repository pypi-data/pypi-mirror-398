from __future__ import annotations

import base64
import csv
import hashlib
import os
import tempfile
import zipfile
from pathlib import Path

import setuptools.build_meta as _orig


def _wheel_dist_info_dir(zf: zipfile.ZipFile) -> str:
    for name in zf.namelist():
        if name.endswith(".dist-info/RECORD"):
            return name[: -len("RECORD")]
    raise RuntimeError("Could not find *.dist-info/RECORD in wheel")


def _hash_file(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    digest = hashlib.sha256(data).digest()
    b64 = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"sha256={b64}", len(data)


def _ensure_autoload_pth_in_wheel(wheel_path: Path) -> None:
    pth_name = "vlaamscodex_autoload.pth"
    src_pth = Path(__file__).with_name("data") / pth_name
    if not src_pth.exists():
        raise FileNotFoundError(str(src_pth))

    with zipfile.ZipFile(wheel_path, "r") as zf:
        if pth_name in zf.namelist():
            return

        dist_info_dir = _wheel_dist_info_dir(zf)
        record_name = f"{dist_info_dir}RECORD"

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            zf.extractall(td_path)

            # Add the .pth at wheel root (purelib root -> site-packages).
            (td_path / pth_name).write_bytes(src_pth.read_bytes())

            # Update RECORD.
            record_path = td_path / record_name
            rows: list[list[str]] = []
            if record_path.exists():
                with record_path.open(newline="", encoding="utf-8") as f:
                    rows = [row for row in csv.reader(f)]

            # Remove any existing entry for the .pth (shouldn't exist).
            rows = [row for row in rows if row and row[0] != pth_name]

            digest, size = _hash_file(td_path / pth_name)
            rows.append([pth_name, digest, str(size)])

            # RECORD must have empty hash/size.
            new_rows: list[list[str]] = []
            for row in rows:
                if row and row[0] == record_name:
                    new_rows.append([record_name, "", ""])
                else:
                    new_rows.append(row)

            record_path.parent.mkdir(parents=True, exist_ok=True)
            with record_path.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerows(new_rows)

            tmp_wheel = wheel_path.with_suffix(".tmp.whl")
            if tmp_wheel.exists():
                tmp_wheel.unlink()

            with zipfile.ZipFile(tmp_wheel, "w", compression=zipfile.ZIP_DEFLATED) as out:
                for file_path in sorted(td_path.rglob("*")):
                    if file_path.is_dir():
                        continue
                    rel = file_path.relative_to(td_path).as_posix()
                    out.write(file_path, rel)

            os.replace(tmp_wheel, wheel_path)


def build_wheel(
    wheel_directory: str,
    config_settings: dict[str, object] | None = None,
    metadata_directory: str | None = None,
) -> str:
    filename = _orig.build_wheel(wheel_directory, config_settings, metadata_directory)
    _ensure_autoload_pth_in_wheel(Path(wheel_directory) / filename)
    return filename


def build_editable(
    wheel_directory: str,
    config_settings: dict[str, object] | None = None,
    metadata_directory: str | None = None,
) -> str:
    filename = _orig.build_editable(wheel_directory, config_settings, metadata_directory)
    _ensure_autoload_pth_in_wheel(Path(wheel_directory) / filename)
    return filename


def build_sdist(
    sdist_directory: str,
    config_settings: dict[str, object] | None = None,
) -> str:
    return _orig.build_sdist(sdist_directory, config_settings)


get_requires_for_build_wheel = _orig.get_requires_for_build_wheel
get_requires_for_build_editable = _orig.get_requires_for_build_editable
get_requires_for_build_sdist = _orig.get_requires_for_build_sdist
prepare_metadata_for_build_wheel = _orig.prepare_metadata_for_build_wheel
prepare_metadata_for_build_editable = _orig.prepare_metadata_for_build_editable
