#!/usr/bin/env python3
"""Criterio E (checklist mecanico dos .md) — generico, para tracks de
especificacao (o entregavel e markdown, nao codigo).

Config via track.json (raiz, pos-overlay), secao suites.md:
    {"pontos": 15, "pts_por_arquivo": 3, "max_linhas_bloco": 20}
Defaults: 15 pontos, 3 pts por .md "bem criado" (teto = pontos), blocos de
codigo de ate 20 linhas.

fatal: qualquer bloco de codigo com mais de max_linhas_bloco linhas em .md
       -> implementacao colada -> prova zerada (o job de nota aplica o zero;
       aqui o fatal NAO falha o CI, para o feedback do criterio E continuar
       visivel no Summary).
"""
import glob
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
import track_lock  # noqa: E402

_cfg = track_lock.load(BASE).get("suites", {}).get("md", {})
PONTOS = int(_cfg.get("pontos", 15))
PTS_ARQUIVO = int(_cfg.get("pts_por_arquivo", 3))
MAX_LINHAS_BLOCO = int(_cfg.get("max_linhas_bloco", 20))

# Arquivos do esqueleto/template nao pontuam como especificacao do aluno.
EXCLUIR = {"README.md", "ENUNCIADO.md", "ALUNO.md", "FONTES.md", "CHANGELOG.md"}
EXCLUIR_PREFIXOS = (".github/", "scripts/", "docs/", "tests/", "variante/",
                    "correcao/", "gabarito/", ".prova/", "exams/")

CHECKS = [
    # (regex de nome, verificador, descricao)
    (r"constitution\.md$", lambda t: len(re.findall(r"^#", t, re.M)) >= 1
     and len(re.findall(r"(deve|nunca|sempre|obrigatorio|proibido)", t, re.I)) >= 1,
     ">=1 regra operacional"),
    (r"spec\.md$", lambda t: len(re.findall(r"(criterio de aceite|aceite)", t, re.I)) >= 1
     and len(re.findall(r"\d", t)) >= 1,
     ">=1 criterio de aceite mensuravel por UC"),
    (r"plan\.md$", lambda t: len(re.findall(r"(porque|pois|justificativa|motivo|decisao)", t, re.I)) >= 1,
     ">=1 decisao tecnica com justificativa"),
    (r"tests\.md$", lambda t: len(re.findall(r"(borda|limite|adjacente|arredond|teto|exat|\+1|zero|negativ)", t, re.I)) >= 1,
     ">=1 caso de borda por regra"),
    (r"tasks\.md$", lambda t: len(re.findall(r"^\s*[-*]\s+\S", t, re.M)) >= 3,
     ">=3 tarefas decompostas"),
    (r".*\.md$", lambda t: len(re.findall(r"^#", t, re.M)) >= 1
     and len(t.split()) >= 40,
     "estruturado: headers + especificacao concreta"),
]


def blocos_codigo(texto):
    """retorna lista com o nº de linhas de cada bloco de fence (``` ou mais).

    Regras CommonMark que o parser ingenuo errava: fence de abertura so fecha
    com fence de MESMO tamanho ou maior (evasao com 4 crases), e fence inline
    de uma linha (```codigo```) nao abre bloco (falso fatal)."""
    blocos, fence_len, atual = [], 0, 0
    for linha in texto.splitlines():
        m = re.match(r"^\s*(`{3,})(.*)$", linha)
        if fence_len == 0:
            if m and "`" not in m.group(2):
                fence_len = len(m.group(1))
                atual = 0
        else:
            if m and len(m.group(1)) >= fence_len and not m.group(2).strip():
                blocos.append(atual)
                fence_len = 0
            else:
                atual += 1
    if fence_len:
        blocos.append(atual)
    return blocos


def main():
    mds = []
    for p in glob.glob(os.path.join(BASE, "**", "*.md"), recursive=True):
        rel = os.path.relpath(p, BASE).replace(os.sep, "/")
        if rel in EXCLUIR or rel.startswith(EXCLUIR_PREFIXOS):
            continue
        mds.append(rel)

    fatal, pontuados, detalhes = [], [], []

    for rel in sorted(mds):
        texto = open(os.path.join(BASE, rel), encoding="utf-8", errors="replace").read()
        grandes = [n for n in blocos_codigo(texto) if n > MAX_LINHAS_BLOCO]
        if grandes:
            fatal.append("%s contem bloco de codigo de %d linhas (> %d) — "
                         "implementacao colada nos .md: prova zerada."
                         % (rel, max(grandes), MAX_LINHAS_BLOCO))
            continue
        for padrao, verifica, desc in CHECKS:
            if re.search(padrao, rel) and verifica(texto):
                pontuados.append((rel, desc))
                break
        else:
            detalhes.append("%s: nao satisfez nenhum item do checklist." % rel)

    pontos = min(PONTOS, PTS_ARQUIVO * len(pontuados))
    for rel, desc in pontuados:
        detalhes.append("+%d pts: %s (%s)" % (PTS_ARQUIVO, rel, desc))

    resultado = {
        "job": "md", "criterio": "E", "pontos": pontos, "max": PONTOS,
        "fatal": fatal, "detalhes": detalhes,
        "obs": ["Criterios avaliados na correcao docente (modelo fixo + suite "
                "escondida) NAO aparecem nesta nota parcial."],
    }
    with open(os.path.join(BASE, "result-md.json"), "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    # fatal aqui nao falha o CI sozinho: a nota final zera via job de nota
    # (mantem o feedback do criterio E visivel no Summary).


if __name__ == "__main__":
    main()
