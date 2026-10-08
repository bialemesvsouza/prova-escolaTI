#!/usr/bin/env python3
"""Camada de SUBIDA (tracks de debugging) — generico.

Sobe o ambiente containerizado da track com a variante injetada no ambiente
(TODOS os parametros escalares de variante/params.json viram variaveis de
ambiente — o compose da track os referencia, ex.: ${PORTA_PUBLICADA}) e conta
quantos servicos ficaram em execucao.

Config em track.json (suites.sobe):
    {"compose_file": "compose.yaml", "servicos_esperados": 3,
     "espera_s": 45, "pontos": 20, "criterio": "C (configuração)"}

Binario no CI: todos os servicos de pe = pontos cheios; senao 0 (a proporcao
fina e da correcao docente). Emite result-sobe.json e SEMPRE derruba o
ambiente ao final (compose down -v).
"""
import json
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
import track_lock  # noqa: E402
from variante import slug_do_repo, variante  # noqa: E402

cfg = track_lock.load(BASE).get("suites", {}).get("sobe", {})
COMPOSE = cfg.get("compose_file", "compose.yaml")
ESPERADOS = int(cfg.get("servicos_esperados", 3))
ESPERA = int(cfg.get("espera_s", 45))
PONTOS = int(cfg.get("pontos", 20))
CRITERIO = cfg.get("criterio", "Configuração")


def env_da_variante():
    env = dict(os.environ)
    for k, val in variante(slug_do_repo(), BASE).items():
        if isinstance(val, (str, int)):
            env[k] = str(val)
    return env


env = env_da_variante()
print("==> docker compose -f %s up --build -d" % COMPOSE)
up = subprocess.run(["docker", "compose", "-f", COMPOSE, "up", "--build", "-d"],
                    cwd=BASE, env=env)
print("==> aguardando %ds" % ESPERA)
time.sleep(ESPERA)
r = subprocess.run(["docker", "compose", "-f", COMPOSE, "ps",
                    "--status", "running", "--format", "{{.Name}}"],
                   capture_output=True, text=True, cwd=BASE, env=env)
running = [l for l in r.stdout.splitlines() if l.strip()]
subprocess.run(["docker", "compose", "-f", COMPOSE, "logs", "--tail=50"],
               cwd=BASE, env=env)

ok = up.returncode == 0 and len(running) >= ESPERADOS
resultado = {"job": "sobe", "criterio": CRITERIO,
             "pontos": PONTOS if ok else 0, "max": PONTOS,
             "obs": ["Servicos em execucao: %d/%d" % (len(running), ESPERADOS),
                     "Proporcao fina por erro corrigido na correcao docente."]}
with open(os.path.join(BASE, "result-sobe.json"), "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)
print(json.dumps(resultado, ensure_ascii=False, indent=2))

subprocess.run(["docker", "compose", "-f", COMPOSE, "down", "-v"],
               cwd=BASE, env=env)
