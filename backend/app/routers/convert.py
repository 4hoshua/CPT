"""Conversion routes wrapping the vendored Packet Tracer scripts."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from fastapi.responses import JSONResponse

from ..models import User
from ..security import get_current_user
from ..pt_tools import build_json, decode_pkt_to_xml

router = APIRouter(prefix="/api/convert", tags=["convert"])


def _safe_stem(filename: str | None, default: str) -> str:
    if not filename:
        return default
    stem = Path(filename).stem
    return stem or default


@router.post("/xml")
async def convert_to_xml(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
) -> Response:
    """Decode an uploaded .pkt/.pka file into Packet Tracer XML."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    with tempfile.TemporaryDirectory() as tmp:
        pkt_path = Path(tmp) / "input.pkt"
        xml_path = Path(tmp) / "output.xml"
        pkt_path.write_bytes(data)
        try:
            decode_pkt_to_xml(pkt_path, xml_path)
        except Exception as exc:  # noqa: BLE001 - surface decode failure to client
            raise HTTPException(
                status_code=400, detail=f"Failed to decode Packet Tracer file: {exc}"
            )
        xml_bytes = xml_path.read_bytes()

    stem = _safe_stem(file.filename, "output")
    return Response(
        content=xml_bytes,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{stem}.xml"'},
    )


@router.post("/json")
async def convert_to_json(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
) -> JSONResponse:
    """Extract devices and cables from an uploaded Packet Tracer XML file."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "input.xml"
        xml_path.write_bytes(data)
        try:
            result = build_json(xml_path)
        except Exception as exc:  # noqa: BLE001 - surface parse failure to client
            raise HTTPException(
                status_code=400, detail=f"Failed to parse XML: {exc}"
            )

    # Drop the temp absolute path; expose the original upload name instead.
    result["source"] = file.filename
    return JSONResponse(content=result)
