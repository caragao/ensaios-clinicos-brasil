"""Cliente HTTP da API de Ensaios Clínicos da ANVISA.

Contrato (ver docs/anvisa_schema.md):
- Header `Authorization: Guest` + headers de navegador para passar o Cloudflare.
- Listagem: GET /ensaios?column=&order=asc&count=&page=&filter[fasesEstudo]=CSV
- Detalhe:  GET /ensaio/?ddcmcoce=&coce=
"""
from __future__ import annotations
import time
import requests


class AnvisaClient:
    def __init__(self, cfg: dict):
        a, h = cfg["anvisa"], cfg["http"]
        self.base = a["base_url"].rstrip("/")
        self.delay = h["delay_seconds"]
        self.max_retries = h["max_retries"]
        self.backoff = h["backoff_seconds"]
        self.timeout = h["timeout"]
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": a["authorization"],
            "User-Agent": h["user_agent"],
            "Accept": "application/json",
            "Referer": "https://consultas.anvisa.gov.br/",
        })

    def _get(self, path: str, params=None):
        url = f"{self.base}/{path.lstrip('/')}"
        last = None
        for attempt in range(self.max_retries):
            try:
                r = self.session.get(url, params=params, timeout=self.timeout)
                # 429/503 = throttling/Cloudflare: espera e tenta de novo
                if r.status_code in (429, 500, 502, 503):
                    last = f"HTTP {r.status_code}"
                    time.sleep(self.backoff * (attempt + 1))
                    continue
                r.raise_for_status()
                time.sleep(self.delay)
                return r.json()
            except requests.RequestException as e:
                last = str(e)
                time.sleep(self.backoff * (attempt + 1))
        raise RuntimeError(f"Falha em GET {url} params={params}: {last}")

    def listar(self, fases_csv: str, count: int, page: int) -> dict:
        """Uma página da listagem. `filter[fasesEstudo]` é CSV escalar (ex.: '4,12')."""
        params = {
            "column": "", "order": "asc", "count": count, "page": page,
            "filter[fasesEstudo]": fases_csv,
        }
        return self._get("ensaios", params)

    def detalhe(self, ddcmcoce, coce) -> dict:
        """Detalhe de um estudo. ddcmcoce pode ser vazio quando idDDCM é null."""
        params = {"ddcmcoce": ddcmcoce or "", "coce": coce}
        return self._get("ensaio/", params)
