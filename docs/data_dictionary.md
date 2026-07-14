# Dicionário de dados

## Tabela `estudo` (1 linha por estudo / coce)
| coluna | origem | descrição |
|---|---|---|
| `coce` | ANVISA `id` | id do estudo `NNN/AAAA` (PK) |
| `ddcmcoce` | ANVISA `idDDCM` | id do DDCM (pode ser null) |
| `numero_processo` | ANVISA `numeroProcesso` | nº do processo ANVISA |
| `ano` | derivado | **DDCM-Ano**: sufixo `AAAA` de `idDDCM`; fallback para `coce` |
| `patrocinador` | ANVISA `empresa` | patrocinador do estudo |
| `cnpj_patrocinador` | ANVISA `cnpj` | CNPJ do patrocinador |
| `medicamento` | ANVISA `nomeProduto` | medicamento experimental |
| `classe_terapeutica` | ANVISA `classeTerapeutica` | classe terapêutica |
| `fase` | ANVISA `faseEstudo` | IV, III/IV, ... |
| `situacao` | ANVISA `situacao` | situação do estudo |
| `titulo` | ANVISA `motivoPesquisa` | título/descrição |
| `tipo_estudo` | ANVISA `tipoEstudo` | ex.: possui cooperação estrangeira |
| `tipo_medicamento` | ANVISA `tipoMedicamento` | ex.: sintético/semissintético |
| `cid10` | ANVISA `cid10` | código + descrição CID-10 |

## Tabela `instituicao` (1 linha por instituição única)
| coluna | origem | descrição |
|---|---|---|
| `inst_key` | derivado | `cnes:<x>` / `cnpj:<x>` / `nome:<NOME>` (PK) |
| `nome` | ANVISA `instituto` | nome do centro |
| `cnes` | ANVISA `cnes` | código CNES |
| `cnpj` | ANVISA/CNES | CNPJ |
| `uf`, `uf_nome` | CNES `codigo_uf` | UF (sigla/nome) |
| `municipio`, `codigo_municipio` | CNES + IBGE | município |
| `natureza_juridica_cod` | CNES | código CONCLA |
| `natureza_juridica_desc` | ref CONCLA | descrição da natureza jurídica |
| `esfera_administrativa` | CNES | Federal/Estadual/Municipal/Privada |
| `latitude`, `longitude` | CNES | geolocalização |
| `cnes_nome_razao`, `cnes_nome_fantasia` | CNES | nomes oficiais |
| `match_cnes` | derivado | 1 se enriquecido pelo CNES, 0 caso contrário |

## Tabela `participacao` (N:N estudo × instituição)
| coluna | origem | descrição |
|---|---|---|
| `coce` | FK estudo | |
| `inst_key` | FK instituição | |
| `ano` | derivado | ano do estudo |
| `num_pacientes` | ANVISA `numeroPacientes` | nº de pacientes do centro naquele estudo |
| `investigadores` | ANVISA `investigadores[].nome` | investigadores (separados por `;`) |

## Regras de negócio
- **Ano (DDCM-Ano)**: derivado do `idDDCM` (ano do DDCM), com fallback para o `coce`; estudos fora
  de `[ano_min, ano_max]` (config) são descartados. Como o regime de DDCM começou em 2015, estudos
  antigos sem DDCM (idDDCM nulo) tendem a ficar fora da janela 2015–2025.
- **Dedup de instituição**: prioridade CNES > CNPJ > nome (uppercase).
- **Enriquecimento**: só instituições com CNES válido; demais ficam com `match_cnes=0`.
- **Pacientes agregados**: soma de `num_pacientes` das participações (pode contar o mesmo paciente
  em estudos distintos — é volume de participação, não pacientes únicos).
