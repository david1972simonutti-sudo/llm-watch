"""
render.py — Génère UN seul artefact HTML autonome à deux onglets :
  • "Compte-rendu"   : le CR de la semaine (titre "LLM analyse du DD/MM/YYYY",
       Partie 1 tableaux majeures+radar, Partie 2 entrants).
  • "État des lieux" : le tableau de référence (photo du marché à date).

Navigation interne (JavaScript), aucun lien inter-fichiers : fonctionne au
double-clic ET dans l'aperçu intégré. Ouverture directe sur le tableau via #etat.

  output/latest.html + output/archive/CR-<week>.html
"""

import html
import datetime
from pathlib import Path

import referential as REF

OUTPUT_DIR = Path("output")
RADAR_MAX = 5

_CSS = """
:root{
  --bg:#F6F7F9; --surface:#FFFFFF; --ink:#151A22; --ink-2:#4C5666;
  --muted:#8B94A3; --line:#E4E8EE; --line-strong:#CDD4DE;
  --majeur:#B45309; --radar:#1F5FBF; --entrant:#6D28D9; --entrant-bg:#F3EEFD; --entrant-line:#D6C2F5;
  --down:#1A7F4B; --up:#B4232A; --stable:#8B94A3;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; --radius:12px;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.55;
  -webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
.page{max-width:1000px;margin:0 auto;padding:36px 24px 72px}
a{color:var(--radar);text-decoration:none} a:hover{text-decoration:underline}
.masthead{border-bottom:2px solid var(--ink);padding-bottom:14px;
  display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap}
.brand{font-size:13px;font-weight:700;letter-spacing:.14em;text-transform:uppercase}
.brand span{color:var(--majeur)}
.issue{font-size:12px;color:var(--muted);letter-spacing:.04em}
.eyebrow{font-size:11px;font-weight:600;letter-spacing:.13em;text-transform:uppercase;color:var(--muted)}
.title{font-size:30px;font-weight:700;letter-spacing:-.02em;margin:20px 0 4px}
.tabs{display:flex;gap:4px;margin-top:16px;border-bottom:1px solid var(--line-strong)}
.tab{appearance:none;background:none;border:none;cursor:pointer;font-family:inherit;
  font-size:13px;font-weight:600;color:var(--muted);padding:10px 16px;border-radius:8px 8px 0 0;
  border-bottom:2px solid transparent;margin-bottom:-1px}
.tab:hover{color:var(--ink-2)}
.tab.active{color:var(--ink);border-bottom-color:var(--majeur);background:var(--surface)}
.view{display:none} .view.active{display:block}
.hero{padding:16px 0 26px;border-bottom:1px solid var(--line)}
.verdict{font-size:19px;line-height:1.4;font-weight:600;letter-spacing:-.01em;max-width:62ch;margin:8px 0 18px}
.stats{display:flex;gap:26px;flex-wrap:wrap}
.stat{display:flex;flex-direction:column;gap:1px}
.stat .n{font-size:21px;font-weight:700;letter-spacing:-.02em}
.stat .l{font-size:10.5px;color:var(--muted);letter-spacing:.05em;text-transform:uppercase}
.stat.hi .n{color:var(--majeur)}
.part{margin-top:36px}
.part-head{display:flex;align-items:baseline;gap:10px;border-bottom:2px solid var(--ink);padding-bottom:8px}
.part-head h2{font-size:17px;font-weight:700;letter-spacing:-.01em}
.part-head .sub{font-size:12px;color:var(--muted);margin-left:auto}
.subhead{font-size:12px;font-weight:700;letter-spacing:.02em;color:var(--ink-2);
  text-transform:uppercase;margin:20px 0 8px;display:flex;align-items:center;gap:8px}
.subhead .c{font-weight:500;color:var(--muted);text-transform:none;letter-spacing:0}
table{width:100%;border-collapse:collapse;font-size:13px;background:var(--surface);
  border:1px solid var(--line);border-radius:var(--radius);overflow:hidden}
thead th{padding:9px 12px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.06em;
  color:var(--muted);font-weight:700;background:var(--bg);border-bottom:1px solid var(--line-strong)}
tbody td{padding:11px 12px;vertical-align:top;color:var(--ink-2);line-height:1.5;border-bottom:1px solid var(--line)}
tbody tr:last-child td{border-bottom:none}
.rel{display:flex;flex-direction:column;gap:2px}
.rel-h{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.dot{width:9px;height:9px;border-radius:50%;flex:none}
.dot.h{background:var(--majeur)} .dot.m{background:var(--radar)} .dot.l{background:var(--stable)}
.rel-t{font-weight:650;color:var(--ink)} .rel-p{font-size:11.5px;color:var(--muted)} .rel-d{font-size:11px;color:var(--muted)}
.bench{font-size:11px;font-style:italic;color:var(--muted);margin-top:5px;border-top:1px dashed var(--line);padding-top:5px}
.cost-down{color:var(--down);font-weight:600}.cost-up{color:var(--up);font-weight:600}.cost-stable{color:var(--stable);font-weight:600}
.src{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.col-rel{width:30%}.col-cost{width:14%}.col-src{width:9%}
.calm{background:var(--surface);border:1px dashed var(--line-strong);border-radius:var(--radius);padding:16px;font-size:13px;color:var(--ink-2)}
.entrant{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--entrant);
  border-radius:var(--radius);padding:16px 18px;margin-bottom:12px}
.entrant-top{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-bottom:8px}
.tag{font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;padding:2px 7px;border-radius:5px;
  background:var(--entrant-bg);color:var(--entrant);border:1px solid var(--entrant-line)}
.entrant-name{font-size:16px;font-weight:650} .entrant-org{font-size:12px;color:var(--muted)}
.crit{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
.crit span{font-size:10.5px;background:var(--bg);border:1px solid var(--line-strong);border-radius:5px;padding:2px 8px;color:var(--ink-2)}
.dims{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px}
.dim{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:9px 11px}
.dim .dl{font-size:9.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:3px}
.dim .dt{font-size:12.5px;color:var(--ink-2)}
.pn{font-weight:650;color:var(--ink)}.pm{font-size:11.5px;color:var(--muted);margin-top:2px}
.chips{display:flex;gap:4px;flex-wrap:wrap}
.chip{font-size:10px;padding:2px 6px;border-radius:4px;background:var(--bg);border:1px solid var(--line-strong);color:var(--ink-2)}
.lead{font-size:15px;color:var(--ink-2);max-width:64ch;margin:14px 0 20px;line-height:1.5}
.foot{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);font-size:11px;color:var(--muted);line-height:1.7}
/* badge brique */
.brk{display:inline-block;font-size:9.5px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;
  padding:1px 6px;border-radius:4px;background:var(--radar-bg,#EEF3FC);color:var(--radar);border:1px solid #cfe0f7;margin-top:3px}
.active-bar{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin:14px 0 4px}
.active-bar .lab{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;font-weight:700}
.active-chip{font-size:11px;font-weight:600;padding:3px 9px;border-radius:20px;background:var(--majeur-bg,#FDF6EC);
  color:var(--majeur);border:1px solid #ecd3a8}
/* schéma de flux UX */
.flow-wrap{margin-top:8px}
.flow-band-label{font-size:10.5px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin:22px 0 8px}
.flow-amont{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:6px}
.flow-row{display:flex;align-items:stretch;gap:6px;flex-wrap:wrap}
.node{background:var(--surface);border:1px solid var(--line-strong);border-radius:10px;padding:10px 12px;
  min-width:120px;flex:1 1 120px;position:relative}
.node.amont{border-left:3px solid var(--entrant)}
.node.flux{border-left:3px solid var(--radar)}
.node.endpoint{background:var(--ink);color:#fff;border:none;flex:0 0 auto;min-width:78px;display:flex;
  align-items:center;justify-content:center;font-weight:700;font-size:13px}
.node.model{border-left:3px solid var(--majeur);background:var(--majeur-bg,#FDF6EC)}
.node.on{box-shadow:0 0 0 2px var(--majeur);border-left-color:var(--majeur)}
.node .nk{font-size:9px;font-weight:700;color:var(--muted);letter-spacing:.06em}
.node .nt{font-size:12.5px;font-weight:650;color:var(--ink);margin:2px 0 3px;line-height:1.25}
.node .nr{font-size:10.5px;color:var(--ink-2);line-height:1.35}
.node .non{position:absolute;top:-8px;right:-6px;font-size:8.5px;font-weight:700;background:var(--majeur);color:#fff;
  padding:1px 6px;border-radius:20px;letter-spacing:.03em}
.arrow{align-self:center;color:var(--muted);font-size:16px;flex:0 0 auto}
.transverse-band{margin-top:10px;background:var(--bg);border:1px dashed var(--line-strong);border-radius:10px;padding:12px}
.control-band{position:relative;margin-top:6px;background:var(--entrant-bg,#F3EEFD);border:1px solid var(--entrant-line,#D6C2F5);
  border-left:3px solid var(--entrant);border-radius:10px;padding:12px 14px}
.control-band.on{box-shadow:0 0 0 2px var(--entrant)}
.control-band .nk{font-size:9px;font-weight:700;color:var(--entrant);letter-spacing:.06em}
.control-band .nt{font-size:13.5px;font-weight:650;color:var(--ink);margin:2px 0 3px}
.control-band .nr{font-size:11.5px;color:var(--ink-2);line-height:1.4}
.control-band .non{position:absolute;top:-8px;right:-6px;font-size:8.5px;font-weight:700;background:var(--entrant);color:#fff;padding:1px 6px;border-radius:20px}
.transverse-band .trow{display:flex;gap:10px;flex-wrap:wrap}
.tcell{flex:1 1 160px;font-size:11.5px;color:var(--ink-2)}
.tcell b{color:var(--ink);font-size:12px}
/* trajectoires */
.traj{margin-top:10px}
.traj-item{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-bottom:8px}
.traj-h{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.traj-h .tl{font-weight:650;font-size:13.5px}
.traj-h .grp{font-size:9.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);border:1px solid var(--line-strong);border-radius:4px;padding:1px 6px}
.traj-xy{font-size:12.5px;color:var(--ink-2);margin:6px 0}
.traj-xy .x{color:var(--muted)} .traj-xy .to{color:var(--majeur);font-weight:600}
.traj-sub{display:flex;gap:5px;flex-wrap:wrap;margin-top:4px}
.traj-anchor{font-size:10.5px;color:var(--muted);margin-top:6px;font-style:italic}
@media(max-width:720px){.dims{grid-template-columns:1fr}.page{padding:26px 16px 56px}
  .title{font-size:24px}table{font-size:12px}.table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
  .flow-row{flex-direction:column}.arrow{transform:rotate(90deg)}.node.endpoint{min-width:0}}
"""

