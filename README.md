# OncoSignal · Scientific Intelligence

**Plateforme de veille et de rapprochement de données scientifiques en oncologie.**
Projet indépendant de MAMPOUYA CLARK, inspiré des missions de stage en Competitive Intelligence / Data Science. Aucune affiliation, validation ou donnée interne des Laboratoires Pierre Fabre.

## Ce qui fonctionne

- Interface web française : synthèse du corpus, phases, liens NCT, recherche citée, catalogue, qualité, revue et collecte.
- Collecteurs bornés ClinicalTrials.gov API v2 et PubMed E-utilities, sur action explicite.
- Stockage SQLite des notices, instantanés de réponses, versions, empreintes SHA-256 et décisions de revue.
- Rapprochement conservateur : petit dictionnaire d’alias et liens par NCT exact, sans fusion arbitraire d’études.
- Recherche lexicale TF-IDF fonctionnelle sans modèle téléchargé ; index sémantique optionnel persistant et fusion RRF.
- API FastAPI ; serveur MCP SDK v1 réellement implémenté et testé en stdio local.
- Synthèse extractive par défaut ; brouillon OpenAI optionnel en CLI avec vérification de citations exactes.
- Tests, évaluation synthétique, Docker, GitHub Actions et configuration Render.

## 1. Windows / VS Code — démarrage

**Python 3.10**. Extraire le ZIP, puis ouvrir le dossier **oncosignal**, qui contient `pyproject.toml` et `lancer.py`. Ne pas ouvrir seulement le dossier parent créé par Windows.

Dans Terminal → Nouveau terminal, exécuter une ligne à la fois :

