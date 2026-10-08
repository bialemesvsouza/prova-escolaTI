#!/usr/bin/env python3
"""Runner de SMOKE (tracks de debugging) — generico.

O esqueleto cuida do CICLO DE VIDA do ambiente (compose up/down com a
variante injetada como variaveis de ambiente); as CHECAGENS do contrato sao
da track, no script declarado em track.json (suites.smoke):

    {"compose_file": "compose.yaml", "script": "smoke_track.py",
     "espera_s": 45}

O script da track (pos-overlay na RAIZ do repo do aluno, como o
tests_publicos.py das tracks de API) deve emitir result-smoke.json no formato
de criterios do nota.py. Este runner NAO conhece o contrato da prova.
Sempre derruba o ambiente ao final (compose down -v).
"""
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
import track_lock  # noqa: E402
from variante import slug_do_repo, variante  # noqa: E402

cfg = track_lock.load(BASE).get("suites", {}).get("smoke", {})
COMPOSE = cfg.get("compose_file", "compose.yaml")
SCRIPT = cfg.get("script", "smoke_track.py")
ESPERA = int(cfg.get("espera_s", 45))

if not os.path.exists(os.path.join(BASE, SCRIPT)):
    print("Script de smoke da track ausente: %s" % SCRIPT)
    sys.exit(2)

env = dict(os.environ)
for k, val in variante(slug_do_repo(), BASE).items():
    if isinstance(val, (str, int)):
        env[k] = str(val)

try:
    print("==> docker compose -f %s up --build -d" % COMPOSE)
    subprocess.run(["docker", "compose", "-f", COMPOSE, "up", "--build", "-d"],
                   cwd=BASE, env=env)
    print("==> aguardando %ds" % ESPERA)
    time.sleep(ESPERA)
    print("==> python3 %s (checagens da track)" % SCRIPT)
    subprocess.run([sys.executable, SCRIPT], cwd=BASE, env=env)
finally:
    subprocess.run(["docker", "compose", "-f", COMPOSE, "down", "-v"],
                   cwd=BASE, env=env)
