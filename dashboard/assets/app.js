/* Dashboard de Ensaios Clínicos — vanilla JS, sem dependências externas. */
(function () {
  "use strict";
  let D, byCoce, partByInst, instByKey;
  const F = { ano: "", sit: "", fase: "", classe: "", patroc: "", uf: "", natureza: "", inst: "" };
  let instSort = { k: "n_estudos", dir: -1 };
  let estSort = { k: "ano", dir: -1 };

  window.boot = function () {
    D = window.DATASET;
    if (!D) return;
    document.getElementById("empty").style.display = "none";
    document.getElementById("app").style.display = "block";
    document.getElementById("subtitle").textContent =
      `${D.meta.n_estudos} estudos · ${D.meta.n_instituicoes} instituições`;

    byCoce = {}; D.estudos.forEach(e => byCoce[e.coce] = e);
    instByKey = {}; D.instituicoes.forEach(i => instByKey[i.inst_key] = i);
    partByInst = {};
    D.participacoes.forEach(p => { (partByInst[p.inst_key] = partByInst[p.inst_key] || []).push(p); });

    buildFilterOptions();
    wireEvents();
    render();
  };

  const uniqSorted = (arr) => [...new Set(arr.filter(v => v != null && v !== ""))].sort((a, b) => (""+a).localeCompare(""+b, "pt"));

  function buildFilterOptions() {
    fill("f_ano", uniqSorted(D.estudos.map(e => e.ano)));
    fill("f_sit", uniqSorted(D.estudos.map(e => e.situacao)));
    fill("f_fase", uniqSorted(D.estudos.map(e => e.fase)));
    fill("f_classe", uniqSorted(D.estudos.map(e => e.classe_terapeutica)));
    fill("f_patroc", uniqSorted(D.estudos.map(e => e.patrocinador)));
    fill("f_uf", uniqSorted(D.instituicoes.map(i => i.uf)));
    fill("f_natureza", uniqSorted(D.instituicoes.map(i => i.natureza_grupo)));
  }
  function fill(id, vals) {
    const s = document.getElementById(id);
    s.innerHTML = '<option value="">Todos</option>' + vals.map(v => `<option>${esc(v)}</option>`).join("");
  }

  function wireEvents() {
    const map = { f_ano: "ano", f_sit: "sit", f_fase: "fase", f_classe: "classe", f_patroc: "patroc", f_uf: "uf", f_natureza: "natureza" };
    Object.entries(map).forEach(([id, key]) => {
      document.getElementById(id).addEventListener("change", e => { F[key] = e.target.value; render(); });
    });
    document.getElementById("f_inst").addEventListener("input", e => { F.inst = e.target.value.toLowerCase(); render(); });
    document.getElementById("btn_clear").addEventListener("click", () => {
      Object.keys(F).forEach(k => F[k] = "");
      document.querySelectorAll("#filters select").forEach(s => s.value = "");
      document.getElementById("f_inst").value = "";
      render();
    });
    document.getElementById("modal_close").addEventListener("click", closeModal);
    document.getElementById("overlay").addEventListener("click", e => { if (e.target.id === "overlay") closeModal(); });
    document.querySelectorAll("#t_inst th").forEach(th => th.addEventListener("click", () => {
      const k = th.dataset.k; instSort.dir = instSort.k === k ? -instSort.dir : -1; instSort.k = k; render();
    }));
    document.querySelectorAll("#t_estudos th").forEach(th => th.addEventListener("click", () => {
      const k = th.dataset.k; estSort.dir = estSort.k === k ? -estSort.dir : -1; estSort.k = k; render();
    }));
  }

  // Um estudo passa nos filtros de estudo? (ano/sit/fase/classe/patroc)
  function estudoMatch(e) {
    if (F.ano && String(e.ano) !== F.ano) return false;
    if (F.sit && e.situacao !== F.sit) return false;
    if (F.fase && e.fase !== F.fase) return false;
    if (F.classe && e.classe_terapeutica !== F.classe) return false;
    if (F.patroc && e.patrocinador !== F.patroc) return false;
    return true;
  }
  // Filtro de instituição (uf/busca) — aplicado às participações
  function instMatch(inst) {
    if (!inst) return false;
    if (F.uf && inst.uf !== F.uf) return false;
    if (F.natureza && inst.natureza_grupo !== F.natureza) return false;
    if (F.inst && !((inst.nome || "").toLowerCase().includes(F.inst))) return false;
    return true;
  }
  const instFilterActive = () => F.uf || F.natureza || F.inst;

  function computeView() {
    // participações que satisfazem estudo + instituição
    const parts = D.participacoes.filter(p => {
      const e = byCoce[p.coce]; if (!e || !estudoMatch(e)) return false;
      if (instFilterActive() && !instMatch(instByKey[p.inst_key])) return false;
      return true;
    });
    // estudos visíveis = os que têm ao menos uma participação válida (ou todos, se sem filtro de inst)
    let estudos;
    if (instFilterActive()) {
      const cs = new Set(parts.map(p => p.coce));
      estudos = D.estudos.filter(e => cs.has(e.coce));
    } else {
      estudos = D.estudos.filter(estudoMatch);
    }
    return { parts, estudos };
  }

  function render() {
    const { parts, estudos } = computeView();
    renderKPIs(estudos, parts);
    renderAno(estudos);
    renderCat("c_sit", count(estudos, "situacao"));
    renderCat("c_classe", count(estudos, "classe_terapeutica"), 8);
    renderCat("c_patroc", count(estudos, "patrocinador"), 8);
    renderCat("c_uf", countPartUF(parts));
    renderInstTable(parts);
    renderEstudoTable(estudos, parts);
  }

  function renderKPIs(estudos, parts) {
    const pacientes = parts.reduce((s, p) => s + (p.num_pacientes || 0), 0);
    const insts = new Set(parts.map(p => p.inst_key)).size;
    const patrocs = new Set(estudos.map(e => e.patrocinador).filter(Boolean)).size;
    const kpis = [
      ["Estudos", estudos.length], ["Instituições", insts],
      ["Pacientes (soma)", pacientes.toLocaleString("pt-BR")], ["Patrocinadores", patrocs],
    ];
    document.getElementById("kpis").innerHTML = kpis.map(([l, v]) =>
      `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join("");
  }

  function count(rows, key) {
    const m = {};
    rows.forEach(r => { const k = r[key] || "—"; m[k] = (m[k] || 0) + 1; });
    return Object.entries(m).sort((a, b) => b[1] - a[1]);
  }
  function countPartUF(parts) {
    const m = {};
    parts.forEach(p => { const uf = (instByKey[p.inst_key] || {}).uf || "—"; m[uf] = (m[uf] || 0) + 1; });
    return Object.entries(m).sort((a, b) => b[1] - a[1]);
  }

  function renderAno(estudos) {
    const m = {};
    estudos.forEach(e => { if (e.ano) m[e.ano] = (m[e.ano] || 0) + 1; });
    const anos = Object.keys(m).map(Number).sort((a, b) => a - b);
    if (!anos.length) { document.getElementById("c_ano").innerHTML = '<div class="muted">Sem dados.</div>'; return; }
    const w = 900, h = 180, pad = 30;
    const max = Math.max(...anos.map(a => m[a]));
    const x = i => pad + i * (w - 2 * pad) / Math.max(1, anos.length - 1);
    const y = v => h - pad - v * (h - 2 * pad) / max;
    const pts = anos.map((a, i) => `${x(i)},${y(m[a])}`).join(" ");
    let svg = `<svg viewBox="0 0 ${w} ${h}" width="100%" preserveAspectRatio="none" style="max-height:200px">`;
    svg += `<polyline fill="none" stroke="#38bdf8" stroke-width="2.5" points="${pts}"/>`;
    anos.forEach((a, i) => {
      svg += `<circle cx="${x(i)}" cy="${y(m[a])}" r="3" fill="#818cf8"/>`;
      svg += `<text x="${x(i)}" y="${h - 8}" text-anchor="middle">${a}</text>`;
      svg += `<text x="${x(i)}" y="${y(m[a]) - 8}" text-anchor="middle" fill="#e2e8f0">${m[a]}</text>`;
    });
    svg += `</svg>`;
    document.getElementById("c_ano").innerHTML = svg;
  }

  function renderCat(id, entries, limit) {
    const rows = (limit ? entries.slice(0, limit) : entries);
    if (!rows.length) { document.getElementById(id).innerHTML = '<div class="muted">Sem dados.</div>'; return; }
    const max = Math.max(...rows.map(r => r[1]));
    document.getElementById(id).innerHTML = rows.map(([lab, v]) =>
      `<div class="bar-row"><div class="lab" title="${esc(lab)}">${esc(lab)}</div>
       <div class="track"><div class="fill" style="width:${(v / max * 100).toFixed(1)}%"></div></div>
       <div class="val">${v}</div></div>`).join("");
  }

  function renderInstTable(parts) {
    // agrega participações por instituição
    const agg = {};
    parts.forEach(p => {
      const a = agg[p.inst_key] || (agg[p.inst_key] = { estudos: new Set(), pac: 0 });
      a.estudos.add(p.coce); a.pac += (p.num_pacientes || 0);
    });
    let rows = Object.entries(agg).map(([k, a]) => {
      const i = instByKey[k] || {};
      return { inst_key: k, nome: i.nome || "—", uf: i.uf || "—", municipio: i.municipio || "—",
               natureza_grupo: i.natureza_grupo || "—",
               n_estudos: a.estudos.size, n_pacientes: a.pac };
    });
    rows.sort(cmp(instSort));
    const tb = document.querySelector("#t_inst tbody");
    tb.innerHTML = rows.map(r =>
      `<tr class="clickable" data-k="${esc(r.inst_key)}">
        <td>${esc(r.nome)}</td><td>${esc(r.uf)}</td><td>${esc(r.municipio)}</td>
        <td>${esc(r.natureza_grupo)}</td><td>${r.n_estudos}</td><td>${r.n_pacientes.toLocaleString("pt-BR")}</td>
      </tr>`).join("") || `<tr><td colspan="6" class="muted">Nenhuma instituição.</td></tr>`;
    tb.querySelectorAll("tr.clickable").forEach(tr =>
      tr.addEventListener("click", () => openModal(tr.dataset.k)));
  }

  function renderEstudoTable(estudos, parts) {
    const pacByCoce = {}, instByCoceCount = {};
    parts.forEach(p => {
      pacByCoce[p.coce] = (pacByCoce[p.coce] || 0) + (p.num_pacientes || 0);
      (instByCoceCount[p.coce] = instByCoceCount[p.coce] || new Set()).add(p.inst_key);
    });
    let rows = estudos.map(e => ({ ...e, n_inst: (instByCoceCount[e.coce] || new Set()).size, n_pac: pacByCoce[e.coce] || 0 }));
    rows.sort(cmp(estSort));
    document.querySelector("#t_estudos tbody").innerHTML = rows.map(e =>
      `<tr><td>${e.ano ?? "—"}</td><td>${esc(e.medicamento)}</td><td>${esc(e.classe_terapeutica)}</td>
       <td><span class="tag">${esc(e.fase)}</span></td><td>${esc(e.situacao)}</td><td>${esc(e.patrocinador)}</td>
       <td>${e.n_inst}</td><td>${e.n_pac.toLocaleString("pt-BR")}</td></tr>`).join("")
       || `<tr><td colspan="8" class="muted">Nenhum estudo.</td></tr>`;
  }

  function openModal(instKey) {
    const i = instByKey[instKey] || {};
    document.getElementById("m_nome").textContent = i.nome || "—";
    document.getElementById("m_sub").textContent =
      [i.cnes_nome_razao, i.cnes ? "CNES " + i.cnes : null, i.cnpj ? "CNPJ " + i.cnpj : null].filter(Boolean).join(" · ");
    const parts = partByInst[instKey] || [];
    const totalPac = parts.reduce((s, p) => s + (p.num_pacientes || 0), 0);
    const anos = parts.map(p => p.ano).filter(Boolean);
    const meta = [
      ["UF", i.uf || "—"], ["Município", i.municipio || "—"],
      ["Natureza (grupo)", i.natureza_grupo || "—"], ["Natureza Jurídica", i.natureza_juridica_desc || "—"],
      ["Esfera", i.esfera_administrativa || "—"],
      ["Estudos", new Set(parts.map(p => p.coce)).size], ["Pacientes (soma)", totalPac.toLocaleString("pt-BR")],
      ["Período", anos.length ? Math.min(...anos) + "–" + Math.max(...anos) : "—"],
    ];
    document.getElementById("m_meta").innerHTML = meta.map(([l, v]) =>
      `<div class="m"><div class="l">${l}</div><div class="v">${v}</div></div>`).join("");
    const rows = parts.map(p => ({ ...p, e: byCoce[p.coce] || {} }))
      .sort((a, b) => (b.ano || 0) - (a.ano || 0));
    document.querySelector("#m_estudos tbody").innerHTML = rows.map(p =>
      `<tr><td>${p.ano ?? "—"}</td><td title="${esc(p.e.titulo)}">${esc(trunc(p.e.titulo, 70))}</td>
       <td>${esc(p.e.patrocinador)}</td><td><span class="tag">${esc(p.e.fase)}</span></td>
       <td>${esc(p.e.situacao)}</td><td>${(p.num_pacientes || 0).toLocaleString("pt-BR")}</td></tr>`).join("")
       || `<tr><td colspan="6" class="muted">Sem estudos.</td></tr>`;
    document.getElementById("overlay").classList.add("open");
  }
  function closeModal() { document.getElementById("overlay").classList.remove("open"); }

  const cmp = (s) => (a, b) => {
    let x = a[s.k], y = b[s.k];
    if (typeof x === "number" && typeof y === "number") return (x - y) * s.dir;
    return String(x ?? "").localeCompare(String(y ?? ""), "pt") * s.dir;
  };
  function esc(s) { return (s == null ? "—" : String(s)).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
  function trunc(s, n) { s = s || ""; return s.length > n ? s.slice(0, n) + "…" : s; }
})();
