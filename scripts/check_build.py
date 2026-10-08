#!/usr/bin/env python3
"""Camada de COMPILACAO (tracks de debugging) — generico.

Roda o comando de build declarado pela track em track.json (suites.compila):
    {"cmd": "mvn -B -q package -DskipTests", "dir": "backend",
     "pontos": 25, "criterio": "B (compilação)"}

Binario por desenho no CI: build ok = pontos cheios, quebrado = 0. A
proporcao fina por erro corrigido e refinada na correcao docente.
Emite result-compila.json.
"""
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
import track_lock  # noqa: E402

cfg = track_lock.load(BASE).get("suites", {}).get("compila", {})
CMD = cfg.get("cmd", "")
DIR = os.path.join(BASE, cfg.get("dir", "."))
PONTOS = int(cfg.get("pontos", 25))
CRITERIO = cfg.get("criterio", "Compilação")

if not CMD:
    print("suites.compila.cmd ausente no track.json — nada a fazer.")
    sys.exit(2)

print("$ %s   (cwd: %s)" % (CMD, cfg.get("dir", ".")))
r = subprocess.run(CMD, shell=True, cwd=DIR)
ok = r.returncode == 0

resultado = {"job": "compila", "criterio": CRITERIO,
             "pontos": PONTOS if ok else 0, "max": PONTOS,
             "obs": ["build '%s' %s" % (CMD, "OK" if ok else "FALHOU"),
                     "Proporcao fina por erro corrigido na correcao docente."]}
with open(os.path.join(BASE, "result-compila.json"), "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)
print(json.dumps(resultado, ensure_ascii=False, indent=2))
