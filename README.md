# Ensaios Clínicos no Brasil — Mapeamento & Dashboard

Mapeia os **ensaios clínicos** registrados na ANVISA e os **centros de pesquisa** que os
executam, enriquece as instituições com dados do **CNES** (Natureza Jurídica, UF, município) e
entrega dois dashboards para análise da evolução dos estudos e drill-down por instituição.

> **Escopo atual:** estudos de **Fase IV e III/IV**, período **2015–2025**, todas as situações.
> Parametrizável em [`config.yaml`](config.yaml).

## Fontes de dados
- **ANVISA** — API de Consultas de Ensaios Clínicos (`consultas.anvisa.gov.br/api/ensaio`).
  Contrato documentado em [`docs/anvisa_schema.md`](docs/anvisa_schema.md).
- **CNES / DEMAS Dados Abertos** — `apidadosabertos.saude.gov.br/cnes/estabelecimentos`.
  Join **exato** pelo código CNES que a própria ANVISA fornece por instituição.
  Ver [`docs/cnes_schema.md`](docs/cnes_schema.md).

## Arquitetura
```
ANVISA API ─► data/raw/ ─► transform ─► SQLite (data/processed/ensaios.sqlite)
CNES  API ─────────────────► enrich ──┘        │
                                               ├─► dashboard/ (HTML estático, dataset.js)
                                               └─► app/ (Streamlit, consulta ao vivo)
```

## Setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |  Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## Rodar o pipeline (ETL)
```bash
python -m src.pipeline                 # extrai da ANVISA, enriquece com CNES, gera SQLite + dataset
python -m src.pipeline --skip-extract  # reprocessa a partir de data/raw já baixado
```
Saídas: `data/processed/ensaios.sqlite` e `dashboard/data/dataset.js` (+ `dataset.json`).

> A API da ANVISA fica atrás de **Cloudflare**. O cliente usa headers de navegador + throttling;
> a extração de detalhes é **idempotente** (retoma de onde parou). Ajuste `http.delay_seconds` em
> `config.yaml` se encontrar bloqueios (HTTP 503).

## Dashboards
- **Estático (HTML):** abra `dashboard/index.html` no navegador (funciona direto do disco).
  Publicável no GitHub Pages ou como Artifact. Filtros: Ano, Situação, Fase, Classe Terapêutica,
  Patrocinador, UF, Instituição. Clique numa instituição para ver o detalhe (estudos, ano, pacientes).
- **Exploratório (Streamlit):**
  ```bash
  streamlit run app/streamlit_app.py
  ```

## Estrutura
```
src/          pipeline ETL (anvisa/, cnes/, transform, load, aggregate, pipeline)
docs/         schemas congelados + dicionário de dados
dashboard/    dashboard HTML estático (index.html, assets/, data/)
app/          dashboard Streamlit
data/         raw/ (bruto, git-ignored) e processed/ (SQLite)
config.yaml   parâmetros (fases, período, rate-limits)
```

## Limitações conhecidas
- O **Ano** é derivado do sufixo `NNN/AAAA` do id do estudo (não há data de estudo confiável na API).
- Instituições sem código CNES não recebem enriquecimento (marcadas `match_cnes=false`).
- Dados dependem da carga atual da base pública da ANVISA.
