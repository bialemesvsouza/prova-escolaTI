#!/usr/bin/env python3
"""Criterio E (metodo sistematico) — generico, para tracks de debugging.

Heuristica publica: commits pequenos, frequentes e com mensagens que indiquem
hipotese -> correcao; relatorio equivalente (tabela hipotese/evidencia) no
arquivo declarado pela track tambem conta.

Config em track.json (suites.metodo):
    {"pontos": 10, "relatorio": "backend/README.md"}

Emite result-metodo.json. O refinamento (revisao humana do metodo) e da
correcao docente.
"""
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
import track_lock  # noqa: E402

cfg = track_lock.load(BASE).get("suites", {}).get("metodo", {})
PONTOS = int(cfg.get("pontos", 10))
RELATORIO = cfg.get("relatorio", "backend/README.md")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=BASE).stdout


log = git("log", "--format=%s")
linhas = [l.strip() for l in log.splitlines() if l.strip()]
mensagens = [l for l in linhas
             if not any(m in l.lower() for m in ("github-actions", "[bot]"))]
n = len(mensagens)

padrao = re.compile(r"(fix|debug|corrige?|ajusta?|hypo|hip[oó]tese|wip)", re.I)
bem_descritivas = [m for m in mensagens if len(m) >= 12 and padrao.search(m)]

relatorio = os.path.exists(os.path.join(BASE, RELATORIO))
if relatorio:
    texto = open(os.path.join(BASE, RELATORIO), encoding="utf-8", errors="replace").read()
    relatorio = bool(re.search(r"(hip[oó]tese|erro|debug|diagn[oó]stico|corre[cç][aã]o)", texto, re.I))

pontos = 0
if n >= 2:
    pontos += 3
if n >= 4:
    pontos += 2
if len(bem_descritivas) >= 3:
    pontos += 3
if relatorio:
    pontos += 2
pontos = min(PONTOS, pontos)

resultado = {
    "job": "metodo", "criterio": "E (método)",
    "pontos": pontos, "max": PONTOS,
    "obs": ["%d commits, %d mensagens no padrao hipotese->correcao, relatorio: %s"
            % (n, len(bem_descritivas), "sim" if relatorio else "nao"),
            "Refinamento na correcao docente (revisao humana do metodo)."],
}
with open(os.path.join(BASE, "result-metodo.json"), "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)
print(json.dumps(resultado, ensure_ascii=False, indent=2))
