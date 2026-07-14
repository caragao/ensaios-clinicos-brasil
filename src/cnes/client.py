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


class CnesClient:
    def __init__(self, cfg: dict):
        c, h = cfg["cnes"], cfg["http"]
        self.estab_url = c["estabelecimentos_url"].rstrip("/")
        self.ibge_url = c["ibge_municipios_url"].rstrip("/")
        self.delay = h["delay_seconds"]
        self.timeout = h["timeout"]
        self.uf = _load_ref("uf.json")
        self.nat = _load_ref("natureza_juridica.json")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": h["user_agent"], "Accept": "application/json",
        })
        self.mun_cache_path = cfg["paths"]["municipios_cache"]
        self.mun_cache = {}
        if os.path.exists(self.mun_cache_path):
            with open(self.mun_cache_path, encoding="utf-8") as fh:
                self.mun_cache = json.load(fh)

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
        key = str(codigo_municipio)
        if key in self.mun_cache:
            return self.mun_cache[key]
        data = self._get(f"{self.ibge_url}/{key}")
        nome = data.get("nome") if isinstance(data, dict) else None
        self.mun_cache[key] = nome
        return nome

    def save_municipio_cache(self):
        with open(self.mun_cache_path, "w", encoding="utf-8") as fh:
            json.dump(self.mun_cache, fh, ensure_ascii=False, indent=1)

    def estabelecimento(self, cnes: str) -> dict | None:
        """Retorna dados normalizados do estabelecimento, ou None se não encontrado."""
        if not cnes:
            return None
        data = self._get(f"{self.estab_url}/{str(cnes).strip()}")
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
            "esfera_administrativa": data.get("descricao_esfera_administrativa"),
            "latitude": data.get("latitude_estabelecimento_decimo_grau"),
            "longitude": data.get("longitude_estabelecimento_decimo_grau"),
        }
