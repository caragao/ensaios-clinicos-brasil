"""Extração dos DETALHES de cada estudo -> data/raw/details/{coce}.json.

Idempotente: pula detalhes já baixados (permite retomar após bloqueio Cloudflare).
"""
from __future__ import annotations
import json
import os
from .client import AnvisaClient


def _safe(coce: str) -> str:
    return str(coce).replace("/", "_").replace("\\", "_")


def extract_details(cfg: dict, items: list[dict] | None = None) -> list[dict]:
    client = AnvisaClient(cfg)
    raw = cfg["paths"]["raw_dir"]
    if items is None:
        with open(os.path.join(raw, "list.json"), encoding="utf-8") as fh:
            items = json.load(fh)

    ddir = os.path.join(raw, "details")
    os.makedirs(ddir, exist_ok=True)
    details, falhas = [], []

    for i, it in enumerate(items, 1):
        coce = it.get("id")
        ddcmcoce = it.get("idDDCM")
        fpath = os.path.join(ddir, f"{_safe(coce)}.json")
        if os.path.exists(fpath):
            with open(fpath, encoding="utf-8") as fh:
                details.append(json.load(fh))
            continue
        try:
            det = client.detalhe(ddcmcoce, coce)
            with open(fpath, "w", encoding="utf-8") as fh:
                json.dump(det, fh, ensure_ascii=False, indent=1)
            details.append(det)
        except Exception as e:  # noqa: BLE001
            print(f"[detail] FALHA coce={coce}: {e}")
            falhas.append(coce)
        if i % 20 == 0:
            print(f"[detail] {i}/{len(items)} processados")

    print(f"[detail] {len(details)} detalhes ok, {len(falhas)} falhas")
    if falhas:
        with open(os.path.join(raw, "detail_falhas.json"), "w", encoding="utf-8") as fh:
            json.dump(falhas, fh, ensure_ascii=False, indent=1)
    return details
