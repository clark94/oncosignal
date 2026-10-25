# MCP local

Installation : `python -m pip install -e ".[mcp]"` dans l’environnement du projet.
Le SDK v1 maintenu est volontairement épinglé `<2`, tests réalisés avec 1.30.0. Ce choix permet Python 3.10 et les interfaces utilisées ; ce n’est pas une revendication d’utilisation de la dernière version majeure.

Exemple de configuration pour un client MCP qui supporte `mcpServers` (adapter les chemins) :
```json
{
  "mcpServers": {
    "oncosignal": {
      "command": "C:\\CHEMIN\\oncosignal\\.venv\\Scripts\\python.exe",
      "args": ["-m", "oncosignal.mcp_server"],
      "env": {
        "ONCO_WORKSPACE": "C:\\CHEMIN\\oncosignal\\workspace"
      }
    }
  }
}
```

Initialiser d’abord ce workspace avec `python -m oncosignal demo` ou la collecte. Le serveur MCP ne crée pas automatiquement le corpus fictif. Le chemin absolu évite les problèmes de répertoire courant.

Le client lance le serveur ; les messages JSON-RPC utilisent stdin/stdout. Les sorties de diagnostic vont sur stderr. Le test `test_actual_mcp_stdio` démarre réellement le sous-processus, initialise la session, découvre les outils et appelle `search_evidence`.

Le mode privé de l’API HTTP ne s’applique pas au transport stdio : la protection est celle du compte local et des permissions du fichier SQLite. Ne donner accès qu’à un client de confiance et n’y mettre aucune donnée non autorisée. Pas de transport HTTP MCP fourni dans cette version.
