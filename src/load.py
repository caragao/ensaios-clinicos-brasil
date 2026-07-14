"""Cria o schema SQLite e carrega estudos, instituições e participações."""
from __future__ import annotations
import sqlite3

SCHEMA = """
DROP TABLE IF EXISTS participacao;
DROP TABLE IF EXISTS estudo;
DROP TABLE IF EXISTS instituicao;

CREATE TABLE estudo (
    coce TEXT PRIMARY KEY,
    ddcmcoce TEXT,
    numero_processo TEXT,
    ano INTEGER,
    patrocinador TEXT,
    cnpj_patrocinador TEXT,
    medicamento TEXT,
    classe_terapeutica TEXT,
    fase TEXT,
    situacao TEXT,
    titulo TEXT,
    tipo_estudo TEXT,
    tipo_medicamento TEXT,
    cid10 TEXT
);

CREATE TABLE instituicao (
    inst_key TEXT PRIMARY KEY,
    nome TEXT,
    cnes TEXT,
    cnpj TEXT,
    uf TEXT,
    uf_nome TEXT,
    municipio TEXT,
    codigo_municipio TEXT,
    natureza_juridica_cod TEXT,
    natureza_juridica_desc TEXT,
    esfera_administrativa TEXT,
    latitude REAL,
    longitude REAL,
    cnes_nome_razao TEXT,
    cnes_nome_fantasia TEXT,
    match_cnes INTEGER
);

CREATE TABLE participacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coce TEXT REFERENCES estudo(coce),
    inst_key TEXT REFERENCES instituicao(inst_key),
    ano INTEGER,
    num_pacientes INTEGER,
    investigadores TEXT
);

CREATE INDEX idx_estudo_ano ON estudo(ano);
CREATE INDEX idx_estudo_fase ON estudo(fase);
CREATE INDEX idx_estudo_situacao ON estudo(situacao);
CREATE INDEX idx_estudo_classe ON estudo(classe_terapeutica);
CREATE INDEX idx_inst_uf ON instituicao(uf);
CREATE INDEX idx_part_coce ON participacao(coce);
CREATE INDEX idx_part_inst ON participacao(inst_key);
"""


def load(sqlite_path: str, data: dict):
    conn = sqlite3.connect(sqlite_path)
    try:
        conn.executescript(SCHEMA)
        conn.executemany(
            """INSERT INTO estudo (coce,ddcmcoce,numero_processo,ano,patrocinador,cnpj_patrocinador,
               medicamento,classe_terapeutica,fase,situacao,titulo,tipo_estudo,tipo_medicamento,cid10)
               VALUES (:coce,:ddcmcoce,:numero_processo,:ano,:patrocinador,:cnpj_patrocinador,
               :medicamento,:classe_terapeutica,:fase,:situacao,:titulo,:tipo_estudo,:tipo_medicamento,:cid10)""",
            data["estudos"],
        )
        conn.executemany(
            """INSERT INTO instituicao (inst_key,nome,cnes,cnpj,uf,uf_nome,municipio,codigo_municipio,
               natureza_juridica_cod,natureza_juridica_desc,esfera_administrativa,latitude,longitude,
               cnes_nome_razao,cnes_nome_fantasia,match_cnes)
               VALUES (:inst_key,:nome,:cnes,:cnpj,:uf,:uf_nome,:municipio,:codigo_municipio,
               :natureza_juridica_cod,:natureza_juridica_desc,:esfera_administrativa,:latitude,:longitude,
               :cnes_nome_razao,:cnes_nome_fantasia,:match_cnes)""",
            [{**i, "match_cnes": 1 if i.get("match_cnes") else 0} for i in data["instituicoes"]],
        )
        conn.executemany(
            """INSERT INTO participacao (coce,inst_key,ano,num_pacientes,investigadores)
               VALUES (:coce,:inst_key,:ano,:num_pacientes,:investigadores)""",
            data["participacoes"],
        )
        conn.commit()
        n = lambda t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"[load] estudo={n('estudo')} instituicao={n('instituicao')} participacao={n('participacao')}")
    finally:
        conn.close()
