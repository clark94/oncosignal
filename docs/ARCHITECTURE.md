# Architecture et choix

Sources → instantanés SQLite → normalisation → notices versionnées → liens NCT explicites → index → recherche/extraits → revue humaine.

- **CollectionAgent** : endpoints fixes, pagination bornée, retries bornés, instantanés de réponse (JSON ou XML). Pas de scraping de sites ni texte intégral d’éditeurs.
- **AlignmentAgent** : Unicode/accents, alias explicites de quatre molécules et trois indications, extraction NCT. Les noms non reconnus ne sont pas inventés ; les interventions structurées de ClinicalTrials sont conservées. Dictionnaire à enrichir et valider par les experts. Pas d’alignement complet MeSH/UMLS/ChEMBL, pas de détection de cible moléculaire ni dose/bras/biomarqueur.
- **QualityAgent** : manque de phase, promoteur, texte, date et revue. Un champ manquant dans une publication n’a pas la même signification que dans un essai. Les indicateurs de couverture ne doivent pas être agrégés comme un score clinique.
- **EvidenceAgent** : référence NCT exacte entre une publication et un essai ; un lien peut ne concerner qu’une mention et reste à vérifier. Pas de fusion par simple ressemblance de titre.
- **Retrieval** : TF-IDF recalculé sur le petit corpus ; option embeddings persistés + cosinus + RRF. Aucun entraînement local ; similarité sans calibration probabiliste.
- **Synthesis** : extraction sans LLM par défaut ; un appel facultatif de génération en CLI seulement.

## Tables
`records` (identité source unique, statut de revue, hash et document normalisé), `versions` (contenus scientifiques successifs), `snapshots` (réponses sources brutes), `vectors` (modèle + version de contenu + vecteur), `reviews` (décision associée au hash), `audit` (événements de pipeline).

Les ensembles molécules/indications restent des tableaux JSON dans la notice : ce prototype n’implémente pas un modèle normalisé de graphe biomédical. SQLite est la base relationnelle effective ; les vecteurs sont persistés et interrogés en mémoire, pas servis par une base vectorielle industrielle. Migration Postgres/pgvector ou autre moteur à étudier après mesures.

## Traçabilité
SHA-256 identifie un contenu, sans prouver sa vérité ni certifier sa source. La date de collecte n’est pas la date scientifique. DateRevised PubMed est une révision de notice, pas la date de publication. Le champ de mise à jour du registre est conservé séparément.
Les contrôles portent sur la notice courante. Les instantanés préservent les réponses reçues ; leurs éventuelles erreurs de parsing sont signalées mais ne sont pas corrigées silencieusement.

## Limites opérationnelles
Une instance, corpus modeste, calcul de similarité exhaustif et stockage local. Aucun SLA, sauvegarde automatique, SSO, RBAC, journal inviolable, planificateur, tâche distribuée ou alertes e-mail. Une collecte déjà commencée peut continuer si le navigateur abandonne. Les limites de concurrence sont locales au processus. Les données collectées ne sont pas automatiquement toutes pertinentes en oncologie : le périmètre dépend de la requête.
