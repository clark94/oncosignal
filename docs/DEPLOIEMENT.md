# Déploiement

## Démonstration portfolio
GitHub contient le code et les fixtures fictives. L’image Docker contient les assets et le corpus d’exemple. Le serveur écoute sur ONCO_HOST=0.0.0.0 et lit PORT fourni par l’hébergeur.
Render : Web Service Docker, racine contenant Dockerfile, health `/health`. Aucun build/start personnalisé nécessaire en mode Docker. Une adresse HTTPS est fournie par la plateforme ; consulter les prix et conditions actuels avant de valider le service.
Ne définir ni ONCO_ADMIN_TOKEN ni OPENAI_API_KEY pour une simple démo publique. Les écritures API seront alors refusées. Les appels de synthèse LLM sont uniquement en CLI et ne sont pas exposés via le site.

La base est dans /workspace dans l’image. Sans volume persistant, les données ne survivent pas aux redéploiements/restarts/veilles. Une offre gratuite convient à une démo réinitialisable, pas à la conservation du corpus d’une entreprise. Docker Compose local contient un volume persistant.

## Espace interne pilote
Définir ONCO_PRIVATE=1, ONCO_ADMIN_TOKEN>=24 caractères aléatoires, ONCO_WORKSPACE sur stockage durable et NCBI_EMAIL. Le jeton est saisi dans le dialogue de l’interface et envoyé dans Authorization, jamais dans une URL. Le changer après exposition.
Le navigateur conserve le jeton en mémoire, pas dans localStorage. Un utilisateur ayant le jeton possède les droits admin ; il n’existe pas de rôles ni d’identité vérifiée.
Avant données internes : SSO/OIDC, rôles, journaux nominatifs, sauvegardes testées, règles de conservation, revue sécurité, contrats de données et validation par les responsables. Pas d’inférence de conformité légale ou réglementaire.

## Dépannage Windows
- `pyproject.toml` introuvable : `Test-Path .\pyproject.toml`, ouvrir le sous-dossier oncosignal.
- `No module named oncosignal` : installer le projet dans le même .venv utilisé pour lancer.
- `ERR_CONNECTION_REFUSED` : garder le serveur ouvert et tester `curl.exe --noproxy "*" http://127.0.0.1:8010/health` dans un deuxième terminal.
- Port utilisé : `$env:ONCO_PORT="8011"`, relancer et ouvrir localhost:8011.
- Recherche hybride refusée : installer l’extra semantic et réindexer le workspace concerné ; aucun retour silencieux en mode lexical.
- Collecte refusée : jeton admin absent/invalide ; ne pas confondre avec la clé OpenAI.
- PubMed indisponible : vérifier NCBI_EMAIL, connexion et limites d’usage.
- API retourne 502 : source externe indisponible, pas de faux succès ; réessayer après vérification. Aucun contournement de restriction réseau automatique.