_JS = """
(function(){
  function show(name){
    document.querySelectorAll('.view').forEach(function(v){v.classList.toggle('active',v.id===name);});
    document.querySelectorAll('.tab').forEach(function(t){t.classList.toggle('active',t.dataset.view===name);});
    try{ history.replaceState(null,'',name==='etat'?'#etat':'#cr'); }catch(e){/* origine sandboxée : on ignore */}
  }
  document.querySelectorAll('.tab').forEach(function(t){
    t.addEventListener('click',function(){show(t.dataset.view);});
  });
  var h;
  try{ h=(location.hash||'').slice(1); }catch(e){ h=''; }
  if(!h||!document.getElementById(h)) h='cr';
  show(h);
})();
"""


def _esc(s): return html.escape(str(s or ""))
def _cost_cls(d): return {"down": "cost-down", "up": "cost-up"}.get((d or "").lower(), "cost-stable")
def _dot(i): return {"high": "h", "medium": "m"}.get(i, "l")


def _release_row(it):
    bench = f"<div class=bench>Benchmark — {_esc(it['benchmark_note'])}</div>" if it.get("benchmark_note") else ""
    src = (f"<a class=src href='{_esc(it['source_url'])}' target=_blank rel=noopener>{_esc(it.get('source_type') or 'lien')} ↗</a>"
           if it.get("source_url") else "")
    brk = REF.brick_label(it.get("brique")) if it.get("brique") else ""
    brk_html = f"<span class=brk>{_esc(brk)}</span>" if brk else ""
    return f"""<tr>
      <td class=col-rel><div class=rel><div class=rel-h><span class='dot {_dot(it.get('impact'))}'></span>
        <span class=rel-t>{_esc(it.get('title') or it.get('name'))}</span></div>
        <div class=rel-p>{_esc(it.get('provider_name'))}</div><div class=rel-d>{_esc(it.get('published_date'))}</div>
        {brk_html}</div></td>
      <td>{_esc(it.get('problem_solved'))}{bench}</td>
      <td>{_esc(it.get('application_unlocked'))}</td>
      <td class=col-cost><span class={_cost_cls(it.get('cost_direction'))}>{_esc(it.get('cost_trend'))}</span></td>
      <td class=col-src>{src}</td></tr>"""


