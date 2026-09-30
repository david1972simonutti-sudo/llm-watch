"""
demo_data.py — Jeu d'exemple pour `python collect.py --demo` (aucun appel API).

Scénario : la semaine dernière on a déjà remonté GPT-5.6, Opus 5, Grok 4.5.
Cette semaine : 2 majeures (Gemini 3 Ultra, DeepSeek V4), plusieurs mouvements
radar (Qwen, Mistral, Cohere, Meta), un nouvel entrant hors roster (Moonshot Kimi).
Opus 5 est re-remonté par le collecteur -> doit être filtré (test de dédup).
"""

import datetime

VERDICT = ("Google et DeepSeek rebattent les cartes : niveau top sur le code à tarif agressif, "
           "pendant que l'open-weights chinois (Qwen, DeepSeek) s'installe durablement dans le peloton de tête.")


def _pub(days):
    return (datetime.date.today() - datetime.timedelta(days=days)).isoformat()


# ── Déjà vu la semaine dernière (pré-charge le ledger) ──
_PRIOR = [
    ("openai", "OpenAI / GPT", {"slug": "gpt-5-6", "title": "GPT-5.6", "published_date": "2026-07-20", "impact": "high"}),
    ("anthropic", "Anthropic / Claude", {"slug": "opus-5", "title": "Claude Opus 5", "published_date": "2026-07-24", "impact": "high"}),
    ("xai", "xAI / Grok", {"slug": "grok-4-5", "title": "Grok 4.5", "published_date": "2026-07-18", "impact": "medium"}),
]

_SNAP = {
    "openai": {"provider_name": "OpenAI / GPT", "flagship_model": "GPT-5.6 Sol/Terra/Luna",
        "specialization": "raisonnement, science, cyber", "tags": ["code", "agent", "reasoning"],
        "cost_state": "↘ Luna -30%", "cost_direction": "down", "signal": "3 variantes : compromis coût/perf par contexte."},
    "anthropic": {"provider_name": "Anthropic / Claude", "flagship_model": "Claude Opus 5 / Fable 5",
        "specialization": "code long-horizon, agents", "tags": ["code", "agent", "enterprise"],
        "cost_state": "↘ Opus 5 -50%", "cost_direction": "down", "signal": "Opus 5 = intelligence proche de Fable 5 à moitié prix."},
    "google": {"provider_name": "Google / Gemini", "flagship_model": "Gemini 3 Ultra",
        "specialization": "multimodal, code, contexte long", "tags": ["code", "multimodal", "agent"],
        "cost_state": "↘ -40% vs 2.5 Pro", "cost_direction": "down", "signal": "Gemini 3 Ultra : niveau top code à tarif agressif."},
    "meta": {"provider_name": "Meta / Llama", "flagship_model": "Llama 4.1",
        "specialization": "open-weights, multimodal", "tags": ["open", "multimodal"],
        "cost_state": "poids ouverts", "cost_direction": "stable", "signal": "Resserre l'écart avec les modèles fermés."},
    "mistral": {"provider_name": "Mistral AI", "flagship_model": "Mistral Large 3.1",
        "specialization": "open-weights, souverain EU", "tags": ["open", "code", "enterprise"],
        "cost_state": "poids ouverts", "cost_direction": "stable", "signal": "Alternative souveraine open-weights."},
    "xai": {"provider_name": "xAI / Grok", "flagship_model": "Grok 4.5",
        "specialization": "temps réel X/SpaceX", "tags": ["code", "agent"],
        "cost_state": "$2 / $6 par M tokens", "cost_direction": "stable", "signal": "Temps réel X ; benchmarks indépendants absents."},
    "microsoft": {"provider_name": "Microsoft Copilot", "flagship_model": "Copilot / Azure OpenAI",
        "specialization": "M365, enterprise", "tags": ["enterprise", "agent"],
        "cost_state": "↑ Cowork pay-per-use", "cost_direction": "up", "signal": "Copilot Cowork facturé à l'usage."},
    "deepseek": {"provider_name": "DeepSeek", "flagship_model": "DeepSeek-V4",
        "specialization": "code, raisonnement, très bas coût", "tags": ["open", "code", "reasoning"],
        "cost_state": "≈1/10 des flagships fermés", "cost_direction": "down", "signal": "Rapport perf/prix agressif en poids ouverts."},
    "qwen": {"provider_name": "Qwen / Alibaba", "flagship_model": "Qwen 3 Max",
        "specialization": "multilingue, open-weights", "tags": ["open", "multimodal", "reasoning"],
        "cost_state": "poids ouverts", "cost_direction": "stable", "signal": "Famille très large, forte adoption en Asie."},
    "cohere": {"provider_name": "Cohere", "flagship_model": "Command A / R+",
        "specialization": "RAG, enterprise, souveraineté", "tags": ["enterprise", "rag"],
        "cost_state": "API entreprise", "cost_direction": "stable", "signal": "Positionnement RAG/entreprise, déploiement privé."},
    "lighton": {"provider_name": "LightOn", "flagship_model": "Paradigm / Agent-ModernColBERT",
        "specialization": "RAG souverain européen", "tags": ["enterprise", "open"],
        "cost_state": "SaaS", "cost_direction": "stable", "signal": "Pivot enterprise confirmé ; la tech linéaire n'est pas le moat."},
}


