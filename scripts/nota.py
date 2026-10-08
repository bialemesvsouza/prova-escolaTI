#!/usr/bin/env python3
"""Agrega os resultados dos jobs em nota.json e no GitHub Step Summary.

Le o teto de pontos (`nota_max` + `extras_max`) da rubrica da pasta do ano,
quando aplicada.

Uso (job de nota, artefatos baixados em ./resultados):
    python scripts/nota.py            # ou, explicitamente:
    python scripts/nota.py resultados
"""
import glob
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
from variante import pasta_do_ano  # noqa: E402

DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd(), "resultados")

teto = 100
extras_teto = 0
try:
    pasta = pasta_do_ano(BASE)
    candidatos = [os.path.join(BASE, "rubrica.json")]
    if pasta:
        candidatos.append(os.path.join(BASE, pasta, "rubrica.json"))
    for alvo in candidatos:
        if os.path.exists(alvo):
            rubrica = json.load(open(alvo, encoding="utf-8"))
            teto = int(rubrica.get("nota_max", 100))
            extras_teto = int(rubrica.get("extras_max", 0))
            break
except Exception:
    pass

criterios, fatal_geral, observacoes = [], [], []
for path in sorted(glob.glob(os.path.join(DIR, "result-*.json"))):
    try:
        dados = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        observacoes.append("Nao foi possivel ler %s (%s)." % (os.path.basename(path), e))
        continue
    fatal_geral += dados.get("fatal", [])
    if "pontos" in dados:
        criterios.append(dados)
    elif "criterios" in dados:
        criterios.extend(dados["criterios"])
    observacoes += dados.get("obs", [])


def eh_extra(c):
    return bool(c.get("extra")) or str(c.get("criterio", "")).lower().startswith("extra")


extras = sum(c.get("pontos", 0) for c in criterios if eh_extra(c))
base = sum(c.get("pontos", 0) for c in criterios if not eh_extra(c))

if fatal_geral:
    nota = 0
else:
    nota = min(teto + extras_teto, base + extras)

linhas = ["# Nota parcial — Auto-correcao", "",
          "| Criterio | Pontos |", "| --- | --- |"]
if criterios:
    for c in criterios:
        linhas.append("| %s | %d/%d |" % (c.get("criterio", c.get("job", "?")),
                                          c.get("pontos", 0), c.get("max", 0)))
else:
    linhas.append("| (nenhum criterio executado) | 0 |")
linhas += ["", "**Nota parcial:** %d/%d (base %d + extras %d)"
           % (nota, teto + extras_teto, base, extras)]
if fatal_geral:
    linhas += ["", "### Motivos de zeramento", ""] + ["- " + f for f in fatal_geral]
if observacoes:
    linhas += ["", "### Observacoes", ""] + ["- " + o for o in observacoes]

summary = os.environ.get("GITHUB_STEP_SUMMARY")
if summary:
    with open(summary, "a", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
print("\n".join(linhas))

with open(os.path.join(os.getcwd(), "nota.json"), "w", encoding="utf-8") as f:
    json.dump({"nota": nota, "teto": teto, "criterios": criterios,
               "fatal": fatal_geral, "observacoes": observacoes},
              f, ensure_ascii=False, indent=2)

# replica a nota na issue unica da prova (upsert por marcador — nao spamma).
# O corpo do comentario carrega "Ultima atualizacao" (ISO + link da run) e um
# historico cronologico dos disparos (ate 10 entradas) — o aluno enxerga que
# e sempre o MESMO comentario editado. O fechar-prova faz parse da linha
# "**Nota parcial:** N/100" — mantida intacta.
try:
    from datetime import datetime  # noqa: E402
    import prova_issue  # noqa: E402

    iso = datetime.now().astimezone().isoformat(timespec="seconds")
    run_url = ""
    if os.environ.get("GITHUB_RUN_ID") and os.environ.get("GITHUB_REPOSITORY"):
        run_url = "%s/%s/actions/runs/%s" % (
            os.environ.get("GITHUB_SERVER_URL", "https://github.com"),
            os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_RUN_ID"])

    anterior = None
    n_issue = prova_issue.numero()
    if n_issue and prova_issue.TOKEN and prova_issue.REPO_FULL:
        status, comentarios = prova_issue._api(
            "GET", "/repos/%s/issues/%s/comments?per_page=100"
            % (prova_issue.REPO_FULL, n_issue))
        if status == 200 and isinstance(comentarios, list):
            for c in comentarios:
                if (c.get("body") or "").startswith("<!-- nota-parcial -->"):
                    anterior = c.get("body")
                    break
    historico = []
    if anterior and "### Histórico" in anterior:
        secao = anterior.split("### Histórico", 1)[1]
        historico = [l for l in secao.splitlines() if l.strip().startswith("- ")]
    entrada = "- %s · nota %d/%d%s" % (
        iso, nota, teto + extras_teto, " · [run](%s)" % run_url if run_url else "")
    historico = (historico + [entrada])[-10:]

    texto_issue = "\n".join(
        ["# Nota parcial — Auto-correção", "",
         "**Última atualização:** %s%s" % (
             iso, " · [ver run](%s)" % run_url if run_url else ""),
         ""] + linhas[2:] + ["", "### Histórico"] + historico)
    prova_issue.atualizar_comentario("nota-parcial", texto_issue)
except Exception as e:
    print("comentario de nota na issue falhou (%s) — seguindo." % e)