def _release_table(items):
    head = ("<thead><tr><th class=col-rel>Provider · Nouveauté</th><th>Problème résolu</th>"
            "<th>Usage métier débloqué</th><th class=col-cost>Coût</th><th class=col-src>Source</th></tr></thead>")
    return f"<div class=table-wrap><table>{head}<tbody>{''.join(_release_row(it) for it in items)}</tbody></table></div>"


def _entrant_block(e):
    v = e.get("validation_criteria", {}) or {}
    crit = []
    if v.get("publication"): crit.append(f"📄 {_esc(v['publication'])}")
    if v.get("funding"): crit.append(f"💰 {_esc(v['funding'])}")
    if v.get("benchmark_name"): crit.append(f"📊 {_esc(v['benchmark_name'])} : {_esc(v.get('benchmark_score'))}")
    if v.get("availability"): crit.append("✅ dispo")
    bench = f"<div class=bench>Benchmark — {_esc(e['benchmark_note'])}</div>" if e.get("benchmark_note") else ""
    src = f"<a class=src href='{_esc(e['source_url'])}' target=_blank rel=noopener>Source ↗</a>" if e.get("source_url") else ""
    return f"""<div class=entrant>
      <div class=entrant-top><span class=tag>Nouvel entrant</span>
        <span class=entrant-name>{_esc(e.get('name'))}</span>
        <span class=entrant-org>· {_esc(e.get('org'))}{(' · '+_esc(e.get('country'))) if e.get('country') else ''}</span></div>
      <div class=crit>{''.join(f'<span>{c}</span>' for c in crit)}</div>
      <div class=dims>
        <div class=dim><div class=dl>Ce qu'il apporte</div><div class=dt>{_esc(e.get('problem_solved'))}</div></div>
        <div class=dim><div class=dl>Usage débloqué</div><div class=dt>{_esc(e.get('application_unlocked'))}</div></div>
        <div class=dim><div class=dl>Positionnement</div><div class=dt>{_esc(e.get('positioning'))}</div></div>
        <div class=dim><div class=dl>Tendance coût</div><div class=dt>{_esc(e.get('cost_trend'))}</div></div></div>
      {bench}<div style='margin-top:8px'>{src}</div></div>"""


