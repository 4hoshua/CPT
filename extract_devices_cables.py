#!/usr/bin/env python3

"""Extrai dispositivos e cabos de um XML do Packet Tracer."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def parse_number(value: str | None) -> int | float | None:
    text = normalize_text(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return None


def parse_bool(value: str | None) -> bool | None:
    text = normalize_text(value)
    if text is None:
        return None
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


def extract_devices(root: ET.Element) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    devices: list[dict[str, Any]] = []
    devices_by_addr: dict[str, dict[str, Any]] = {}

    for device in root.findall("./NETWORK/DEVICES/DEVICE"):
        type_node = device.find("ENGINE/TYPE")
        logical_node = device.find("WORKSPACE/LOGICAL")

        device_data = {
            "name": normalize_text(device.findtext("ENGINE/NAME")),
            "category": normalize_text(type_node.text if type_node is not None else None),
            "model": normalize_text(type_node.get("model") if type_node is not None else None),
            "custom_model": normalize_text(type_node.get("customModel") if type_node is not None else None),
            "power": parse_bool(device.findtext("ENGINE/POWER")),
            "description": normalize_text(device.findtext("ENGINE/DESCRIPTION")),
            "dev_addr": normalize_text(device.findtext("WORKSPACE/LOGICAL/DEV_ADDR")),
            "mem_addr": normalize_text(device.findtext("WORKSPACE/LOGICAL/MEM_ADDR")),
            "x": parse_number(logical_node.findtext("X") if logical_node is not None else None),
            "y": parse_number(logical_node.findtext("Y") if logical_node is not None else None),
            "cluster_id": normalize_text(device.findtext("WORKSPACE/LOGICAL/DEVCLUSTERID")),
        }

        devices.append(device_data)

        dev_addr = device_data["dev_addr"]
        if dev_addr:
            devices_by_addr[dev_addr] = device_data

    return devices, devices_by_addr


def extract_cables(root: ET.Element, devices_by_addr: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    cables: list[dict[str, Any]] = []

    for link in root.findall("./NETWORK/LINKS/LINK"):
        cable_node = link.find("CABLE")
        if cable_node is None:
            continue

        ports = [normalize_text(port.text) for port in cable_node.findall("PORT")]
        from_addr = normalize_text(cable_node.findtext("FROM_DEVICE_MEM_ADDR"))
        to_addr = normalize_text(cable_node.findtext("TO_DEVICE_MEM_ADDR"))
        from_device = devices_by_addr.get(from_addr or "")
        to_device = devices_by_addr.get(to_addr or "")

        cables.append(
            {
                "type": normalize_text(link.findtext("TYPE")),
                "length": parse_number(cable_node.findtext("LENGTH")),
                "functional": parse_bool(cable_node.findtext("FUNCTIONAL")),
                "from": {
                    "device": from_device["name"] if from_device else None,
                    "dev_addr": from_addr,
                    "port": ports[0] if len(ports) > 0 else None,
                    "reference": normalize_text(cable_node.findtext("FROM")),
                },
                "to": {
                    "device": to_device["name"] if to_device else None,
                    "dev_addr": to_addr,
                    "port": ports[1] if len(ports) > 1 else None,
                    "reference": normalize_text(cable_node.findtext("TO")),
                },
                "dce": {
                    "device_reference": normalize_text(cable_node.findtext("DCEDEV")),
                    "port": normalize_text(cable_node.findtext("DCEPORT")),
                },
                "geo_view_color": normalize_text(cable_node.findtext("GEO_VIEW_COLOR")),
                "managed_in_rack_view": parse_bool(cable_node.findtext("IS_MANAGED_IN_RACK_VIEW")),
            }
        )

    return cables


def build_output(xml_path: Path) -> dict[str, Any]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    devices, devices_by_addr = extract_devices(root)
    cables = extract_cables(root, devices_by_addr)
    unresolved_cables = [
        cable
        for cable in cables
        if cable["from"]["device"] is None or cable["to"]["device"] is None
    ]

    return {
        "source": str(xml_path),
        "device_count": len(devices),
        "cable_count": len(cables),
        "unresolved_cable_count": len(unresolved_cables),
        "devices": devices,
        "cables": cables,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extrai dispositivos e cabos de um XML exportado do Packet Tracer."
    )
    parser.add_argument("input", type=Path, help="Arquivo XML de entrada")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Arquivo JSON de saída. Se omitido, imprime no terminal.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_output(args.input)
    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        sys.stdout.write(output + "\n")

    if result["unresolved_cable_count"] > 0:
        print(
            f"[aviso] {result['unresolved_cable_count']} cabo(s) não tiveram os dois endpoints resolvidos.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())