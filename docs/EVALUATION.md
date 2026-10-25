# Évaluation

## Tests logiciels
API et contrôle d’accès, idempotence des imports, alias sans faux positifs par sous-chaîne, liens NCT, citations, abstention, version/revue, rejet des sorties LLM inventées, index périmé, exports CSV sans formules actives et communication MCP stdio.

## Garde-fou synthétique
`tests/benchmark_demo.py` contient six questions : cinq molécules et une absence de réponse. Le fichier `benchmark-demo.json` conserve les résultats du code livré : précision et rappel à 2, rang réciproque, abstention et latence. C’est un jeu construit avec les mêmes fiches que les tests ; aucune généralisation métier.

## Protocole métier à construire avec les experts
- Corpus réel daté, échantillonné par source, indication, molécule, phase et promoteur ; documenter couverture et exclusions.
- Questions indépendantes rédigées avant les expériences, réponses/sources attendues validées par deux experts, arbitrage des désaccords.
- Séparer jeu de calibration (alias, seuil) et jeu de test ; éviter fuite entre publications d’un même essai.
- Comparer TF-IDF seul et hybride sur le même snapshot : Recall@k, nDCG@k, MRR, précision, abstentions justifiées et fausses abstentions.
- Mesurer précision/rappel de l’alignement NCT et des entités ; ne pas confondre mention de molécule avec bras expérimental.
- Pour le LLM : fidélité affirmation par affirmation, couverture des citations, contradictions, omissions et degré d’abstention ; annotation humaine obligatoire.
- Temps de collecte, latences p50/p95, RAM et coût par question, avec fournisseurs/modèles/prix/version/date explicités. Les coûts nuls ou absents ne doivent pas être présentés comme gratuits si un LLM externe est utilisé.

Les métriques de corpus réel, de fidélité clinique et de coût fournisseur ne sont pas disponibles et ne sont pas inventées.
