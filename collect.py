"""
collect.py — Collecte hebdomadaire + assemblage du CR "LLM analyse du DD/MM/YYYY".

Flux : collecte par provider (Claude + web search) -> classification via ledger
(nouveau / connu / à archiver) -> CR deux étages (majeures / radar top-5) +
entrants -> rendu HTML (CR + état des lieux) + email du lundi.

  python collect.py            # collecte réelle (nécessite ANTHROPIC_API_KEY)
  python collect.py --demo     # données d'exemple, sans API, pour prévisualiser
  python collect.py --no-mail  # sans email
"""

import os
import sys
import json
import time
import re
import datetime
from pathlib import Path

import ledger as L
import render as R
import referential as REF

RADAR_MAX = R.RADAR_MAX
MODEL = "claude-sonnet-4-6"
TODAY = datetime.date.today()

PROVIDERS_TIER1 = [
    {"id": "openai",    "name": "OpenAI / GPT"},
    {"id": "anthropic", "name": "Anthropic / Claude"},
    {"id": "google",    "name": "Google / Gemini"},
    {"id": "meta",      "name": "Meta / Llama"},
    {"id": "mistral",   "name": "Mistral AI"},
    {"id": "xai",       "name": "xAI / Grok"},
    {"id": "microsoft", "name": "Microsoft Copilot"},
    {"id": "deepseek",  "name": "DeepSeek"},
    {"id": "qwen",      "name": "Qwen / Alibaba"},
    {"id": "cohere",    "name": "Cohere"},
]
PROVIDERS_TIER2 = [{"id": "lighton", "name": "LightOn"}]

ROSTER_STR = ", ".join(p["name"] for p in PROVIDERS_TIER1) + ", LightOn"


def week_id():   return f"{TODAY.year}-W{TODAY.isocalendar()[1]:02d}"
def week_label():
    monday = TODAY - datetime.timedelta(days=TODAY.weekday())
    sunday = monday + datetime.timedelta(days=6)
    f = lambda d: d.strftime("%-d %b")
    return f"Semaine {TODAY.isocalendar()[1]} · {f(monday)}–{f(sunday)} {TODAY.year}"
def doc_title(): return f"LLM analyse du {TODAY.strftime('%d/%m/%Y')}"


def extract_json(text):
    text = re.sub(r"```json\s*", "", text); text = re.sub(r"```\s*", "", text).strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if not m: raise ValueError(f"Aucun JSON. Début : {text[:200]}")
    raw = m.group(0)
    try: return json.loads(raw)
    except json.JSONDecodeError: pass
    def fix(s):
        out, in_str, esc = [], False, False
        for ch in s:
            if esc: out.append(ch); esc = False; continue
            if ch == "\\": out.append(ch); esc = True; continue
            if ch == '"': in_str = not in_str; out.append(ch); continue
            if in_str and ch == "\n": out.append("\\n"); continue
            if in_str and ch == "\r": continue
            out.append(ch)
        return "".join(out)
    return json.loads(fix(raw))


