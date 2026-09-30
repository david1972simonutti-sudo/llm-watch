"""
ledger.py — État persistant + déduplication déterministe.

Source de vérité unique inter-semaines. Permet :
  1. de ne jamais répéter une info déjà remontée (dédup par ID stable) ;
  2. de tenir un "état des lieux" courant par provider (tableau de référence) ;
  3. de distinguer "vraiment nouveau" d'un vieux résultat de web search qui
     remonte par hasard (fenêtre sur la date de PUBLICATION).

La dédup sur texte libre de LLM ne peut pas être parfaite : le ledger reste
inspectable et corrigeable à la main (state/ledger.json).
"""

import json
import re
import difflib
import datetime
import unicodedata
from pathlib import Path

LEDGER_PATH = Path("state/ledger.json")
DATE_WINDOW_DAYS = 30      # au-delà, un item n'est pas "nouveau cette semaine"
FUZZY_THRESHOLD = 0.86     # rattrape les variations de formulation d'un même item


def _empty_ledger() -> dict:
    return {"items": {}, "snapshot": {}, "weeks_generated": [], "last_run": None}


def load_ledger(path: Path = LEDGER_PATH) -> dict:
    path = Path(path)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for k, v in _empty_ledger().items():
            data.setdefault(k, v)
        return data
    return _empty_ledger()


def save_ledger(ledger: dict, path: Path = LEDGER_PATH) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def make_id(provider_id: str, item: dict) -> str:
    key = item.get("slug") or item.get("title") or item.get("name") or ""
    return f"{provider_id}:{slugify(key)}"


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", slugify(text))


def find_existing(ledger, provider_id, item, threshold=FUZZY_THRESHOLD):
    new_id = make_id(provider_id, item)
    if new_id in ledger["items"]:
        return new_id
    new_norm = _norm(item.get("slug") or item.get("title") or item.get("name") or "")
    if not new_norm:
        return None
    for iid, ex in ledger["items"].items():
        if ex.get("provider_id") != provider_id:
            continue
        ex_norm = _norm(ex.get("slug") or ex.get("title") or ex.get("name") or "")
        if not ex_norm:
            continue
        if new_norm == ex_norm or difflib.SequenceMatcher(None, new_norm, ex_norm).ratio() >= threshold:
            return iid
    return None


def parse_date(s):
    if not s:
        return None
    try:
        return datetime.date.fromisoformat(str(s).strip()[:10])
    except ValueError:
        return None


def classify(ledger, provider_id, item, today, window_days=DATE_WINDOW_DAYS):
    """(statut, id) : 'known' | 'new' | 'backfill'.
    backfill = nouveau au ledger mais non daté / trop ancien -> entre au ledger
    en silence pour ne pas ressortir, mais PAS dans le CR."""
    existing = find_existing(ledger, provider_id, item)
    if existing:
        return ("known", existing)
    new_id = make_id(provider_id, item)
    pub = parse_date(item.get("published_date"))
    if pub is None:
        return ("backfill", new_id)
    age = (today - pub).days
    if age > window_days or age < -3:
        return ("backfill", new_id)
    return ("new", new_id)


def record(ledger, item_id, provider_id, item, week_id, today, in_cr):
    if item_id in ledger["items"]:
        return
    stored = dict(item)
    stored.update({"id": item_id, "provider_id": provider_id,
                   "first_seen_week": week_id, "first_seen_date": today.isoformat(),
                   "surfaced_in_cr": in_cr})
    ledger["items"][item_id] = stored


def update_snapshot(ledger, provider_id, snapshot, week_id, today):
    if not snapshot:
        return
    row = dict(snapshot)
    row.update({"provider_id": provider_id, "updated_week": week_id,
                "updated_date": today.isoformat()})
    ledger["snapshot"][provider_id] = row
