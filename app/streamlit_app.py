"""Dashboard exploratório (Streamlit) sobre a base SQLite de ensaios clínicos.

Uso:  streamlit run app/streamlit_app.py
"""
from __future__ import annotations
import os
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "processed", "ensaios.sqlite")

st.set_page_config(page_title="Ensaios Clínicos no Brasil", layout="wide")


@st.cache_data(show_spinner=False)
def load():
    con = sqlite3.connect(DB)
    est = pd.read_sql_query("SELECT * FROM estudo", con)
    inst = pd.read_sql_query("SELECT * FROM instituicao", con)
    part = pd.read_sql_query("SELECT * FROM participacao", con)
    con.close()
    part = part.merge(inst[["inst_key", "nome", "uf", "municipio", "natureza_juridica_desc"]],
                      on="inst_key", how="left")
    part = part.merge(est[["coce", "fase", "situacao", "classe_terapeutica", "patrocinador", "titulo", "medicamento"]],
                      on="coce", how="left")
    return est, inst, part


if not os.path.exists(DB):
    st.error("Base não encontrada. Rode primeiro:  python -m src.pipeline")
    st.stop()

est, inst, part = load()
st.title("Ensaios Clínicos no Brasil")
st.caption(f"{len(est)} estudos · {len(inst)} instituições · {int(part['num_pacientes'].sum()):,} pacientes (soma)")

# ---- Filtros ----
with st.sidebar:
    st.header("Filtros")
    def opts(series):
        return sorted([v for v in series.dropna().unique() if v != ""])
    f_ano = st.multiselect("Ano", opts(est["ano"]))
    f_sit = st.multiselect("Situação", opts(est["situacao"]))
    f_fase = st.multiselect("Fase", opts(est["fase"]))
    f_classe = st.multiselect("Classe Terapêutica", opts(est["classe_terapeutica"]))
    f_patroc = st.multiselect("Patrocinador", opts(est["patrocinador"]))
    f_uf = st.multiselect("UF da Instituição", opts(inst["uf"]))
    f_inst = st.text_input("Instituição (busca)")

# Aplica filtros de estudo
e = est.copy()
if f_ano: e = e[e["ano"].isin(f_ano)]
if f_sit: e = e[e["situacao"].isin(f_sit)]
if f_fase: e = e[e["fase"].isin(f_fase)]
if f_classe: e = e[e["classe_terapeutica"].isin(f_classe)]
if f_patroc: e = e[e["patrocinador"].isin(f_patroc)]

p = part[part["coce"].isin(e["coce"])]
if f_uf: p = p[p["uf"].isin(f_uf)]
if f_inst: p = p[p["nome"].str.contains(f_inst, case=False, na=False)]
if f_uf or f_inst:
    e = e[e["coce"].isin(p["coce"])]

# ---- KPIs ----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Estudos", len(e))
c2.metric("Instituições", p["inst_key"].nunique())
c3.metric("Pacientes (soma)", f"{int(p['num_pacientes'].sum()):,}")
c4.metric("Patrocinadores", e["patrocinador"].nunique())

# ---- Gráficos ----
g1, g2 = st.columns(2)
with g1:
    st.subheader("Evolução — estudos por ano")
    ano = e.dropna(subset=["ano"]).groupby("ano").size().reset_index(name="estudos")
    if len(ano):
        st.plotly_chart(px.line(ano, x="ano", y="estudos", markers=True), use_container_width=True)
with g2:
    st.subheader("Por situação")
    sit = e.groupby("situacao").size().reset_index(name="n").sort_values("n")
    if len(sit):
        st.plotly_chart(px.bar(sit, x="n", y="situacao", orientation="h"), use_container_width=True)

g3, g4 = st.columns(2)
with g3:
    st.subheader("Top classes terapêuticas")
    cl = e.groupby("classe_terapeutica").size().reset_index(name="n").sort_values("n").tail(10)
    if len(cl):
        st.plotly_chart(px.bar(cl, x="n", y="classe_terapeutica", orientation="h"), use_container_width=True)
with g4:
    st.subheader("Distribuição por UF")
    uf = p.groupby("uf").size().reset_index(name="n").sort_values("n", ascending=False)
    if len(uf):
        st.plotly_chart(px.bar(uf, x="uf", y="n"), use_container_width=True)

# ---- Tabela de instituições + drill-down ----
st.subheader("Instituições de pesquisa")
agg = (p.groupby("inst_key")
        .agg(estudos=("coce", "nunique"), pacientes=("num_pacientes", "sum"))
        .reset_index()
        .merge(inst, on="inst_key", how="left")
        .sort_values("estudos", ascending=False))
tabela = agg[["nome", "uf", "municipio", "natureza_juridica_desc", "estudos", "pacientes"]]
st.dataframe(tabela, use_container_width=True, hide_index=True)

st.subheader("Detalhe da instituição")
if len(agg):
    escolha = st.selectbox("Selecione uma instituição", agg["nome"].tolist())
    row = agg[agg["nome"] == escolha].iloc[0]
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("UF", row["uf"] or "—")
    d2.metric("Município", row["municipio"] or "—")
    d3.metric("Estudos", int(row["estudos"]))
    d4.metric("Pacientes (soma)", f"{int(row['pacientes']):,}")
    st.write(f"**Natureza Jurídica:** {row['natureza_juridica_desc'] or '—'}  ·  "
             f"**CNES:** {row['cnes'] or '—'}  ·  **CNPJ:** {row['cnpj'] or '—'}")
    det = (part[part["inst_key"] == row["inst_key"]]
           [["ano", "titulo", "patrocinador", "fase", "situacao", "num_pacientes"]]
           .sort_values("ano", ascending=False)
           .rename(columns={"titulo": "estudo", "num_pacientes": "pacientes"}))
    st.dataframe(det, use_container_width=True, hide_index=True)