def _etat_table(ledger):
    snap = ledger.get("snapshot", {})
    provs = [p for p in snap if snap[p].get("kind") != "entrant"]
    entr = [p for p in snap if snap[p].get("kind") == "entrant"]
    rows = ""
    for pid in provs + entr:
        r = snap[pid]
        chips = "".join(f"<span class=chip>{_esc(t)}</span>" for t in r.get("tags", []))
        rows += (f"<tr><td><div class=pn>{_esc(r.get('provider_name'))}</div>"
                 f"<div class=pm>{_esc(r.get('flagship_model'))}</div></td>"
                 f"<td><div class=chips>{chips}</div><div class=pm style='margin-top:5px'>{_esc(r.get('specialization'))}</div></td>"
                 f"<td><span class={_cost_cls(r.get('cost_direction'))}>{_esc(r.get('cost_state'))}</span></td>"
                 f"<td>{_esc(r.get('signal'))}</td></tr>")
    if not rows:
        rows = "<tr><td colspan=4>État des lieux vide — lancez une première collecte.</td></tr>"
    return (f"<div class=table-wrap><table><thead><tr><th style='width:17%'>Provider</th>"
            f"<th style='width:22%'>Spécialisation</th><th style='width:14%'>Coût</th>"
            f"<th>Signal — état courant</th></tr></thead><tbody>{rows}</tbody></table></div>")


def _active_bar(active):
    if not active:
        return ""
    chips = "".join(f"<span class=active-chip>{_esc(REF.brick_label(k))}</span>" for k in active)
    return f"<div class=active-bar><span class=lab>Briques qui bougent cette semaine</span>{chips}</div>"


