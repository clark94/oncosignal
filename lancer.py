"""Lancer depuis le dossier du projet : py -3.10 lancer.py"""
from pathlib import Path
import os
import subprocess
import sys

root=Path(__file__).resolve().parent
python=root/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
if not python.exists():
    print('Créez l’environnement : py -3.10 -m venv .venv',flush=True)
    raise SystemExit(1)
if subprocess.run([str(python),'-c','import oncosignal, fastapi, uvicorn'],cwd=root).returncode:
    print('Installez : .\\.venv\\Scripts\\python.exe -m pip install -e ".[dev,mcp]"',flush=True)
    raise SystemExit(1)
print('Ouvrez http://127.0.0.1:8010 dans Chrome/Edge. Gardez ce terminal ouvert.',flush=True)
raise SystemExit(subprocess.call([str(python),'-m','oncosignal','serve'],cwd=root))
