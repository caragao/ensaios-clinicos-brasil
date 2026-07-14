"""Exporta o dataset do SQLite para o dashboard estático (JS embutido, funciona em file://)."""
from __future__ import annotations
import json
import os
import sqlite3


def _rows(conn, sql):
    conn.row_factory = sqlite3.Row
    return [dict(r) for r in conn.execute(sql).fetchall()]


def export(sqlite_path: str, dashboard_data_dir: str):
    conn = sqlite3.connect(sqlite_path)
    try:
        estudos = _rows(conn, "SELECT * FROM estudo")
        instituicoes = _rows(conn, "SELECT * FROM instituicao")
        participacoes = _rows(conn, """
            SELECT p.coce, p.inst_key, p.ano, p.num_pacientes, p.investigadores,
                   e.fase, e.situacao, e.classe_terapeutica, e.patrocinador
              FROM participacao p JOIN estudo e ON e.coce = p.coce
        """)
    finally:
        conn.close()

    dataset = {
        "meta": {
            "n_estudos": len(estudos),
            "n_instituicoes": len(instituicoes),
            "n_participacoes": len(participacoes),
        },
        "estudos": estudos,
        "instituicoes": instituicoes,
        "participacoes": participacoes,
    }

    os.makedirs(dashboard_data_dir, exist_ok=True)
    # JSON puro (referência / uso externo)
    with open(os.path.join(dashboard_data_dir, "dataset.json"), "w", encoding="utf-8") as fh:
        json.dump(dataset, fh, ensure_ascii=False)
    # JS embutido: permite abrir o index.html direto do disco (sem servidor)
    with open(os.path.join(dashboard_data_dir, "dataset.js"), "w", encoding="utf-8") as fh:
        fh.write("window.DATASET = ")
        json.dump(dataset, fh, ensure_ascii=False)
        fh.write(";")
    print(f"[aggregate] dataset exportado ({len(estudos)} estudos) em {dashboard_data_dir}")
