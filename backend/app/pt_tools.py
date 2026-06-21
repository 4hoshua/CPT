"""Thin adapter over the vendored Packet Tracer CLI scripts in ``pt/``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pt.extract_devices_cables import build_output
from pt.ptexplorer import ptfile_decode


def decode_pkt_to_xml(pkt_path: Path, xml_path: Path) -> None:
    """Decode a .pkt/.pka file at ``pkt_path`` into XML written to ``xml_path``."""
    ptfile_decode(str(pkt_path), str(xml_path))


def build_json(xml_path: Path) -> dict[str, Any]:
    """Parse a Packet Tracer XML file into the devices/cables dict."""
    return build_output(xml_path)
