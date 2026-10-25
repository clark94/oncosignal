# Validation — 25 octobre 2026

## Exécuté
- Linux, CPython **3.10.22** ; installation du package avec extras dev et mcp.
- Tests Python : **19 réussis**, un avertissement de dépréciation de TestClient. Cas API, citations, XML/JSON, pagination, versions/revue, protection, index synthétique et protocole MCP.
- Test MCP réel : sous-processus Python, initialisation de session, découverte de quatre outils, appel search_evidence via SDK client/serveur 1.30.0.
- Frontend : vérification syntaxique JavaScript et test DOM jsdom 26.1.0 contre un vrai serveur Uvicorn (chargement des 10 notices, navigation, recherche citée, filtre essai, détail avec provenance).
- Évaluation lexicale sur 6 questions fictives : résultats dans benchmark-demo.json ; pas de prétention de performance clinique.

## Non exécuté ou partiel
- Visuel dans Chrome/Edge réel : non testé. Le test jsdom ne vérifie ni rendu pixel ni application réelle de la CSP.
- API ClinicalTrials en direct : indisponible dans le réseau de préparation (DNS). PubMed en direct : non testé. Le parsing et les scénarios HTTP sont vérifiés sur fixtures synthétiques.
- Vrai modèle Sentence Transformers : pas téléchargé/testé. Persistance des vecteurs, fusion et détection de péremption testées avec un encodeur factice clairement identifié.
- OpenAI réel : aucun appel effectué, aucune clé fournie ; contrat HTTP et rejet des citations fabriquées testés avec httpx.MockTransport.
- Construction du wheel Python : réussie ; assets web et corpus de démonstration inclus.
- Docker Engine absent de l’environnement : image non construite ici. Workflow CI fourni pour build et smoke test.
- Déploiement GitHub/Render : instructions et configuration fournies ; aucun dépôt ou service créé.
- Windows : non exécuté ; instructions adaptées à PowerShell et Python 3.10.

Une dépréciation de Starlette TestClient concernant httpx a été observée ; les tests passent avec les versions enregistrées dans requirements-tested.txt.

## Reproduire le contrôle DOM (facultatif)
Node.js n’est pas nécessaire au fonctionnement. Pour les développeurs qui veulent reproduire le test, installer jsdom dans un dossier de test séparé :
```powershell
npm.cmd install --prefix .ui-tests jsdom@26.1.0
$env:NODE_PATH = "$PWD\.ui-tests\node_modules"
$env:ONCO_TEST_PYTHON = "$PWD\.venv\Scripts\python.exe"
node tests/ui-smoke.cjs
```
Ne pas versionner .ui-tests. Le script choisit un port temporaire et ne modifie pas le workspace principal.
