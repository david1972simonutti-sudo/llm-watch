# LLM Market Watch — veille hebdomadaire

Veille LLM automatisée, livrée chaque **lundi 8h** par email, pour décideurs non-experts.
Titre du rapport : **« LLM analyse du DD/MM/YYYY »**.

## Ce qui est produit

| Objet | Rôle | Se répète ? |
|---|---|---|
| `state/ledger.json` | Mémoire interne (jamais ouverte à la main) de tout ce qui a été vu | — |
| `output/latest.html` | Fichier unique à **3 onglets** : *Compte-rendu* (le diff), *État des lieux* (référence), *Schéma des briques* (flux UX + trajectoires) | CR : non · État/Schéma : oui |
| Email du lundi | Rappel synthétique : majeures + radar + entrants, lien vers le fichier | Non |

La navigation entre les deux onglets est interne (JavaScript) : un seul fichier à ouvrir,
aucun lien inter-fichiers cassable. L'email pointe vers l'onglet CR ; `#etat` ouvre directement
sur le tableau de référence.

Le CR est en **deux parties** :
- **Partie 1 — Sorties importantes** : tableau *Nouveautés majeures* (impact fort) puis *Radar* (top 5).
- **Partie 2 — Nouveaux entrants & licornes** : modèles validés sur 3 critères stricts (arXiv/financement >10M€, benchmark vérifié, dispo réelle).

**Providers suivis (11)** : OpenAI, Anthropic, Google, Meta, Mistral, xAI, Microsoft, **DeepSeek, Qwen/Alibaba, Cohere**, LightOn.

## Deux façons de l'automatiser

- **Cloud (recommandé) — GitHub Actions** : tourne chaque lundi sans ton Mac, dédup réelle
  (ledger recommité), rapport publié sur une URL fixe (Pages), email optionnel. Voir **SETUP-GITHUB.md**.
- **Local — macOS launchd** : tourne sur ton Mac le lundi 8h (voir § Automatiser). Contrainte :
  le Mac doit être allumé.

## Installation

```bash
cd llm-watch
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # puis édite .env
```

## Prévisualiser sans clé API

```bash
python collect.py --demo
```

Génère les deux HTML à partir de données d'exemple. Montre la dédup : un « Opus 5 »
déjà connu ne réapparaît pas dans le CR mais reste dans le tableau.

## Collecte réelle

```bash
python collect.py            # collecte + HTML + email
python collect.py --no-mail  # sans email
```

## Automatiser le lundi 8h (macOS)

1. `run_weekly.sh` → adapte `PROJECT_DIR`.
2. `com.david.llmwatch.plist` → remplace les 3 chemins `/Users/david/llm-watch/...`.
3. Installe :

```bash
chmod +x run_weekly.sh && mkdir -p logs
cp com.david.llmwatch.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.david.llmwatch.plist
launchctl start com.david.llmwatch    # test immédiat
```

**Limite assumée** : si le Mac dort à 8h, le run se fait au réveil (une fois) ; s'il est
éteint, il est sauté. Pour une exécution garantie portable fermé → passer en cloud
(GitHub Actions + Pages), non inclus.

## Email

Renseigne le bloc SMTP du `.env`. Pour Gmail : *mot de passe d'application*
(<https://myaccount.google.com/apppasswords>), jamais ton mot de passe principal.
Bloc vide = pas d'email, le reste fonctionne. Les secrets restent en local.

## Dédup & maintenance

- ID stable `provider:slug` ; un ID déjà connu est ignoré.
- Item sans date de publication vérifiable, ou daté de +30 j → entre au ledger en
  silence mais **pas** dans le CR (protection anti-hallucination).
- `state/ledger.json` est éditable pour corriger un doublon. Le supprimer = repartir de zéro.

## Référentiel des briques fonctionnelles

Chaque nouveauté est rattachée à **une brique** parmi 7 : `architecture`, `alignement`,
`prompting`, `rag`, `agentique`, `raisonnement`, `inference` (+ axes transverses
`evaluation`, `multimodal`, `securite`). Le CR affiche la brique par item et les
« briques qui bougent cette semaine ». L'onglet *Schéma* présente le flux UX
(Prompt → RAG → Agentique → Modèle → Raisonnement → Inférence → Résultat) et la
trajectoire X→Y de chaque brique. Tout est éditable à un seul endroit : `referential.py`
(libellés, trajectoires, sous-briques, ancres scientifiques).

## Fichiers

```
collect.py  ledger.py  render.py  notify.py  demo_data.py  referential.py
run_weekly.sh  com.david.llmwatch.plist  requirements.txt  .env.example
output/  state/  logs/
```
