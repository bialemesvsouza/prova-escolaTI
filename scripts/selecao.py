#!/usr/bin/env python3
"""Selecao de track — listagem compartilhada das candidatas.

Candidatas = dummy permanente (`exams/dummy-exam/`, fora da hierarquia de
ano) + as tracks do ANO MAIS RECENTE (`exams/<ano>/<track>/`). Usado por:

- aplicar_prova.py  — match da .prova/track e stall com as opcoes;
- setup_prova.py    — lista de provas no comentario de boas-vindas;
- preparar_entrega.py — validacao imediata do /track.

O fetch do template segue o mesmo padrao em todos os scripts: remote
`prova-template`, TEMPLATE_URL (repo publico, sem PAT), FETCH_HEAD. Reposit-
orio gerado a partir do template NAO e fork — o remote e adicionado pelo
sistema na hora de listar/aplicar.
"""
import os
import re
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMMY = "exams/dummy-exam"  # prova-teste PERMANENTE, fora da hierarquia de ano
REMOTE = "prova-template"


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=BASE,
                          capture_output=True, text=True)


def fetch_template(template_url: str) -> bool:
    """Adiciona/atualiza o remote do template e faz fetch (main -> FETCH_HEAD).

    Fetch COMPLETO de proposito: um fetch --depth 1 marca o repo como shallow
    e o push seguinte (commit do bot de aplicacao) e rejeitado com "shallow
    update not allowed". O template e pequeno — o custo e irrelevante."""
    git("remote", "remove", REMOTE)
    git("remote", "add", REMOTE, template_url)
    return git("fetch", REMOTE, "main").returncode == 0


def pastas_publicadas(ref: str = "FETCH_HEAD"):
    """Pastas de prova publicadas numa ref: dummy + exams/<ano>/<track>/."""
    r = git("ls-tree", "-r", "--name-only", ref)
    pastas = {m.group(1)
              for m in re.finditer(r"^(exams/\d{4}/[^/]+)/", r.stdout, re.M)}
    if re.search(r"^exams/dummy-exam/", r.stdout, re.M):
        pastas.add(DUMMY)
    return sorted(pastas)


def candidatas(pastas):
    """Candidatas de selecao: dummy + tracks do ano mais recente."""
    anos = sorted({p.split("/")[1] for p in pastas
                   if re.match(r"exams/\d{4}/", p)})
    ano = anos[-1] if anos else ""
    return sorted(p for p in pastas
                  if p == DUMMY or (ano and p.split("/")[1] == ano))


def nomes(pastas):
    """Nomes de pasta (para /track e para exibicao)."""
    return sorted(os.path.basename(p) for p in pastas)
