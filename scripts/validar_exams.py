#!/usr/bin/env python3
"""Valida as pastas de prova em exams/ — roda no CI do TEMPLATE (push na main).

Erros (exit 1): track.json invalido (campos obrigatorios, tipos, valores de
workflows nao-booleanos), contrato.json sem a secao variante com as chaves
exatas, rubrica.json sem nota_max/janela_minutos, item da pasta colidindo
com o esqueleto.
Avisos (exit 0): mais de uma track no mesmo ano, dummy permanente publicado.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMS = os.path.join(BASE, "exams")
BLOQUEADOS = {"scripts", ".github", "docs", ".gitignore", ".prova", "tests"}
VARIANTE_OBRIGATORIAS = {"PREFIXOS": list, "RAZOES": list,
                         "PORTA_BASE": int, "FAIXA": int}


def validar_extras(extras, prefixo):
    """Cada entrada: {"opcoes": list} OU {"base": int, "faixa": int[, "passo": int]}."""
    falhas = []
    if not isinstance(extras, dict):
        return ["%s: contrato.json variante.extras deve ser objeto" % prefixo]
    for nome, cfg in extras.items():
        if not isinstance(cfg, dict):
            falhas.append("%s: variante.extras.%s deve ser objeto" % (prefixo, nome))
        elif "opcoes" in cfg:
            if not isinstance(cfg["opcoes"], list) or not cfg["opcoes"]:
                falhas.append("%s: variante.extras.%s.opcoes deve ser lista nao-vazia"
                              % (prefixo, nome))
        elif not (isinstance(cfg.get("base"), int) and isinstance(cfg.get("faixa"), int)):
            falhas.append("%s: variante.extras.%s precisa de opcoes(list) ou "
                          "base(int)+faixa(int)" % (prefixo, nome))
        else:
            if cfg["faixa"] < 1:
                falhas.append("%s: variante.extras.%s.faixa deve ser >= 1"
                              % (prefixo, nome))
            if "passo" in cfg and not isinstance(cfg["passo"], int):
                falhas.append("%s: variante.extras.%s.passo deve ser int"
                              % (prefixo, nome))
            fmt = cfg.get("formato")
            if fmt is not None and (not isinstance(fmt, str) or fmt.count("%") != 1):
                falhas.append("%s: variante.extras.%s.formato deve ser string com "
                              "exatamente 1 placeholder (ex.: prova_%%02d)"
                              % (prefixo, nome))
    return falhas

erros, avisos = [], []

if not os.path.isdir(EXAMS):
    print("exams/ ausente — nenhuma prova publicada.")
    sys.exit(0)

por_ano = {}
pastas = []  # (prefixo de exibicao, caminho) — dummy + tracks dos anos
dummy = os.path.join(EXAMS, "dummy-exam")
if os.path.isdir(dummy):
    pastas.append(("exams/dummy-exam", dummy))
for ano in sorted(os.listdir(EXAMS)):
    dir_ano = os.path.join(EXAMS, ano)
    if not os.path.isdir(dir_ano) or not ano.isdigit():
        continue
    tracks = sorted(d for d in os.listdir(dir_ano)
                    if os.path.isdir(os.path.join(dir_ano, d)))
    por_ano[ano] = tracks
    if len(tracks) > 1:
        avisos.append("%s: %d tracks publicadas juntas (%s) — confirme a "
                      "selecao via /track na issue" % (ano, len(tracks), ", ".join(tracks)))
    for track in tracks:
        pastas.append(("exams/%s/%s" % (ano, track), os.path.join(dir_ano, track)))

for prefixo, pasta in pastas:
    if prefixo == "exams/dummy-exam":
        avisos.append("exams/dummy-exam: dummy permanente publicado — "
                      "esperado; entra como candidato de selecao em qualquer ano")
    for item in os.listdir(pasta):
        if item in BLOQUEADOS:
            erros.append("%s: item '%s' colide com o esqueleto" % (prefixo, item))
    # track.json
    tj = os.path.join(pasta, "track.json")
    if not os.path.exists(tj):
        erros.append("%s: track.json ausente" % prefixo)
    else:
        try:
            lock = json.load(open(tj, encoding="utf-8"))
        except ValueError:
            lock = None
            erros.append("%s: track.json nao e JSON valido" % prefixo)
        if isinstance(lock, dict):
            for campo, tipo in (("track", str), ("lockfile_version", int),
                                ("workflows", dict), ("recursos", dict)):
                if not isinstance(lock.get(campo), tipo):
                    erros.append("%s: track.json campo '%s' deve ser %s"
                                 % (prefixo, campo, tipo.__name__))
            wf = lock.get("workflows")
            if isinstance(wf, dict):
                try:
                    from track_lock import KNOWN_WORKFLOW_KEYS
                    conhecidas = {k.split(".", 1)[1] for k in KNOWN_WORKFLOW_KEYS}
                except Exception:
                    conhecidas = set()
                for chave, valor in wf.items():
                    if not isinstance(valor, bool):
                        erros.append("%s: track.json workflows.%s deve ser true/false"
                                     % (prefixo, chave))
                    elif conhecidas and chave not in conhecidas:
                        avisos.append("%s: track.json workflows.%s NAO e chave "
                                      "conhecida (typo?) — sera ignorada"
                                      % (prefixo, chave))
    # contrato.json
    cj = os.path.join(pasta, "contrato.json")
    if not os.path.exists(cj):
        erros.append("%s: contrato.json ausente" % prefixo)
    else:
        try:
            contrato = json.load(open(cj, encoding="utf-8"))
            variante = contrato["variante"]
            if "extras" in variante:
                erros.extend(validar_extras(variante["extras"], prefixo))
            else:
                # sem extras, as tabelas nucleo sao obrigatorias
                for chave, tipo in VARIANTE_OBRIGATORIAS.items():
                    if not isinstance(variante.get(chave), tipo):
                        erros.append("%s: contrato.json variante.%s deve ser %s"
                                     % (prefixo, chave, tipo.__name__))
        except KeyError as e:
            erros.append("%s: contrato.json sem secao %s" % (prefixo, e))
        except ValueError:
            erros.append("%s: contrato.json nao e JSON valido" % prefixo)
    # rubrica.json
    rj = os.path.join(pasta, "rubrica.json")
    if not os.path.exists(rj):
        erros.append("%s: rubrica.json ausente" % prefixo)
    else:
        try:
            rubrica = json.load(open(rj, encoding="utf-8"))
            if "nota_max" not in rubrica or "janela_minutos" not in rubrica:
                erros.append("%s: rubrica.json sem nota_max/janela_minutos" % prefixo)
        except ValueError:
            erros.append("%s: rubrica.json nao e JSON valido" % prefixo)

for a in avisos:
    print("AVISO:", a)
for e in erros:
    print("ERRO:", e)
print("exams validados: %d pasta(s), %d ano(s)" % (len(pastas), len(por_ano)))
sys.exit(1 if erros else 0)
