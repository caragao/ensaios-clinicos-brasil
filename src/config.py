"""Carrega config.yaml e expõe caminhos absolutos do projeto."""
from __future__ import annotations
import os
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config(path: str | None = None) -> dict:
    path = path or os.path.join(ROOT, "config.yaml")
    with open(path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    # Resolve caminhos relativos à raiz do projeto
    for key, val in cfg.get("paths", {}).items():
        cfg["paths"][key] = os.path.join(ROOT, val)
    return cfg


def ensure_dirs(cfg: dict) -> None:
    p = cfg["paths"]
    os.makedirs(p["raw_dir"], exist_ok=True)
    os.makedirs(os.path.dirname(p["sqlite"]), exist_ok=True)
    os.makedirs(p["dashboard_data"], exist_ok=True)