def call_claude(prompt, max_tokens=2500, web_search=True):
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    kwargs = {"model": MODEL, "max_tokens": max_tokens,
              "messages": [{"role": "user", "content": prompt}]}
    if web_search:
        kwargs["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]
    resp = client.messages.create(**kwargs)
    return "\n".join(b.text for b in resp.content if hasattr(b, "text"))


PROVIDER_PROMPT = """Tu es un analyste IA senior. Veille hebdomadaire pour décideurs non-experts (C-level, responsables BU, directeurs techniques).

Aujourd'hui : {today}
Provider : {name}
Cherche les nouveautés des 7 derniers jours UNIQUEMENT.

Renvoie TOUJOURS :
1. snapshot = l'état COURANT du provider (même sans news), pour un tableau de référence.
2. releases = les nouveautés des 7 derniers jours (liste vide si rien de neuf — valide et honnête, n'invente rien).

Pour chaque release, 3 dimensions décideur (pas de jargon) :
- problem_solved : problème concret résolu, vs la version précédente
- application_unlocked : usage métier / type d'application débloqué
- cost_trend : hausse/baisse/nouveau tarif, ordre de grandeur si dispo

impact : "high" seulement pour nouveau flagship, rupture tarifaire, ou capacité qui débloque un usage. Sinon "medium"/"low".
published_date : date de PUBLICATION vérifiable (officiel/arXiv/leaderboard), YYYY-MM-DD. Non vérifiable -> null.
slug : identifiant machine court et stable (ex: "gpt-5-6").
benchmark_note : si un score est cité, distingue le claim marketing de ce qu'il mesure / risque de contamination. Sinon null.
brique : LA brique fonctionnelle principale que cette nouveauté fait avancer, une seule parmi :
  "architecture" (modèle brut, pré-entraînement, MoE, attention, contexte long)
  "alignement" (post-entraînement, RLHF, DPO, instruction tuning)
  "prompting" (techniques de prompt, interaction)
  "rag" (récupération / connaissance externe)
  "agentique" (outils, planification, agents, multi-agents)
  "raisonnement" (chain-of-thought entraîné, reasoning models, calcul à l'inférence)
  "inference" (efficience, quantization, vitesse, coût de service)
transverse : axe transverse secondaire concerné, ou null : "evaluation" | "multimodal" | "securite".

Retourne UNIQUEMENT du JSON valide, sans markdown :
{{"id":"{id}","name":"{name}",
"snapshot":{{"provider_name":"{name}","flagship_model":"...","specialization":"3-5 mots",
"tags":["code","agent","multimodal","open","enterprise","reasoning"],
"cost_state":"état tarifaire court","cost_direction":"down|up|stable",
"signal":"une phrase : l'état courant le plus important en langage business"}},
"releases":[{{"slug":"...","title":"...","kind":"release|feature|pricing|benchmark|partnership",
"impact":"high|medium|low","brique":"architecture|alignement|prompting|rag|agentique|raisonnement|inference",
"transverse":"evaluation|multimodal|securite ou null",
"problem_solved":"...","application_unlocked":"...","cost_trend":"...",
"published_date":"YYYY-MM-DD ou null","source_url":"...","source_type":"officiel|arxiv|benchmark|presse",
"benchmark_note":"ou null"}}]}}"""

LIGHTON_PROMPT = """Tu es un analyste IA spécialisé deep tech européenne. Aujourd'hui : {today}
Analyse LightOn (Paris). Rythme lent : cherche les 30 derniers jours.
Tranche : leur différenciation technique (attention linéaire) devient-elle un avantage business réel, ou pivotent-ils vers un RAG/enterprise générique ? Mets ce verdict dans snapshot.signal.
Même format que les autres providers (snapshot toujours renseigné + releases). published_date vérifiable (null sinon), slug stable.
Retourne UNIQUEMENT du JSON valide :
{{"id":"lighton","name":"LightOn",
"snapshot":{{"provider_name":"LightOn","flagship_model":"...","specialization":"3-5 mots",
"tags":["enterprise","open"],"cost_state":"...","cost_direction":"down|up|stable","signal":"verdict tech-vs-business"}},
"releases":[{{"slug":"...","title":"...","kind":"release|feature|pricing|benchmark|partnership",
"impact":"high|medium|low","brique":"architecture|alignement|prompting|rag|agentique|raisonnement|inference",
"transverse":"evaluation|multimodal|securite ou null","problem_solved":"...","application_unlocked":"...","cost_trend":"...",
"published_date":"YYYY-MM-DD ou null","source_url":"...","source_type":"officiel|arxiv|benchmark|presse","benchmark_note":"ou null"}}]}}"""

EMERGING_PROMPT = """Tu es un analyste IA rigoureux. Aujourd'hui : {today}
Cherche les NOUVEAUX modèles/startups LLM émergés dans les 14 derniers jours, HORS acteurs déjà suivis (OpenAI, Anthropic, Google, Meta, Mistral, xAI, Microsoft, DeepSeek, Qwen/Alibaba, Cohere, LightOn).

CRITÈRES STRICTS — inclus SEULEMENT si les 3 sont remplis :
1. Publication arXiv peer-reviewed OU financement documenté >10M€ OU levée significative annoncée
2. Performance vérifiée sur >=1 benchmark : SWE-bench, MMLU-Pro, HumanEval, GPQA, Chatbot Arena
3. Disponibilité réelle : API publique OU poids sur HuggingFace/GitHub
Nouvelles licornes / à surveiller : Falcon (TII), Yi (01.AI), Phi (MS Research), Amazon Nova, Reka, AI21, Moonshot/Kimi, Inflection, et toute nouvelle licorne LLM.
Si aucun ne remplit les 3 critères, retourne une liste vide (réponse honnête valide).
published_date vérifiable (null sinon), slug stable, impact selon l'ampleur.

Retourne UNIQUEMENT du JSON valide :
{{"emerging_models":[{{"slug":"...","name":"...","org":"...","country":"...","impact":"high|medium|low",
"brique":"architecture|alignement|prompting|rag|agentique|raisonnement|inference","transverse":"evaluation|multimodal|securite ou null",
"problem_solved":"...","application_unlocked":"...","positioning":"positionnement vs GPT/Claude/Gemini","cost_trend":"...",
"published_date":"YYYY-MM-DD ou null","source_url":"...","source_type":"officiel|arxiv|benchmark|presse",
"validation_criteria":{{"publication":"arXiv:XXXX ou null","funding":"montant ou null","benchmark_name":"...","benchmark_score":"...","availability":"URL"}},
"benchmark_note":"ce que mesure le benchmark / limites"}}]}}"""

VERDICT_PROMPT = """Tu es directeur de la stratégie IA. En UNE phrase (max 30 mots), langage décideur, dis la chose la plus importante de la semaine pour choisir un LLM aujourd'hui.
Données : {data}
Retourne UNIQUEMENT la phrase, sans guillemets ni préambule."""


def _ingest(pout, pid, pname, ledger, wid, buckets, active):
    for rel in pout.get("releases", []) or []:
        rel.setdefault("provider_name", pname)
        rel["brique"] = REF.normalize_brick(rel.get("brique")) or REF.DEFAULT_BRICK
        status, iid = L.classify(ledger, pid, rel, TODAY)
        if status == "known":
            continue
        L.record(ledger, iid, pid, rel, wid, TODAY, in_cr=(status == "new"))
        if status == "new":
            active.add(rel["brique"])
            (buckets["high"] if rel.get("impact") == "high" else buckets["rest"]).append(rel)


def _rank(items):
    order = {"medium": 0, "low": 1}
    src = {"officiel": 0, "arxiv": 0, "benchmark": 1, "presse": 2}
    return sorted(items, key=lambda it: (order.get(it.get("impact"), 2), src.get(it.get("source_type"), 3),
                  -(L.parse_date(it.get("published_date")) or datetime.date.min).toordinal()))


def build_report(providers_out, emerging_out, ledger, wid, wlabel, verdict_fn):
    buckets = {"high": [], "rest": []}
    active = set()
    for pout in providers_out:
        pid, pname = pout["id"], pout["name"]
        L.update_snapshot(ledger, pid, pout.get("snapshot"), wid, TODAY)
        _ingest(pout, pid, pname, ledger, wid, buckets, active)

    entrants = []
    for em in emerging_out or []:
        em.setdefault("provider_name", em.get("org", ""))
        em["brique"] = REF.normalize_brick(em.get("brique")) or REF.DEFAULT_BRICK
        status, iid = L.classify(ledger, "emerging", em, TODAY)
        if status == "known":
            continue
        L.record(ledger, iid, "emerging", em, wid, TODAY, in_cr=(status == "new"))
        if status == "new":
            active.add(em["brique"])
            entrants.append(em)
            L.update_snapshot(ledger, iid, {
                "provider_name": em.get("name"), "flagship_model": em.get("org", ""),
                "specialization": em.get("positioning") or (em.get("problem_solved", "")[:60]),
                "tags": ["entrant"], "cost_state": em.get("cost_trend", ""),
                "cost_direction": "stable", "signal": em.get("problem_solved", ""), "kind": "entrant",
            }, wid, TODAY)

    majeures = buckets["high"]
    radar = _rank(buckets["rest"])[:RADAR_MAX]
    compact = {"majeures": [f"{x.get('provider_name')}: {x.get('title')}" for x in majeures],
               "radar": [x.get("title") for x in radar], "entrants": [x.get("name") for x in entrants]}
    verdict = verdict_fn(compact) if (majeures or radar or entrants) else \
        "Semaine calme : aucun mouvement majeur, les choix de LLM restent inchangés."
    if not verdict:
        verdict = (f"{majeures[0].get('provider_name')} marque la semaine avec {majeures[0].get('title')}."
                   if majeures else "Mouvements incrémentaux au radar, pas de rupture majeure.")

    return {"week_id": wid, "week_label": wlabel, "doc_title": doc_title(),
            "generated": TODAY.isoformat(), "roster": ROSTER_STR, "verdict": verdict,
            "active_bricks": sorted(active),
            "cr": {"majeures": majeures, "radar": radar, "entrants": entrants}}


def collect_provider_live(prov, is_lighton=False):
    print(f"  → {prov['name']}")
    tpl = LIGHTON_PROMPT if is_lighton else PROVIDER_PROMPT
    raw = call_claude(tpl.format(today=TODAY.isoformat(), id=prov["id"], name=prov["name"]),
                      max_tokens=2500, web_search=True)
    return extract_json(raw)


def run_live(send_mail=True):
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)   # le .env est prioritaire sur une clé exportée dans .zshrc
    except ImportError:
        pass
    if "ANTHROPIC_API_KEY" not in os.environ:
        sys.exit("ANTHROPIC_API_KEY manquante — configure ton .env (voir .env.example).")

    wid, wlabel = week_id(), week_label()
    print(f"\n═══ {doc_title()} — {wlabel} ═══")
    ledger = L.load_ledger()
    providers_out = []
    print("\n▶ Providers")
    for prov in PROVIDERS_TIER1:
        try: providers_out.append(collect_provider_live(prov)); time.sleep(2)
        except Exception as e: print(f"    ✗ {prov['name']} : {e}")
    for prov in PROVIDERS_TIER2:
        try: providers_out.append(collect_provider_live(prov, is_lighton=True)); time.sleep(2)
        except Exception as e: print(f"    ✗ {prov['name']} : {e}")
    print("\n▶ Entrants")
    try:
        emerging_out = extract_json(call_claude(EMERGING_PROMPT.format(today=TODAY.isoformat()),
                                    max_tokens=2200, web_search=True)).get("emerging_models", [])
    except Exception as e:
        print(f"    ✗ entrants : {e}"); emerging_out = []

    def verdict_fn(c):
        try:
            return call_claude(VERDICT_PROMPT.format(data=json.dumps(c, ensure_ascii=False)),
                               max_tokens=200, web_search=False).strip()
        except Exception:
            return None

    report = build_report(providers_out, emerging_out, ledger, wid, wlabel, verdict_fn)
    _finalize(report, ledger, wid, wlabel, send_mail)


