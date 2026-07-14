"""Normaliza os detalhes brutos da ANVISA em tabelas relacionais.

Saídas (em memória):
- estudos: 1 por estudo (coce)
- instituicoes: 1 por instituição única (chave: CNES; fallback CNPJ; fallback nome)
- participacoes: N:N estudo x instituição (com nº de pacientes, ano, investigadores)
"""
from __future__ import annotations
import re

ANO_RE = re.compile(r"/(\d{4})\s*$")


def ano_de(coce) -> int | None:
    """Deriva o ano do sufixo NNN/AAAA do id do estudo."""
    if not coce:
        return None
    m = ANO_RE.search(str(coce))
    return int(m.group(1)) if m else None


def inst_key(inst: dict) -> str:
    cnes = (inst.get("cnes") or "").strip()
    if cnes:
        return f"cnes:{cnes}"
    cnpj = (inst.get("cnpj") or "").strip()
    if cnpj:
        return f"cnpj:{cnpj}"
    return f"nome:{(inst.get('instituto') or '').strip().upper()}"


def _clean(s):
    return s.strip() if isinstance(s, str) else s


def build(details: list[dict], ano_min=None, ano_max=None):
    estudos, participacoes = [], []
    instituicoes: dict[str, dict] = {}

    for det in details:
        coce = det.get("id")
        ano = ano_de(coce)
        if ano is not None and ano_min and ano < ano_min:
            continue
        if ano is not None and ano_max and ano > ano_max:
            continue

        estudos.append({
            "coce": coce,
            "ddcmcoce": det.get("idDDCM"),
            "numero_processo": det.get("numeroProcesso"),
            "ano": ano,
            "patrocinador": _clean(det.get("empresa")),
            "cnpj_patrocinador": det.get("cnpj"),
            "medicamento": _clean(det.get("nomeProduto")),
            "classe_terapeutica": _clean(det.get("classeTerapeutica")),
            "fase": det.get("faseEstudo"),
            "situacao": det.get("situacao"),
            "titulo": _clean(det.get("motivoPesquisa")),
            "tipo_estudo": _clean(det.get("tipoEstudo")),
            "tipo_medicamento": _clean(det.get("tipoMedicamento")),
            "cid10": _clean(det.get("cid10")),
        })

        for inst in det.get("instituicoesPesquisa", []) or []:
            key = inst_key(inst)
            if key not in instituicoes:
                instituicoes[key] = {
                    "inst_key": key,
                    "nome": _clean(inst.get("instituto")),
                    "cnes": _clean(inst.get("cnes")),
                    "cnpj": _clean(inst.get("cnpj")),
                }
            invs = "; ".join(
                _clean(iv.get("nome")) for iv in (inst.get("investigadores") or []) if iv.get("nome")
            )
            participacoes.append({
                "coce": coce,
                "inst_key": key,
                "ano": ano,
                "num_pacientes": inst.get("numeroPacientes") or 0,
                "investigadores": invs or None,
            })

    return {
        "estudos": estudos,
        "instituicoes": list(instituicoes.values()),
        "participacoes": participacoes,
    }
