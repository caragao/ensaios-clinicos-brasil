# CLAUDE.md — Ensaios Clínicos no Brasil

Guia para trabalhar neste repositório. Detalhes de schema em `docs/`.

## O que é
Pipeline ETL (Python) que extrai ensaios clínicos da **ANVISA**, enriquece instituições com o
**CNES**, carrega em **SQLite** e alimenta dois dashboards (HTML estático + Streamlit).

## Comandos
```bash
pip install -r requirements.txt
python -m src.pipeline                 # ETL completo
python -m src.pipeline --skip-extract  # reprocessa de data/raw (sem rebaixar)
streamlit run app/streamlit_app.py     # dashboard exploratório
# dashboard estático: abrir dashboard/index.html no navegador
```

## Contrato da API ANVISA (crítico — ver docs/anvisa_schema.md)
- Base: `https://consultas.anvisa.gov.br/api/ensaio`. Header **`Authorization: Guest`**.
- **Cloudflare**: exige headers de navegador (User-Agent Chrome, `Accept: application/json`,
  `Referer`). `urllib` puro → 403; `requests`/`curl` com headers → 200. Throttle + backoff em 503.
- Listagem: `GET /ensaios?column=&order=asc&count=&page=&filter[fasesEstudo]=4,12`
  - Filtros vão **aninhados sob `filter[...]`** e como **string escalar CSV** (não arrays de objetos).
  - Exige ≥1 filtro (senão `MSG-013`). Resposta = Spring Page (`content`, `totalElements`).
- Detalhe: `GET /ensaio/?ddcmcoce={idDDCM}&coce={id}` (ddcmcoce vazio quando idDDCM é null).
  - Traz `classeTerapeutica`, `instituicoesPesquisa[]` com `cnes`, `numeroPacientes`, `investigadores`.
- IDs de fase: **IV=4, III/IV=12**. Situações: Autorizado=2, Iniciado=3, Finalizado=4, Suspenso=5,
  Cancelado=6, Não Analisado=7, Não autorizado=1.

## CNES (ver docs/cnes_schema.md)
- `GET https://apidadosabertos.saude.gov.br/cnes/estabelecimentos/{cnes}` (sem auth).
- Join **exato** pelo `cnes` que a ANVISA já fornece. `descricao_natureza_juridica_estabelecimento`
  retorna **código** (não descrição) → mapeado em `src/cnes/ref/natureza_juridica.json`.
- Municípios resolvidos via IBGE Localidades e cacheados em `data/processed/municipios_cache.json`.

## Modelo de dados (SQLite)
- `estudo(coce PK, ddcmcoce, ano, patrocinador, cnpj_patrocinador, medicamento, classe_terapeutica,
  fase, situacao, titulo, tipo_estudo, cid10, ...)`
- `instituicao(inst_key PK, nome, cnes, cnpj, uf, municipio, natureza_juridica_desc, match_cnes, ...)`
- `participacao(coce, inst_key, ano, num_pacientes, investigadores)` — N:N (base do drill-down).
- `inst_key`: `cnes:<x>` → fallback `cnpj:<x>` → fallback `nome:<NOME>`.

## Convenções
- Todo texto de usuário/documentação em **português**.
- Extração idempotente: detalhes em `data/raw/details/{coce}.json`; apagar para forçar re-download.
- Parâmetros (fases, período, delays) só em `config.yaml` — não hardcodar.
- `data/raw/` e o `.sqlite` são **git-ignored** (regeráveis pelo pipeline).

## Gotchas
- "Ano" (DDCM-Ano) vem do `idDDCM`, com fallback para o `coce` (ver `transform.ano_ddcm`).
- Dashboard estático carrega `dashboard/data/dataset.js` (`window.DATASET`) para funcionar em `file://`.
- Se o Cloudflare bloquear em lote, aumentar `http.delay_seconds` e rodar `--skip-extract` para retomar.