def seed_ledger(L, wid, today):
    ledger = L._empty_ledger()
    last = (today - datetime.timedelta(days=7)).isoformat()
    for pid, pname, rel in _PRIOR:
        rel = dict(rel); rel["provider_name"] = pname
        iid = L.make_id(pid, rel)
        rel.update({"id": iid, "provider_id": pid, "first_seen_week": "prior",
                    "first_seen_date": last, "surfaced_in_cr": True})
        ledger["items"][iid] = rel
    for pid, snap in _SNAP.items():
        row = dict(snap); row.update({"provider_id": pid, "updated_week": "prior", "updated_date": last})
        ledger["snapshot"][pid] = row
    return ledger


def _rel(pid, pname, **kw):
    kw.setdefault("provider_name", pname)
    return {"id": pid, "name": pname, "snapshot": _SNAP[pid], "releases": [kw]}


PROVIDERS_OUT = [
    {"id": "google", "name": "Google / Gemini", "snapshot": _SNAP["google"], "releases": [
        {"slug": "gemini-3-ultra", "title": "Gemini 3 Ultra", "kind": "release", "impact": "high", "brique":"architecture",
         "problem_solved": "Rapproche Google du meilleur niveau sur le code et le raisonnement long, là où 2.5 décrochait.",
         "application_unlocked": "Agents de dev multi-fichiers et analyse de documents massifs à coût contenu.",
         "cost_trend": "↘ ~-40% vs 2.5 Pro", "cost_direction": "down",
         "published_date": _pub(2), "source_url": "https://blog.google/technology/ai/gemini-3-ultra",
         "source_type": "officiel", "benchmark_note": "SWE-bench Verified ~74% annoncé par Google, non reproduit indépendamment à ce stade."}]},
    {"id": "deepseek", "name": "DeepSeek", "snapshot": _SNAP["deepseek"], "releases": [
        {"slug": "deepseek-v4", "title": "DeepSeek-V4", "kind": "release", "impact": "high", "brique":"architecture",
         "problem_solved": "Perf proche du top en code à une fraction du coût, en poids ouverts.",
         "application_unlocked": "Copilotes de code internes très bas coût, déployables sans API US.",
         "cost_trend": "≈1/10 du prix des flagships fermés", "cost_direction": "down",
         "published_date": _pub(4), "source_url": "https://huggingface.co/deepseek-ai/DeepSeek-V4",
         "source_type": "officiel", "benchmark_note": "SWE-bench Verified ~71% auto-rapporté ; à confirmer sur leaderboard indépendant."}]},
    {"id": "qwen", "name": "Qwen / Alibaba", "snapshot": _SNAP["qwen"], "releases": [
        {"slug": "qwen-3-max", "title": "Qwen 3 Max", "kind": "release", "impact": "medium", "brique":"raisonnement",
         "problem_solved": "Améliore raisonnement et multilingue, comble l'écart avec les modèles fermés.",
         "application_unlocked": "Assistants multilingues (zh/en) déployables on-premise.",
         "cost_trend": "poids ouverts", "cost_direction": "stable",
         "published_date": _pub(3), "source_url": "https://qwenlm.github.io", "source_type": "officiel", "benchmark_note": None}]},
    {"id": "mistral", "name": "Mistral AI", "snapshot": _SNAP["mistral"], "releases": [
        {"slug": "mistral-large-3-1", "title": "Mistral Large 3.1", "kind": "feature", "impact": "medium", "brique":"agentique",
         "problem_solved": "Améliore le suivi d'instructions et l'appel d'outils, faiblesses de la 3.0.",
         "application_unlocked": "Assistants métier open-weights on-premise, sans cloud US.",
         "cost_trend": "poids ouverts, stable", "cost_direction": "stable",
         "published_date": _pub(3), "source_url": "https://mistral.ai/news/large-3-1", "source_type": "officiel", "benchmark_note": None}]},
    {"id": "cohere", "name": "Cohere", "snapshot": _SNAP["cohere"], "releases": [
        {"slug": "command-a-0826", "title": "Command A (mise à jour août)", "kind": "feature", "impact": "medium", "brique":"rag",
         "problem_solved": "Meilleure fidélité RAG et réduction des hallucinations sur documents d'entreprise.",
         "application_unlocked": "Recherche documentaire d'entreprise avec citations fiables.",
         "cost_trend": "tarif API inchangé", "cost_direction": "stable",
         "published_date": _pub(5), "source_url": "https://cohere.com/blog", "source_type": "officiel", "benchmark_note": None}]},
    {"id": "meta", "name": "Meta / Llama", "snapshot": _SNAP["meta"], "releases": [
        {"slug": "llama-4-1", "title": "Llama 4.1", "kind": "release", "impact": "low", "brique":"architecture",
         "problem_solved": "Corrige des régressions de contexte long de la 4.0.",
         "application_unlocked": "Fine-tuning souverain pour secteurs régulés.",
         "cost_trend": "gratuit (poids ouverts)", "cost_direction": "stable",
         "published_date": _pub(6), "source_url": "https://ai.meta.com/blog/llama-4-1", "source_type": "officiel", "benchmark_note": None}]},
    # Opus 5 re-remonté -> DOIT être filtré (déjà connu)
    {"id": "anthropic", "name": "Anthropic / Claude", "snapshot": _SNAP["anthropic"], "releases": [
        {"slug": "opus-5", "title": "Claude Opus 5", "kind": "release", "impact": "high",
         "problem_solved": "…", "application_unlocked": "…", "cost_trend": "…",
         "published_date": "2026-07-24", "source_url": "https://anthropic.com", "source_type": "officiel"}]},
    # OpenAI, xAI, Microsoft, LightOn : semaine calme (snapshot seul)
    {"id": "openai", "name": "OpenAI / GPT", "snapshot": _SNAP["openai"], "releases": []},
    {"id": "xai", "name": "xAI / Grok", "snapshot": _SNAP["xai"], "releases": []},
    {"id": "microsoft", "name": "Microsoft Copilot", "snapshot": _SNAP["microsoft"], "releases": []},
    {"id": "lighton", "name": "LightOn", "snapshot": _SNAP["lighton"], "releases": []},
]

EMERGING_OUT = [
    {"slug": "kimi-k2", "name": "Kimi K2", "org": "Moonshot AI", "country": "Chine", "impact": "medium", "brique":"architecture",
     "problem_solved": "Contexte ultra-long (>1M tokens) fiable, à coût maîtrisé.",
     "application_unlocked": "Analyse de corpus juridiques/financiers entiers en une passe.",
     "positioning": "Spécialiste du contexte long face à Gemini ; moins généraliste que GPT/Claude.",
     "cost_trend": "API à bas coût ; poids partiels ouverts",
     "published_date": _pub(4), "source_url": "https://huggingface.co/moonshotai/Kimi-K2", "source_type": "officiel",
     "validation_criteria": {"publication": "arXiv:2508.xxxxx", "funding": "levée >1Md$ (2025)",
        "benchmark_name": "MMLU-Pro", "benchmark_score": "~86%", "availability": "https://huggingface.co/moonshotai/Kimi-K2"},
     "benchmark_note": "Scores de contexte long auto-rapportés ; méthodologie à vérifier."}
]