def _node(key, active, cls="flux"):
    b = REF.BRICKS[key]
    on = " on" if key in active else ""
    badge = "<span class=non>ACTIF</span>" if key in active else ""
    return (f"<div class='node {cls}{on}'>{badge}<div class=nk>{_esc(b['label'].split(' & ')[0].upper())}</div>"
            f"<div class=nt>{_esc(b['label'])}</div><div class=nr>{_esc(b['role'])}</div></div>")


def _schema_view(active):
    a = set(active or [])
    # amont : fabrication du modèle
    amont = "".join(_node(k, a, "amont") for k in ["architecture", "alignement"])
    # flux d'exécution, ordre UX : prompt -> prompting -> rag -> [modèle] -> raisonnement -> inference -> résultat
    # (l'agentique n'est PLUS une station : c'est une couche de contrôle transverse, cf. bande dédiée)
    arrow = "<span class=arrow>→</span>"
    model = "<div class='node model'><div class=nk>LE MODÈLE</div><div class=nt>Modèle déployé</div><div class=nr>issu des deux briques amont</div></div>"
    parts = [
        "<div class='node endpoint'>Prompt</div>", arrow,
        _node("prompting", a), arrow,
        _node("rag", a), arrow,
        model, arrow,
        _node("raisonnement", a), arrow,
        _node("inference", a), arrow,
        "<div class='node endpoint'>Résultat</div>",
    ]
    flow_row = "<div class=flow-row>" + "".join(parts) + "</div>"

    # bande transverse 1 : Contrôle & orchestration (agentique enveloppe le flux)
    ag = REF.BRICKS["agentique"]
    ag_on = " on" if "agentique" in a else ""
    ag_badge = "<span class=non>ACTIF</span>" if "agentique" in a else ""
    controle_band = (f"<div class='control-band{ag_on}'>{ag_badge}"
                     f"<div class=nk>CONTRÔLE — INTERVIENT AU PROMPT ET AU RÉSULTAT</div>"
                     f"<div class=nt>{_esc(ag['label'])}</div>"
                     f"<div class=nr>{_esc(ag['role'])}</div></div>")

    # bande transverse 2 : Axes-propriétés (qualités qu'on mesure)
    trans_cells = "".join(f"<div class=tcell><b>{_esc(v['label'])}</b><br>{_esc(v['role'])}</div>"
                          for v in REF.TRANSVERSE.values())

    # trajectoires X->Y par brique
    order = ["architecture", "alignement", "prompting", "rag", "agentique", "raisonnement", "inference"]
    gnames = {"amont": "Amont", "flux": "Flux", "controle": "Contrôle"}
    traj = ""
    for k in order:
        b = REF.BRICKS[k]
        subs = "".join(f"<span class=chip>{_esc(s)}</span>" for s in b["sub"])
        traj += (f"<div class=traj-item><div class=traj-h><span class=tl>{_esc(b['label'])}</span>"
                 f"<span class=grp>{gnames.get(b['group'],'')}</span></div>"
                 f"<div class=traj-xy><span class=x>{_esc(b['traj_from'])}</span> → <span class=to>{_esc(b['traj_to'])}</span></div>"
                 f"<div class=traj-sub>{subs}</div>"
                 f"<div class=traj-anchor>{_esc(b['anchor'])}</div></div>")

    return f"""
    <section id=schema class=view>
      <div class=eyebrow>Référentiel · briques fonctionnelles</div>
      <div class=title style='font-size:24px'>Les briques, du prompt au résultat</div>
      <div class=lead>Le parcours d'une requête, de gauche à droite. Deux briques « amont » fabriquent le modèle ;
        le reste s'enchaîne à l'exécution. Le contrôle agentique enveloppe tout le flux. Les briques encadrées ont bougé cette semaine.</div>
      <div class=flow-wrap>
        <div class=flow-band-label>Amont — fabrication du modèle</div>
        <div class=flow-amont>{amont}</div>
        <div class=flow-band-label>Flux d'exécution — expérience utilisateur</div>
        {flow_row}
        <div class=flow-band-label>Contrôle &amp; orchestration — transverse au flux</div>
        {controle_band}
        <div class=flow-band-label>Axes-propriétés transverses</div>
        <div class=transverse-band><div class=trow>{trans_cells}</div></div>
      </div>
      <div class=part>
        <div class=part-head><h2>Trajectoire par brique</h2><span class=sub>d'où l'on vient → état actuel</span></div>
        <div class=traj>{traj}</div>
      </div>
      <div class=foot>Chaque nouveauté du compte-rendu est rattachée à l'une de ces briques.
        Trajectoires et sous-briques éditables dans referential.py.</div>
    </section>"""


