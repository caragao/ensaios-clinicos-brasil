"""Orquestra o pipeline completo: extract -> detail -> transform -> enrich -> load -> aggregate.

Uso:
    python -m src.pipeline                # pipeline completo
    python -m src.pipeline --skip-extract # reprocessa a partir de data/raw já baixado
"""
from __future__ import annotations
import argparse

from .config import load_config, ensure_dirs
from .anvisa.extract import extract_list
from .anvisa.detail import extract_details
from . import transform as T
from .cnes.enrich import enrich
from . import load as L
from . import aggregate as A


def run(skip_extract: bool = False):
    cfg = load_config()
    ensure_dirs(cfg)

    if skip_extract:
        details = extract_details(cfg)  # lê list.json e usa cache de detalhes
    else:
        items = extract_list(cfg)
        details = extract_details(cfg, items)

    ex = cfg["extract"]
    data = T.build(details, ano_min=ex.get("ano_min"), ano_max=ex.get("ano_max"))
    print(f"[transform] estudos={len(data['estudos'])} instituicoes={len(data['instituicoes'])} "
          f"participacoes={len(data['participacoes'])}")

    data["instituicoes"] = enrich(data["instituicoes"], cfg)

    L.load(cfg["paths"]["sqlite"], data)
    A.export(cfg["paths"]["sqlite"], cfg["paths"]["dashboard_data"])
    print("[pipeline] concluído.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-extract", action="store_true",
                    help="reprocessa a partir de data/raw sem rebaixar a listagem")
    args = ap.parse_args()
    run(skip_extract=args.skip_extract)
