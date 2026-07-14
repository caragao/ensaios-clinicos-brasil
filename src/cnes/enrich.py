"""Enriquece as instituições com dados do CNES (join exato por código CNES)."""
from __future__ import annotations
from .client import CnesClient


def enrich(instituicoes: list[dict], cfg: dict) -> list[dict]:
    client = CnesClient(cfg)
    total_cnes = sum(1 for i in instituicoes if i.get("cnes"))
    resolved = 0

    for inst in instituicoes:
        inst.update({
            "uf": None, "uf_nome": None, "municipio": None, "codigo_municipio": None,
            "natureza_juridica_cod": None, "natureza_juridica_desc": None, "natureza_grupo": None,
            "esfera_administrativa": None, "latitude": None, "longitude": None,
            "cnes_nome_razao": None, "cnes_nome_fantasia": None, "match_cnes": False,
        })
        cnes = inst.get("cnes")
        if not cnes:
            continue
        est = client.estabelecimento(cnes)
        if not est:
            continue
        resolved += 1
        inst.update({
            "uf": est["uf"], "uf_nome": est["uf_nome"],
            "municipio": est["municipio"], "codigo_municipio": est["codigo_municipio"],
            "natureza_juridica_cod": est["natureza_juridica_cod"],
            "natureza_juridica_desc": est["natureza_juridica_desc"],
            "natureza_grupo": est["natureza_grupo"],
            "esfera_administrativa": est["esfera_administrativa"],
            "latitude": est["latitude"], "longitude": est["longitude"],
            "cnes_nome_razao": est["nome_razao_social"],
            "cnes_nome_fantasia": est["nome_fantasia"],
            "cnpj": inst.get("cnpj") or est.get("cnpj"),
            "match_cnes": True,
        })

    client.save_municipio_cache()
    print(f"[cnes] instituições={len(instituicoes)} com_cnes={total_cnes} resolvidas={resolved}")
    return instituicoes
