# Correspondance aux missions — portfolio indépendant

| Mission | Démonstration concrète | Limites / suite métier |
|---|---|---|
| Aligner des sources hétérogènes | JSON ClinicalTrials + XML PubMed vers Record ; alias ; NCT explicites | Ontologies métier, bras, doses, indications fines et revue des ambiguïtés à ajouter |
| Développer des agents | Pipeline déterministe, trace par composant ; synthèse LLM facultative | Pas d’autonomie multi-agents ; aucun benchmark comparant des frameworks |
| Bases relationnelles/vectorielles | SQLite versionné ; vecteurs Sentence Transformers optionnels dans SQLite | Pas de serveur vectoriel dédié ; modèle réel à télécharger et évaluer |
| Serveurs MCP/API | API FastAPI ; MCP officiel SDK v1 stdio avec quatre outils | Pas de MCP HTTP public/OAuth ni connexion à un système de l’entreprise |
| Contrôle qualité | Règles documentaires, hash, idempotence, revue liée à une version, tests | Pas de validation réglementaire ou méthodologique des études |
| Restitution et espaces internes | Catalogue, dashboard, recherche avec preuves, CSV/JSON, mode privé | Pas de SSO, partage par équipe ou rapports métier homologués |

## Démonstration d’entretien — 5 minutes
1. Montrer la bannière fictive et expliquer pourquoi aucun résultat clinique n’est fabriqué.
2. Chercher une molécule, montrer extrait, URL, hash et date de collecte.
3. Ouvrir un essai et sa publication liée par NCT ; distinguer référence et preuve clinique.
4. Montrer les champs absents, une revue humaine et les tests de remise en attente après changement.
5. Montrer MCP, Docker et la séparation entre démonstration publique et espace de travail interne.

Présentation possible : « J’ai développé OncoSignal, un POC de veille oncologique qui rapproche des notices d’essais et de publications, conserve leur provenance et expose des recherches via API et MCP. Le prototype distingue les traitements déterministes, les options LLM et les étapes de validation humaine. »
Ne pas présenter le projet comme réalisé pour Pierre Fabre, ni comme une solution déjà validée sur leurs données.
