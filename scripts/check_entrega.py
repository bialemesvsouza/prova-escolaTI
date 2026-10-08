#!/usr/bin/env python3
"""Critérios de entrega: Containerfile/Dockerfile (15) e README com instruções (5).

O 'Dockerfile funcional' completo (suíte sobe sem ajustes) é confirmado pelos
jobs de teste; aqui se verifica a presença e o formato mínimo.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
criterios, obs = [], []


def peso(nome, default):
    """Peso do criterio vem da rubrica da pasta do ano (pos-overlay na raiz)."""
    raiz = os.path.join(os.getcwd(), "rubrica.json")
    for alvo in (raiz, os.path.join(BASE, "rubrica.json")):
        if os.path.exists(alvo):
            try:
                return int(json.load(open(alvo, encoding="utf-8"))
                           ["criterios"][nome])
            except Exception:
                pass
    return default

dockerfile = os.path.join(BASE, "Containerfile")
if not os.path.exists(dockerfile):
    dockerfile = os.path.join(BASE, "Dockerfile")
if not os.path.exists(dockerfile):
    criterios.append({"criterio": "Dockerfile", "pontos": 0, "max": peso("dockerfile", 15)})
    obs.append("Containerfile/Dockerfile AUSENTE — sem ele os testes não sobem e valem 0.")
else:
    texto = open(dockerfile, encoding="utf-8", errors="replace").read()
    nome = os.path.basename(dockerfile)
    if texto.strip() == "FROM scratch":
        criterios.append({"criterio": "Dockerfile", "pontos": 0, "max": peso("dockerfile", 15)})
        obs.append("%s ainda é o stub (FROM scratch)." % nome)
    elif re.search(r"EXPOSE\s+8080", texto) and ("CMD" in texto.upper() or "ENTRYPOINT" in texto.upper()):
        criterios.append({"criterio": "Dockerfile", "pontos": peso("dockerfile", 15), "max": peso("dockerfile", 15)})
        obs.append("%s presente com EXPOSE 8080 e comando de execução." % nome)
    else:
        criterios.append({"criterio": "Dockerfile", "pontos": 7, "max": peso("dockerfile", 15)})
        obs.append("%s presente, mas sem EXPOSE 8080 ou sem CMD/ENTRYPOINT." % nome)

readme = os.path.join(BASE, "README.md")
texto = open(readme, encoding="utf-8", errors="replace").read() if os.path.exists(readme) else ""
tem_local = re.search(r"(local|localhost|dev)", texto, re.I) and re.search(r"(rodar|subir|executar|run)", texto, re.I)
tem_container = re.search(r"(docker|container)", texto, re.I)
if tem_local and tem_container:
    criterios.append({"criterio": "README (instruções)", "pontos": peso("readme", 5), "max": peso("readme", 5)})
elif tem_local or tem_container:
    criterios.append({"criterio": "README (instruções)", "pontos": 2, "max": peso("readme", 5)})
    obs.append("README cobre só local ou só container.")
else:
    criterios.append({"criterio": "README (instruções)", "pontos": 0, "max": peso("readme", 5)})
    obs.append("README sem instruções de subida.")

resultado = {"job": "entrega", "criterios": criterios, "obs": obs}
with open(os.path.join(BASE, "result-entrega.json"), "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)
print(json.dumps(resultado, ensure_ascii=False, indent=2))
