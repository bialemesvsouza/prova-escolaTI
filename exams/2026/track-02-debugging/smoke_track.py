"""Smoke de ponta a ponta da track-02 (Cadastro de Produtos).

Script ENTREGUE PELA TRACK (vai para a raiz do repo do aluno no overlay) —
o esqueleto (scripts/smoke.py) cuida do ciclo de vida do compose; aqui ficam
as checagens do contrato de "saudavel" do ENUNCIADO/contrato.json.

Stdlib pura. Recomputa a variante do nome do repo (nao confia no params.json
commitado) — copia de colega falha aqui. Emite result-smoke.json.
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "scripts"))
from variante import slug_do_repo, variante  # noqa: E402

v = variante(slug_do_repo(), BASE)
PORTA = v["PORTA_PUBLICADA"]
ORIGEM = v["ORIGEM_FRONTEND"]
API = "http://localhost:%d/produtos" % PORTA

observacoes = []


def req(metodo, url, body=None, timeout=5, origin=False):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=metodo)
    if data:
        r.add_header("Content-Type", "application/json")
    if origin:
        # CORS so e exercitado de verdade com Origin — sem ele o servidor
        # (corretamente) NAO devolve Access-Control-Allow-Origin
        r.add_header("Origin", ORIGEM)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode()
    except Exception as e:
        return 0, {}, str(e)


# aguarda o backend (max 90s)
for _ in range(30):
    status, _, _ = req("GET", API, timeout=2)
    if status == 200:
        break
    time.sleep(3)

backend_ok, cors_ok, post_ok, lista_ok, frontend_ok = False, False, False, False, False

status, headers, body = req("GET", API, origin=True)
if status == 200:
    try:
        backend_ok = isinstance(json.loads(body), list)
    except ValueError:
        backend_ok = False
cors = next((v for k, v in headers.items()
             if k.lower() == "access-control-allow-origin"), "")
cors_ok = backend_ok and (cors == ORIGEM or cors == "*")

status, _, body = req("POST", API, {"nome": "Teclado", "precoCentavos": 15000, "quantidade": 7})
post_ok = status == 201

status, _, body = req("GET", API)
if status == 200:
    try:
        lista_ok = any(p.get("nome") == "Teclado" for p in json.loads(body))
    except ValueError:
        lista_ok = False

status, _, _ = req("GET", "http://localhost:3000", timeout=5)
frontend_ok = status == 200

pontos_d = 15 if (backend_ok and cors_ok) else (8 if backend_ok else 0)
pontos_a = 30 if (backend_ok and cors_ok and post_ok and lista_ok and frontend_ok) else 0

observacoes.append("backend GET /produtos: %s" % ("OK" if backend_ok else "FALHOU"))
observacoes.append("CORS (%s): %s" % (ORIGEM, "OK" if cors_ok else "FALHOU"))
observacoes.append("POST /produtos: %s" % ("OK" if post_ok else "FALHOU"))
observacoes.append("listagem apos POST: %s" % ("OK" if lista_ok else "FALHOU"))
observacoes.append("frontend :3000: %s" % ("OK" if frontend_ok else "FALHOU"))

resultado = {
    "job": "smoke",
    "criterios": [
        {"criterio": "A (app funcional)", "pontos": pontos_a, "max": 30},
        {"criterio": "D (startup/lógica)", "pontos": pontos_d, "max": 15},
    ],
    "obs": observacoes,
}
with open(os.path.join(BASE, "result-smoke.json"), "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)
print(json.dumps(resultado, ensure_ascii=False, indent=2))
subprocess.run(["docker", "compose", "logs", "--tail=80", "backend"])
