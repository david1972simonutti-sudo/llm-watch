"""
notify.py — Email de rappel du lundi, propre et synthétique.

Identifiants SMTP UNIQUEMENT depuis .env. Aucun secret dans ce fichier, aucun
envoi sans configuration explicite. Styles inline (compatibilité clients mail).

.env :
  SMTP_HOST=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USER=toi@gmail.com
  SMTP_PASS=mot_de_passe_application     # PAS ton mot de passe principal
  MAIL_FROM=toi@gmail.com
  MAIL_TO=toi@gmail.com                   # plusieurs adresses séparées par des virgules
"""

import os
import ssl
import html
import smtplib
import datetime
from email.message import EmailMessage
from pathlib import Path

INK = "#151A22"; INK2 = "#4C5666"; MUT = "#8B94A3"
AMBER = "#B45309"; BLUE = "#1F5FBF"; VIOLET = "#6D28D9"; LINE = "#E4E8EE"


def _esc(s): return html.escape(str(s or ""))


def _missing_env():
    return [k for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "MAIL_FROM", "MAIL_TO")
            if not os.environ.get(k)]


def _rows(items, dot):
    if not items:
        return (f"<tr><td style='padding:6px 0;color:{MUT};font-size:13px'>—</td></tr>")
    out = ""
    for it in items:
        name = _esc(it.get("title") or it.get("name"))
        prov = _esc(it.get("provider_name") or it.get("org") or "")
        prob = _esc(it.get("problem_solved", ""))
        out += (f"<tr><td style='padding:7px 0;border-bottom:1px solid {LINE}'>"
                f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;"
                f"background:{dot};margin-right:7px'></span>"
                f"<b style='color:{INK};font-size:14px'>{name}</b> "
                f"<span style='color:{MUT};font-size:12px'>· {prov}</span><br>"
                f"<span style='color:{INK2};font-size:12.5px'>{prob}</span></td></tr>")
    return out


def _body_html(report, cr_uri, etat_uri):
    c = report["cr"]
    maj = _rows(c["majeures"], AMBER) if c["majeures"] else \
        f"<tr><td style='padding:7px 0;color:{MUT};font-size:13px'>Pas de rupture majeure cette semaine.</td></tr>"
    return f"""<div style="font-family:-apple-system,'Segoe UI',Roboto,sans-serif;max-width:640px;margin:0 auto;color:{INK}">
  <div style="border-bottom:2px solid {INK};padding-bottom:10px">
    <span style="font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:{AMBER};font-weight:700">LLM Market Watch</span>
    <span style="float:right;font-size:12px;color:{MUT}">{_esc(report['week_label'])}</span></div>
  <h1 style="font-size:22px;margin:16px 0 6px;letter-spacing:-.02em">{_esc(report['doc_title'])}</h1>
  <p style="font-size:15px;line-height:1.5;font-weight:600;margin:0 0 20px;color:{INK}">{_esc(report.get('verdict'))}</p>

  <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:{AMBER};margin-bottom:2px">🔴 Nouveautés majeures</div>
  <table style="width:100%;border-collapse:collapse;margin-bottom:18px">{maj}</table>

  <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:{BLUE};margin-bottom:2px">🟡 Radar de la semaine ({len(c['radar'])})</div>
  <table style="width:100%;border-collapse:collapse;margin-bottom:18px">{_rows(c['radar'], BLUE)}</table>

  <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:{VIOLET};margin-bottom:2px">🟣 Nouveaux entrants ({len(c['entrants'])})</div>
  <table style="width:100%;border-collapse:collapse;margin-bottom:22px">{_rows(c['entrants'], VIOLET)}</table>

  <div style="background:#F6F7F9;border:1px solid {LINE};border-radius:10px;padding:14px 16px;font-size:14px">
    📄 <a href="{cr_uri}" style="color:{BLUE};font-weight:600">Ouvrir le compte-rendu complet</a><br>
    📊 <a href="{etat_uri}" style="color:{BLUE};font-weight:600">Ouvrir l'état des lieux</a>
  </div>
  <p style="font-size:11px;color:{MUT};margin-top:16px">Liens vers les fichiers générés sur ta machine ·
    dédup active, aucune répétition d'une semaine sur l'autre.</p>
</div>"""


def send_weekly(report, path: Path):
    """path = l'unique fichier HTML (onglets CR / État des lieux)."""
    missing = _missing_env()
    if missing:
        print(f"  ⚠ Email ignoré — variables .env manquantes : {', '.join(missing)}")
        return
    c = report["cr"]
    base = os.environ.get("REPORT_URL", "").strip()
    if base:
        cr_uri = base
        etat_uri = base.rstrip("/") + "#etat"
    else:
        cr_uri = path.as_uri()
        etat_uri = cr_uri + "#etat"
    subject = f"{report['doc_title']} — {len(c['majeures'])} majeure(s), {len(c['entrants'])} entrant(s)"
    msg = EmailMessage()
    msg["From"] = os.environ["MAIL_FROM"]
    msg["To"] = os.environ["MAIL_TO"]
    msg["Subject"] = subject
    msg.set_content(f"{report['doc_title']}\n{report.get('verdict','')}\n\nOuvre la version HTML.")
    msg.add_alternative(_body_html(report, cr_uri, etat_uri), subtype="html")
    ctx = ssl.create_default_context()
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"]), timeout=30) as s:
        s.starttls(context=ctx)
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)
    print(f"  ✓ Email envoyé à {os.environ['MAIL_TO']}")
