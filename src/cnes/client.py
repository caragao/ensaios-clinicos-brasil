"""Cliente CNES (DEMAS Dados Abertos) + resolução de UF/município/natureza jurídica.

Ver docs/cnes_schema.md. Join exato pelo código CNES fornecido pela ANVISA.
"""
from __future__ import annotations
import json
import os
import time
import requests

REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ref")


def _load_ref(name: str) -> dict:
    with open(os.path.join(REF, name), encoding="utf-8") as fh:
        return json.load(fh)


# Empresas estatais (regime empresarial, mas controle público) — contam como setor Público.
_ESTATAIS = {"2011", "2038"}  # Empresa Pública, Sociedade de Economia Mista


def setor_publico_privado(nat_cod: str | None) -> str | None:
    """Deriva o Setor a partir do código de natureza jurídica (CONCLA).

    Público (Adm. Pública 1xxx + estatais) · Terceiro Setor (sem fins lucrativos 3xxx)
    · Privado (demais empresariais 2xxx + pessoas físicas 4xxx) · Outros (5xxx).
    """
    if not nat_cod:
        return None
    if nat_cod in _ESTATAIS:
        return "Público"
    d = nat_cod[:1]
    return {"1": "Público", "2": "Privado", "3": "Terceiro Setor",
            "4": "Privado", "5": "Outros"}.get(d)


class CnesClient:
    def __init__(self, cfg: dict):
        c, h = cfg["cnes"], cfg["http"]
        self.estab_url = c["estabelecimentos_url"].rstrip("/")
        self.ibge_url = c["ibge_municipios_url"].rstrip("/")
        self.delay = h["delay_seconds"]
        self.timeout = h["timeout"]
        self.uf = _load_ref("uf.json")
        self.nat = _load_ref("natureza_juridica.json")
        self.nat_grupo = _load_ref("natureza_grupo.json")  # grupo CONCLA pelo 1º dígito
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": h["user_agent"], "Accept": "application/json",
        })
        self.ibge_list_url = self.ibge_url  # .../localidades/municipios
        self.mun_cache_path = cfg["paths"]["municipios_cache"]
        # Mapa completo IBGE: prefixo de 6 dígitos -> nome do município.
        # (O CNES fornece o código IBGE de 6 dígitos, sem o dígito verificador.)
        self.mun_map = self._load_municipios()

    def _load_municipios(self) -> dict:
        if os.path.exists(self.mun_cache_path):
            with open(self.mun_cache_path, encoding="utf-8") as fh:
                return json.load(fh)
        data = self._get(self.ibge_list_url) or []
        mun_map = {str(x["id"])[:6]: x["nome"] for x in data if x.get("id")}
        with open(self.mun_cache_path, "w", encoding="utf-8") as fh:
            json.dump(mun_map, fh, ensure_ascii=False)
        print(f"[cnes] mapa IBGE de municípios carregado ({len(mun_map)})")
        return mun_map

    def _get(self, url: str):
        try:
            r = self.session.get(url, timeout=self.timeout)
            time.sleep(self.delay)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            return None

    def municipio_nome(self, codigo_municipio) -> str | None:
        if codigo_municipio in (None, ""):
            return None
        return self.mun_map.get(str(codigo_municipio)[:6])

    def save_municipio_cache(self):
        # Mapa já persistido em _load_municipios; mantido por compatibilidade.
        pass

    def estabelecimento(self, cnes: str) -> dict | None:
        """Retorna dados normalizados do estabelecimento, ou None se não encontrado.

        Cacheia a resposta bruta em data/raw/cnes/{cnes}.json (re-execuções instantâneas).
        """
        if not cnes:
            return None
        cnes = str(cnes).strip()
        cache_dir = os.path.join(os.path.dirname(self.mun_cache_path), "..", "raw", "cnes")
        cache_dir = os.path.normpath(cache_dir)
        os.makedirs(cache_dir, exist_ok=True)
        cpath = os.path.join(cache_dir, f"{cnes}.json")
        if os.path.exists(cpath):
            with open(cpath, encoding="utf-8") as fh:
                data = json.load(fh)
        else:
            data = self._get(f"{self.estab_url}/{cnes}")
            with open(cpath, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False)
        if not isinstance(data, dict) or not data.get("codigo_cnes"):
            return None
        cod_uf = str(data.get("codigo_uf") or "")
        uf = self.uf.get(cod_uf, {})
        nat_code = str(data.get("descricao_natureza_juridica_estabelecimento") or "")
        return {
            "cnes_codigo": str(data.get("codigo_cnes")),
            "nome_razao_social": data.get("nome_razao_social"),
            "nome_fantasia": data.get("nome_fantasia"),
            "cnpj": data.get("numero_cnpj"),
            "uf": uf.get("sigla"),
            "uf_nome": uf.get("nome"),
            "municipio": self.municipio_nome(data.get("codigo_municipio")),
            "codigo_municipio": data.get("codigo_municipio"),
            "natureza_juridica_cod": nat_code or None,
            "natureza_juridica_desc": self.nat.get(nat_code, f"Natureza Jurídica {nat_code}" if nat_code else None),
            "natureza_grupo": self.nat_grupo.get(nat_code[:1]) if nat_code else None,
            "setor": setor_publico_privado(nat_code or None),
            "esfera_administrativa": data.get("descricao_esfera_administrativa"),
            "latitude": data.get("latitude_estabelecimento_decimo_grau"),
            "longitude": data.get("longitude_estabelecimento_decimo_grau"),
        }