def render_report(report, ledger, week_label, out_dir=OUTPUT_DIR):
    m, r, e = report["cr"]["majeures"], report["cr"]["radar"][:RADAR_MAX], report["cr"]["entrants"]
    active = report.get("active_bricks", [])
    maj = _release_table(m) if m else \
        "<div class=calm>Pas de rupture majeure cette semaine — aucun lancement flagship ni bascule tarifaire de premier plan. Les mouvements notables sont au radar ci-dessous.</div>"
    rad = _release_table(r) if r else "<div class=calm>Aucun mouvement secondaire détecté cette semaine.</div>"
    entr = "".join(_entrant_block(x) for x in e) if e else \
        "<div class=calm>Aucun nouvel entrant validé cette semaine (3 critères stricts non remplis).</div>"

    cr_view = f"""
    <section id=cr class='view active'>
      <div class=eyebrow>Compte-rendu hebdomadaire</div>
      <div class=title>{_esc(report['doc_title'])}</div>
      <div class=hero><div class=verdict>{_esc(report.get('verdict'))}</div>
        <div class=stats>
          <div class='stat hi'><div class=n>{len(m)}</div><div class=l>Nouveauté(s) majeure(s)</div></div>
          <div class=stat><div class=n>{len(r)}</div><div class=l>Mouvements au radar</div></div>
          <div class=stat><div class=n>{len(e)}</div><div class=l>Nouveaux entrants</div></div></div></div>
      <div class=part>
        <div class=part-head><h2>Partie 1 — Sorties importantes</h2><span class=sub>7 derniers jours</span></div>
        {_active_bar(active)}
        <div class=subhead>🔴 Nouveautés majeures <span class=c>· impact fort</span></div>{maj}
        <div class=subhead>🟡 Radar de la semaine <span class=c>· top {RADAR_MAX}</span></div>{rad}</div>
      <div class=part>
        <div class=part-head><h2>Partie 2 — Nouveaux entrants &amp; licornes</h2><span class=sub>open-source ou autres · 14 jours</span></div>
        {entr}</div>
      <div class=foot>Généré le {_esc(report.get('generated'))} · Providers suivis : {_esc(report.get('roster',''))}.<br>
        Dates = dates de publication vérifiées ; un item sans date vérifiable n'est pas remonté comme nouveau.
        Claims marketing distingués de la critique des benchmarks. Sans répétition d'une semaine sur l'autre.</div>
    </section>"""

    etat_view = f"""
    <section id=etat class=view>
      <div class=eyebrow>État des lieux · référence courante</div>
      <div class=title style='font-size:24px'>Photographie du marché à date</div>
      <div class=lead>Modèle phare, spécialisation et tendance coût par provider. Cette vue se répète volontairement :
        c'est la référence. Le compte-rendu, lui, ne montre que ce qui a changé.</div>
      {_etat_table(ledger)}
      <div class=foot>Généré le {_esc(datetime.date.today().isoformat())}.</div>
    </section>"""

    schema_view = _schema_view(active)

    body = f"""
    <div class=masthead><div class=brand>LLM <span>Market Watch</span></div><div class=issue>{_esc(week_label)}</div></div>
    <nav class=tabs>
      <button class='tab active' data-view=cr>Compte-rendu</button>
      <button class=tab data-view=etat>État des lieux</button>
      <button class=tab data-view=schema>Schéma des briques</button></nav>
    {cr_view}{etat_view}{schema_view}"""

    doc = ("<!doctype html><html lang=fr><head><meta charset=utf-8>"
           "<meta name=viewport content='width=device-width,initial-scale=1'>"
           f"<title>{_esc(report['doc_title'])}</title><style>{_CSS}</style></head>"
           f"<body><div class=page>{body}</div><script>{_JS}</script></body></html>")

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "archive").mkdir(exist_ok=True)
    (out_dir / "archive" / f"CR-{report['week_id']}.html").write_text(doc, encoding="utf-8")
    latest = out_dir / "latest.html"
    latest.write_text(doc, encoding="utf-8")
    return latest
