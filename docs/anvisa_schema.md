# Schema real da API ANVISA — Ensaios Clínicos (congelado)

Capturado empiricamente em 2026-07-14 a partir de `https://consultas.anvisa.gov.br/api/ensaio/`.

## Autenticação e acesso
- Header **`Authorization: Guest`** (valor fixo; o site o grava em `localStorage`).
- Endpoint atrás de **Cloudflare**. Requisições passam com headers de navegador realistas
  (`User-Agent` de Chrome, `Accept: application/json`, `Referer: https://consultas.anvisa.gov.br/`).
  Validado com `python requests` e `curl` (ambos HTTP 200). `urllib` puro recebe 403.
- Boa prática: throttling entre chamadas + backoff em 429/503.

## Listas de referência (GET, sem parâmetros)
- `GET /api/ensaio/fasesEstudo` → `[{id, descricao}]`
  - Fases relevantes ao projeto: **IV → id `4`**, **III/IV → id `12`**.
  - Outras: I=1, II=2, III=3, N/A=5, IIA=6, IIB=7, 0=8, I/II=9, II/III=10, I/III=11, IIIB=13, IB=14.
- `GET /api/ensaio/situacoesEstudo` → `[{id, descricao}]`
  - Autorizado=2, Cancelado=6, Finalizado=4, Iniciado=3, Não Analisado=7, Não autorizado=1, Suspenso=5.
- `GET /api/ensaio/titulosEstudo`, `.../nomesProduto` → autocomplete.

## Listagem paginada
```
GET /api/ensaio/ensaios?column=&order=asc&count={N}&page={P}&filter[fasesEstudo]={CSV}
```
- **Paginação/ordenação no topo**: `column` (pode ser vazio), `order` (`asc`/`desc`), `count`, `page`.
- **Filtros aninhados sob `filter[...]`**, como **strings escalares** (NÃO arrays de objetos).
  Ex.: `filter[fasesEstudo]=4,12` (CSV de ids). Outros filtros disponíveis (mesma convenção):
  `filter[situacoesEstudo]`, `filter[dataCeDDCMInicial]` (dd/MM/yyyy), `filter[dataCeDDCMFinal]`,
  `filter[cnpjPatrocinador]`, `filter[nomeInvestigador]`, `filter[cid10]`, `filter[titulosEstudo]`,
  `filter[nomesProduto]`, `filter[tiposMedicamento]`, `filter[tiposEstudo]`,
  `filter[protocolosClinicos]`, `filter[numerosProcesso]`, `filter[ceDDCMs]`,
  `filter[instituicaoPesquisa]`.
- **Exige ≥1 filtro** (senão erro de negócio `MSG-013`).
- Passar `filter[X]` como array de objetos → `500 Invalid property ...` (bean `PaginationBuilder`);
  `[object Object]` no valor → `500 SQLGrammarException`. **Sempre CSV escalar.**

### Resposta (Spring Data Page)
```json
{
  "content": [ ItemLista, ... ],
  "totalElements": 214, "totalPages": ..., "size": ..., "number": ...,
  "first": true, "last": false, "numberOfElements": ..., "sort": ...
}
```

### ItemLista
| campo | exemplo | nota |
|---|---|---|
| `idDDCM` | `"10/2018"` ou `null` | ddcmcoce do detalhe; **pode ser null** (registros antigos) |
| `id` | `"120/2013"` | coce do detalhe; `NNN/AAAA` |
| `numeroProcesso` | `"25351624549201275"` | |
| `nomeProduto` | `" ATAZANAVIR"` | medicamento experimental (trim) |
| `faseEstudo` | `"IV"` | |
| `cid10` | `"B24 - DOENÇA ..."` | código + descrição |
| `empresa` | `"BRISTOL-... - 56998982000107"` | patrocinador (às vezes com CNPJ anexado) |
| `situacao` | `null` | frequentemente null na listagem; ver detalhe |
| `dataCarga` | `"2026-07-14T..."` | data de carga da base, **não** é a data do estudo |

## Detalhe do estudo
```
GET /api/ensaio/ensaio/?ddcmcoce={idDDCM}&coce={id}
```
- `ddcmcoce` = `idDDCM` da listagem (se `null`, enviar **vazio** — funciona: `?ddcmcoce=&coce=120/2013`).
- `coce` = `id` da listagem.

### Resposta (objeto)
Campos do topo (superset da listagem) + :
| campo | exemplo | uso no projeto |
|---|---|---|
| `cnpj` | `"51780468000187"` | CNPJ do patrocinador |
| `empresa` | `"JANSSEN-CILAG FARMACÊUTICA LTDA"` | patrocinador |
| `classeTerapeutica` | `"ANTIDIABETICOS"` | **filtro Classe Terapêutica** |
| `tipoEstudo` | `"POSSUI COOPERAÇÃO ESTRANGEIRA"` | |
| `tipoMedicamento` | `"SINTÉTICO/SEMISSINTÉTICO"` | |
| `numeroProtocoloClinico` | | |
| `motivoPesquisa` | `"UM ESTUDO RANDOMIZADO..."` | título/descrição do estudo |
| `situacao` | | situação do estudo |
| `instituicoesPesquisa` | `[ Instituicao ]` | **centros de pesquisa (drill-down)** |

### Instituicao (item de `instituicoesPesquisa`)
| campo | exemplo | uso |
|---|---|---|
| `id` | `"171/2014"` | = coce do estudo |
| `instituto` | `"AMBULATORIO CENTRAL DA UNIVERSIDADE DE CX DO SUL"` | nome do centro |
| `cnes` | `"2239884"` | **código CNES → join exato com CNES** |
| `cnpj` | `"88648761001096"` | CNPJ do centro |
| `numeroPacientes` | `19` | **nº de pacientes naquele estudo** |
| `investigadores` | `[{id, nome}]` | investigador(es) principal(is) |
| `toggle` | `false` | estado de UI (ignorar) |

## Dimensionamento (2026-07-14)
- Fase IV (`4`): **200** estudos. Fase III/IV (`12`): **14**. Combinado (`4,12`): **214**.
- ⇒ ~214 chamadas de detalhe. Job pequeno.

## Derivação do "Ano" (DDCM - Ano)
Não há campo de data do estudo confiável na resposta (só `dataCarga` = carga da base).
Derivar o ano do sufixo `AAAA` do `id` (coce, `NNN/AAAA`); quando `idDDCM` presente, registrar
também o ano do DDCM. Documentar como heurística no dicionário de dados.

## Outros endpoints observados (não usados no MVP)
- `GET /api/ensaio/instituicaoPesquisa`, `.../investigador`, `.../cid10` — busca/autocomplete.
- `GET /api/ensaio/download` (blob), `.../downloadPDF/?ddcmcoce=&coce=` — exportações.
