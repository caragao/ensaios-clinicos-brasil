"""Extração da LISTAGEM de estudos (todas as páginas) -> data/raw/list.json."""
from __future__ import annotations
import json
import os
from .client import AnvisaClient


def extract_list(cfg: dict) -> list[dict]:
    client = AnvisaClient(cfg)
    fases_csv = ",".join(cfg["extract"]["fases"])
    page_size = cfg["extract"]["page_size"]

    first = client.listar(fases_csv, count=page_size, page=1)
    total = first.get("totalElements", 0)
    items = list(first.get("content", []))
    total_pages = first.get("totalPages") or 1
    print(f"[extract] totalElements={total} totalPages={total_pages}")

    for page in range(2, total_pages + 1):
        pg = client.listar(fases_csv, count=page_size, page=page)
        items.extend(pg.get("content", []))
        print(f"[extract] página {page}/{total_pages} -> {len(items)} itens")

    out = os.path.join(cfg["paths"]["raw_dir"], "list.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=1)
    print(f"[extract] salvo {len(items)} itens em {out}")
    return items