def run_demo(send_mail=False):
    import demo_data
    wid, wlabel = week_id(), week_label()
    print(f"\n═══ [DÉMO] {doc_title()} — {wlabel} ═══")
    ledger = demo_data.seed_ledger(L, wid, TODAY)
    report = build_report(demo_data.PROVIDERS_OUT, demo_data.EMERGING_OUT,
                          ledger, wid, wlabel, lambda c: demo_data.VERDICT)
    _finalize(report, ledger, wid, wlabel, send_mail)


def _finalize(report, ledger, wid, wlabel, send_mail):
    if wid not in ledger["weeks_generated"]:
        ledger["weeks_generated"].append(wid)
    ledger["last_run"] = TODAY.isoformat()
    L.save_ledger(ledger)
    path = R.render_report(report, ledger, wlabel)
    Path("output").mkdir(exist_ok=True)
    with open(f"output/report-{wid}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    c = report["cr"]
    print(f"\n  ✓ {len(c['majeures'])} majeure(s) · {len(c['radar'])} radar · {len(c['entrants'])} entrant(s)")
    print(f"  ✓ Rapport (CR + état des lieux, onglets) : {path}")
    if send_mail:
        try:
            import notify
            notify.send_weekly(report, path.resolve())
        except Exception as e:
            print(f"  ⚠ Email non envoyé : {e}")


if __name__ == "__main__":
    demo = "--demo" in sys.argv
    no_mail = "--no-mail" in sys.argv
    (run_demo if demo else run_live)(send_mail=not no_mail)
