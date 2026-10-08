#!/usr/bin/env python3
"""FONTES.md — analise compartilhada: o CI (test_05) e o fechar_prova
(teacher.json) usam EXATAMENTE a mesma regra, para a contagens baterem.

- links: so contam URLs em linha de TABELA NUMERADA (| 1 | ... http...).
  URL em texto corrido ou em exemplo (ex.: "(Ex.: https://...)" do template)
  NAO conta. Deduplicadas (mesma URL em duas tabelas = 1 fonte), na ordem de
  aparicao.
- declarou_vazio: linha iniciando com "Nenhum..." que declara nada
  consultado/utilizado (site, fonte, IA, material, recurso) — alinhado ao
  teste publico test_05.
"""
import os
import re

VAZIO = re.compile(
    r"nenhum(a)?\s+(site|fonte|ia|material|recurso)\s*(externo|externa)?"
    r"\s+(foi\s+)?(consultado|consultada|utilizado|utilizada|usado|usada)",
    re.IGNORECASE)


def analizar(caminho):
    """Retorna {"presente": bool, "declarou_vazio": bool, "links": [urls]}."""
    if not os.path.exists(caminho):
        return {"presente": False, "declarou_vazio": False, "links": []}
    texto = open(caminho, encoding="utf-8", errors="replace").read()
    declarou_vazio, links = False, []
    for linha in texto.splitlines():
        if re.match(r"^\s*\|\s*\d+\s*\|", linha) and "http" in linha:
            for url in re.findall(r"https?://[^\s|)]+", linha):
                if url not in links:
                    links.append(url)
        if re.match(r"^\W{0,3}\s*Nenhum", linha) and VAZIO.search(linha):
            declarou_vazio = True
    return {"presente": True, "declarou_vazio": declarou_vazio, "links": links}
