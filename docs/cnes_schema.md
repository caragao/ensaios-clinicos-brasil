# Schema CNES (enriquecimento) — congelado

Fonte: **API DEMAS Dados Abertos** — `https://apidadosabertos.saude.gov.br/`.
Chave de junção: **código CNES** já fornecido pela ANVISA em `instituicoesPesquisa[].cnes`
(⇒ join **exato**, sem fuzzy matching).

## Endpoint
```
GET https://apidadosabertos.saude.gov.br/cnes/estabelecimentos/{codigo_cnes}
```
- Headers: `User-Agent` de navegador + `Accept: application/json` (sem auth).
- Retorna objeto único do estabelecimento.

## Campos usados
| campo | exemplo | uso |
|---|---|---|
| `codigo_cnes` | `2239884` | chave |
| `nome_razao_social` | `"FUNDACAO UNIVERSIDADE DE CAXIAS DO SUL"` | nome oficial |
| `nome_fantasia` | `"CENTRO CLINICO DA UNIVERSIDADE..."` | nome fantasia |
| `numero_cnpj` | `"88648761001096"` | CNPJ |
| `codigo_uf` | `43` | IBGE UF → sigla (ver `ref/uf.json`) |
| `codigo_municipio` | `430510` | IBGE município → nome (ver `ref/municipios`) |
| `descricao_natureza_juridica_estabelecimento` | `3069` | **código** de natureza jurídica (CONCLA) → descrição (ver `ref/natureza_juridica.json`) |
| `descricao_esfera_administrativa` | `"MUNICIPAL"` | esfera |
| `codigo_tipo_unidade` | `4` | tipo de estabelecimento |
| `latitude_estabelecimento_decimo_grau` / `longitude_...` | | geolocalização (mapa) |

> Nota: apesar do nome, `descricao_natureza_juridica_estabelecimento` retorna o **código** numérico
> da natureza jurídica (padrão CONCLA/IBGE), não a descrição.

## Tabelas de referência (bundled em `src/cnes/ref/`)
- **UF** (`uf.json`): código IBGE (2 díg.) → `{sigla, nome}`. 27 entradas, estático.
- **Natureza jurídica** (`natureza_juridica.json`): código CONCLA → descrição. Estático (subset relevante;
  fallback = código bruto se ausente).
- **Municípios**: resolvidos via IBGE Localidades e cacheados em `data/processed/municipios_cache.json`:
  `GET https://servicodados.ibge.gov.br/api/v1/localidades/municipios/{codigo_municipio}` → `.nome`, `.microrregiao.mesorregiao.UF.sigla`.

## Robustez
- CNES ausente/inválido, ou estabelecimento não encontrado (404) → registrar instituição só com os
  dados da ANVISA (`instituto`, `cnpj`), marcando `match_cnes=false`.
- Gerar relatório de cobertura (nº de CNES resolvidos / total) ao fim do enriquecimento.
