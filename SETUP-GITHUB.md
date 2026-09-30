# Déploiement cloud — GitHub Actions (lundi matin, sans ton Mac)

Fait tourner le pipeline complet dans le cloud chaque lundi : dédup réelle (le
`ledger.json` est recommité dans le dépôt à chaque run), rapport publié sur une
URL fixe (GitHub Pages), email optionnel. Aucune dépendance à ton Mac.

## 1. Créer le dépôt et pousser le projet

Crée un dépôt **privé** sur github.com (ex. `llm-watch`), puis en local :

```zsh
cd ~/llm-watch
git init
git add .
git commit -m "LLM Market Watch"
git branch -M main
git remote add origin https://github.com/<ton-compte>/llm-watch.git
git push -u origin main
```

Le `.gitignore` empêche déjà de pousser ton `.env` (tes secrets restent hors du dépôt).

## 2. Déclarer les secrets

Dépôt → **Settings → Secrets and variables → Actions → New repository secret** :

- `ANTHROPIC_API_KEY` — **obligatoire** (clé API de console.anthropic.com, facturée au token ; ce n'est pas ton abonnement Max).
- Pour l'email (optionnel) : `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `MAIL_FROM`, `MAIL_TO`.
  Gmail : utilise un *mot de passe d'application*.

Tu ne colles ces valeurs qu'ici, côté GitHub. Le code ne les voit jamais en clair.

## 3. Activer GitHub Pages

Dépôt → **Settings → Pages → Build and deployment → Source = GitHub Actions**.
Après le premier run, ton rapport sera à une URL du type
`https://<ton-compte>.github.io/llm-watch/`.

## 4. Premier test (à la demande)

Dépôt → onglet **Actions** → workflow **« LLM Market Watch — hebdo »** →
**Run workflow**. Vérifie que les deux jobs (`build`, `deploy`) passent au vert,
puis ouvre l'URL Pages.

## 5. (Optionnel) Lier l'email à l'URL en ligne

Une fois l'URL Pages connue : **Settings → Secrets and variables → Actions →
Variables → New variable** → `REPORT_URL` = ton URL Pages. Les liens de l'email
pointeront alors vers la page en ligne au lieu d'un fichier local.

C'est tout. Le cron tourne ensuite **chaque lundi** automatiquement.

---

## Bon à savoir (honnêteté sur GitHub Actions)

- **Horaire.** Le cron est réglé sur `06:00 UTC` = **08:00 Paris l'été / 07:00 l'hiver**
  (le fichier gère le fuseau via `TZ: Europe/Paris` pour la date du titre). GitHub peut
  décaler un cron de quelques minutes selon la charge : c'est « lundi matin », pas 8:00 pile.
- **Viser 08:00 pile toute l'année** (optionnel) : mettre deux crons et ne garder que
  l'heure Paris voulue.
  ```yaml
  on:
    schedule:
      - cron: '0 6 * * 1'
      - cron: '0 7 * * 1'
  # puis, 1er step du job build :
      - id: guard
        run: |
          [ "$(TZ=Europe/Paris date +%H)" = "08" ] && echo "go=1" >> "$GITHUB_OUTPUT" || echo "go=0" >> "$GITHUB_OUTPUT"
      - name: Générer le rapport
        if: steps.guard.outputs.go == '1'
        run: python collect.py
  ```
- **Coût.** Dépôt privé : ~2000 min/mois gratuites (ce job prend quelques minutes/semaine,
  très en dessous). Dépôt public : minutes illimitées.
- **Auto-désactivation.** GitHub désactive un cron après 60 jours **sans commit**. Ici le
  recommit hebdo du ledger compte comme activité → le cron reste actif tout seul.
- **Dédup.** Le `ledger.json` recommité à chaque run porte la mémoire anti-répétition.
  Pour repartir d'une photo complète : supprime `state/ledger.json` du dépôt et relance.
- **Lancer à la demande.** Le bouton *Run workflow* (onglet Actions) régénère un bilan
  quand tu veux, en plus du lundi.