```powershell
py -3.10 -m venv .venv
```
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-tested.txt
```
```powershell
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
```
```powershell
.\.venv\Scripts\python.exe -m oncosignal serve
```

Ouvrir **http://127.0.0.1:8010/** dans Chrome/Edge sur le même ordinateur. Garder ce terminal ouvert. Ctrl+C arrête le serveur. Il n’est pas nécessaire d’activer PowerShell ou d’installer Node.js.

Les exécutions suivantes peuvent aussi utiliser :
```powershell
py -3.10 lancer.py
```

Le premier démarrage charge **10 notices entièrement fictives**. Les NCT de démonstration et les liens example.invalid ne sont pas des sources réelles. Aucune conclusion clinique ne doit être tirée de ces données. Le corpus ne décrit pas les produits ou la stratégie d’une entreprise réelle.

Le manifeste principal est `pyproject.toml`. `requirements-tested.txt` est un instantané de versions de dépendances testées sous Python 3.10, pas un verrou multiplateforme complet avec hashes.

Installation alternative avec résolution actualisée :
```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,mcp]"
```

## 2. Vérifier le fonctionnement

Dans un deuxième terminal du même dossier :
```powershell
curl.exe --noproxy "*" http://127.0.0.1:8010/health
```
Réponse : `{"ok":true}`. Schéma de l’API : `/openapi.json`. L’interface principale n’utilise pas de CDN et applique une politique CSP restrictive.

```powershell
.\.venv\Scripts\python.exe -m oncosignal search "pembrolizumab melanoma"
```
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
```powershell
.\.venv\Scripts\python.exe tests/benchmark_demo.py
```
Détail des essais : `docs/VALIDATION.md`. Les scores du petit corpus synthétique ne mesurent pas la performance métier.

## 3. Collecter des données publiques réelles

Les commandes CLI ne nécessitent pas de jeton administrateur. Elles s’exécutent dans un deuxième terminal et utilisent le même workspace :

```powershell
.\.venv\Scripts\python.exe -m oncosignal collect --source clinicaltrials --query "melanoma AND pembrolizumab" --limit 20
```
Pour PubMed, renseigner votre vraie adresse de contact :
```powershell
$env:NCBI_EMAIL = "VOTRE_ADRESSE_EMAIL"
.\.venv\Scripts\python.exe -m oncosignal collect --source pubmed --query "pembrolizumab AND melanoma" --limit 20
```
La collecte est plafonnée à 100 notices par action et à 10 pages ; les jetons de pagination répétés sont refusés. Limitation réseau locale à deux requêtes/seconde, trois tentatives sur 429/5xx, timeout HTTP. Les imports sont idempotents par identifiant source ; toute modification scientifique crée une version et remet la revue en attente. Les données des deux sources restent des notices distinctes.

Pour la collecte depuis l’interface : arrêter le serveur, définir un jeton aléatoire, puis le relancer **dans le même terminal** :
```powershell
$env:ONCO_ADMIN_TOKEN = (.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))")
$env:NCBI_EMAIL = "VOTRE_ADRESSE_EMAIL"
.\.venv\Scripts\python.exe -m oncosignal serve
```
Conserver le jeton dans votre gestionnaire de mots de passe ; pour le consulter localement, `$env:ONCO_ADMIN_TOKEN` l’affiche (ne pas en partager de capture). Cliquer **Accès administrateur**, saisir ce jeton, puis **Collecte de sources**.

Le bouton de connexion ne vérifie les droits qu’au moment des opérations protégées si la lecture est publique. La clé est conservée uniquement dans la mémoire de la page, jusqu’au rafraîchissement. Il s’agit d’un jeton partagé, pas d’un système SSO ou multi-utilisateur.

Pour un corpus entièrement réel, utiliser un espace séparé :
```powershell
$env:ONCO_WORKSPACE = "$PWD\workspace-reel"
.\.venv\Scripts\python.exe -m oncosignal collect --source clinicaltrials --query "melanoma" --limit 20
.\.venv\Scripts\python.exe -m oncosignal serve
```
Le serveur ne charge le corpus fictif que si la base est vide. Actualiser la page après une collecte CLI. Une collecte ne supprime pas les notices qui disparaissent d’une réponse ultérieure : ce n’est pas une synchronisation exhaustive.

## 4. Recherche hybride optionnelle

La recherche de base est **TF-IDF**, pas une recherche sémantique. Pour activer les vrais embeddings :
```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[semantic]"
.\.venv\Scripts\python.exe -m oncosignal index-semantic
```
Le premier appel télécharge `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` et ses dépendances. Les vecteurs sont stockés dans SQLite, puis comparés par cosinus en mémoire et fusionnés avec TF-IDF par RRF. Réindexer après modification/collecte. Sélectionner **Hybride** dans l’interface, ou :
```powershell
.\.venv\Scripts\python.exe -m oncosignal search "melanoma immunotherapy" --mode hybrid
```
Le seuil .35 est expérimental ; à calibrer. Ce n’est pas un moteur vectoriel dédié ni un modèle validé en oncologie. Le téléchargement du vrai modèle n’a pas été vérifié dans cette livraison.

## 5. Synthèse LLM optionnelle — CLI privée uniquement

Le site public n’expose **aucun endpoint payant** de synthèse. La réponse par défaut est extractive. Pour un brouillon généré sur les sources retrouvées, utiliser uniquement des données autorisées à être envoyées au fournisseur :
```powershell
$env:OPENAI_API_KEY = "VOTRE_CLE_PRIVEE"
$env:ONCO_LLM_MODEL = "NOM_DU_MODELE_COMPATIBLE"
$env:ONCO_ALLOW_EXTERNAL_LLM = "1"
.\.venv\Scripts\python.exe -m oncosignal brief "pembrolizumab melanoma" --llm
```
Le modèle doit accepter Chat Completions, le mode JSON et `max_completion_tokens`. Aucun modèle ni tarif n’est imposé. Un appel par commande, maximum 900 jetons de sortie demandés, pas de retry automatique. Les affirmations doivent citer un identifiant fourni et une citation exacte ; sinon la sortie est rejetée. La fidélité sémantique reste à annoter. Les jetons retournés par l’API sont enregistrés dans la sortie ; le coût n’est jamais inventé. Aucun appel à un vrai LLM n’a été effectué ici.

Sans LLM :
```powershell
.\.venv\Scripts\python.exe -m oncosignal brief "osimertinib"
```

## 6. MCP

Le SDK v1 est délibérément borné à `<2` ; ne pas copier des exemples du SDK v2 sans migration.
```powershell
.\.venv\Scripts\python.exe -m oncosignal demo
.\.venv\Scripts\python.exe -m oncosignal mcp
```
Le transport **stdio** attend un client MCP : aucune page web ne s’ouvre, ce n’est pas une erreur. Le client lance normalement ce processus lui-même. Quatre outils en lecture seule : `search_evidence`, `get_record`, `quality_report`, `trial_publication_links`. Aucun outil SQL arbitraire, aucune collecte ou commande shell via MCP. Exemple de configuration dans `docs/MCP.md`.

## 7. Docker local

Avec Docker Desktop démarré :
```powershell
docker compose up --build -d
docker compose ps
docker compose logs --tail 50
```
Ouvrir http://127.0.0.1:8010/. Arrêter : `docker compose down`. La base est conservée dans un volume nommé. `down -v` supprime les données : ne pas l’utiliser pour un simple arrêt.

L’image de base n’installe ni MCP ni Sentence Transformers : ces composants sont optionnels et restent disponibles par installation Python. Aucun téléchargement de modèle lors du démarrage Docker. Ne pas exécuter plusieurs workers sur ce prototype SQLite.

## 8. GitHub et déploiement HTTPS

Nom proposé : **oncosignal**. Description : « Veille scientifique en oncologie : collecte, alignement, recherche citée, contrôles qualité, API et MCP. »

Créer un dépôt vide, puis :
```powershell
git init
git add .
git status
git commit -m "Ajoute OncoSignal, prototype de veille oncologique"
git branch -M main
git remote add origin https://github.com/clark94/oncosignal.git
git push -u origin main
```
Ne pas publier workspace, secrets ou données confidentielles. Vérifier le contenu avant commit. Les clés mises dans le terminal ne sont pas automatiquement dans Git.

Render : Web Service depuis ce dépôt, runtime Docker, Dockerfile `./Dockerfile`, health `/health`. Root Directory vide si pyproject.toml est à la racine. Choisir le plan adapté et vérifier son prix. Le fichier render.yaml fournit une base de configuration sans imposer un abonnement.

Pour une démonstration publique sans frais LLM : aucun jeton admin, aucune clé OpenAI. Les 10 notices fictives sont alors consultables ; collecte et revue HTTP sont désactivées. Pour un espace interne, configurer **ONCO_PRIVATE=1** et **ONCO_ADMIN_TOKEN** en variables privées ; prévoir SSO, rôles et audit nominatif avant un usage d’entreprise.

Le stockage gratuit éphémère de Render ne conserve pas durablement la collecte. Utiliser une base/volume persistant pour un vrai workspace. Voir `docs/DEPLOIEMENT.md`.

## Architecture et portée

`src/oncosignal/` : modèles, collecteurs, store SQLite, alignement, contrôles, recherche, orchestration, API, CLI, MCP et assets web.
`tests/` : API, parsers, pagination, versions, citations, index et véritable échange MCP ; fixtures entièrement fictives.
`docs/` : correspondance à l’offre, architecture, sources, évaluation, déploiement et validation.

Les « agents » de collecte, alignement, qualité et preuve sont des composants déterministes orchestrés. Pas de système multi-agents autonome. La synthèse LLM est un module distinct facultatif. L’objectif est un POC démontrable et auditable, pas un outil de décision clinique ou une plateforme validée pour des données internes.
