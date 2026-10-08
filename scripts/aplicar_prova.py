#!/usr/bin/env python3
"""Aplica a pasta do ano publicada no template (exam-escola-ti).

Gatilhos: schedule (polling a cada 10 min), push, issue_comment e
workflow_dispatch. Idempotente via `.prova/aplicada-<pasta>`.

A aplicacao e CONSEQUENCIA da SELECAO (issueops) — com um detalhe real de
plataforma: **pushes feitos com GITHUB_TOKEN NAO disparam workflows** (regra
anti-recursao do GitHub), entao o commit do bot que grava `.prova/track` NAO
dispara este workflow por push. Por isso o comentario `/track <nome>` na issue
TAMBEM dispara este workflow (issue_comment) e aplica na hora — sem esperar o
commit do bot (evita corrida). O schedule (<=10 min) e o backstop; o push
continua cobrindo commits normais do aluno e re-runs.

Fluxo:
  1. SELECAO = `/track <nome>` do comentario (env ISSUE_COMMENT_BODY) ou, em
     push/schedule, fallback no `.prova/track` (gravado pelo preparar_entrega
     em commit de bot — necessario para repos clonados na mao/re-runs). Sem
     nenhuma das fontes: sys.exit(0) SILENCIOSO (o push de criacao do repo
     vira no-op quieto);
  2. fetch do remote do template (repo publico — sem PAT; o remote
     `prova-template` e adicionado pelo sistema porque o repo gerado a
     partir do template NAO e fork);
  3. monta as CANDIDATAS (scripts/selecao.py): dummy permanente + ano mais
     recente. Nome que nao bate TRAVA e comenta o lembrete na issue (upsert
     `<!-- track-lembrete -->` + sentinela `.prova/track-lembrete`, para nao
     spammar a cada polling);
  4. se ainda nao aplicada: `git checkout <ref> -- <pasta>`, sentinela,
     commit do bot (esse commit ancora o t0 da janela — T4) e push;
  5. gera .prova/exam-dir + variante/params.json e COMENTA na issue unica da
     prova (pasta aplicada, janela, parametros) — nao cria issue nova.

DRY_RUN=1 so descobre a pasta (local ou remoto) sem commitar.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
from variante import slug_do_repo, pasta_do_ano, variante  # noqa: E402
import prova_issue  # noqa: E402
import selecao  # noqa: E402

TOKEN = os.environ.get("GH_TOKEN", "")
REPO_FULL = os.environ.get("REPO_FULL", "")
REPO = os.environ.get("REPO_SLUG") or slug_do_repo()
TEMPLATE_URL = os.environ.get(
    "TEMPLATE_URL", "https://github.com/endersonmenezes/exam-escola-ti.git")
DRY_RUN = os.environ.get("DRY_RUN", "") == "1"


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=BASE,
                          capture_output=True, text=True)


def api(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request("https://api.github.com" + path,
                                 data=data, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError:
        return 0, {}


def main():
    # 0) este script so faz sentido DENTRO de um repositorio git (o do aluno)
    if git("rev-parse", "--is-inside-work-tree").stdout.strip() != "true":
        print("Este diretorio nao e um repositorio git — aplicar_prova so roda "
              "no repo do aluno (workflow). Abortando.")
        return
    if os.environ.get("REPO_FULL", "") == "endersonmenezes/exam-escola-ti":
        print("Repositorio-template — nao e uma prova; no-op.")
        return

    # v3.2: a selecao vem do COMENTARIO /track <nome> (ISSUE_COMMENT_BODY) ou,
    # em push/schedule, do .prova/track (commit do bot do preparar_entrega —
    # cobre repos clonados na mao e re-runs; o push desse commit NAO disparia
    # este workflow, por isso o comentario e o disparo real). Sem nenhuma das
    # fontes: no-op SILENCIOSO — nem fetch, nem comentario.
    corpo_comentario = os.environ.get("ISSUE_COMMENT_BODY", "")
    track_comentario = ""
    if corpo_comentario:
        m = re.search(r"(?im)^\s*/track\s+([\w-]+)", corpo_comentario)
        if m:
            track_comentario = m.group(1)
    track_arquivo = ""
    track_path = os.path.join(BASE, ".prova", "track")
    if os.path.exists(track_path):
        track_arquivo = open(track_path, encoding="utf-8").read().strip()
    track_marcada = track_comentario or track_arquivo
    if not track_marcada:
        sys.exit(0)

    # 1) remote + fetch (repo publico; GITHUB_TOKEN do proprio repo basta)
    if not selecao.fetch_template(TEMPLATE_URL):
        print("Template ainda nao acessivel (%s)." % TEMPLATE_URL)
        return

    pastas = selecao.pastas_publicadas("FETCH_HEAD")
    if not pastas:
        print("Nenhuma pasta de prova publicada no template ainda.")
        return

    # 2) candidatas = dummy permanente + tracks do ANO MAIS RECENTE (selecao.py).
    #    Nome que nao bate TRAVA e lembra UMA vez na issue (upsert + sentinela).
    candidatas = selecao.candidatas(pastas)
    escolhidas = [p for p in candidatas
                  if os.path.basename(p) == track_marcada]
    if not escolhidas:
        opcoes = [("%s (prova-teste)" % p) if p == selecao.DUMMY else p
                  for p in candidatas]
        print("Track '%s' nao encontrada entre as candidatas: %s."
              % (track_marcada, ", ".join(opcoes)))
        if not DRY_RUN:
            texto_issue = (
                "⚠️ **Seleção da track obrigatória.** Candidatas: %s.\n\n"
                "Comente `/track <nome-da-pasta>` nesta issue para escolher a "
                "prova (ex.: `/track crud-fullstack`; para a prova-teste, "
                "`/track dummy-exam`)." % ", ".join(opcoes))
            prova_issue.atualizar_comentario("track-lembrete", texto_issue)
            lembrete = os.path.join(BASE, ".prova", "track-lembrete")
            if not os.path.exists(lembrete):
                with open(lembrete, "w", encoding="utf-8") as f:
                    f.write("ok\n")
                # sentinela precisa ser commitada para sobreviver ao poll
                git("config", "user.name", "github-actions[bot]")
                git("config", "user.email",
                    "41898282+github-actions[bot]@users.noreply.github.com")
                git("add", ".prova/track-lembrete")
                if git("commit", "-m",
                       "chore: lembrete de /track enviado na issue").returncode == 0:
                    git("pull", "--rebase")
                    git("push")
        return
    pasta = escolhidas[-1]
    print("Pasta da prova escolhida:", pasta)

    if DRY_RUN:
        print("DRY_RUN — nada aplicado.")
        return

    # 3) sentinela
    os.makedirs(os.path.join(BASE, ".prova"), exist_ok=True)
    sentinela = os.path.join(BASE, ".prova", "aplicada-" + pasta.replace("/", "-"))
    if os.path.exists(sentinela):
        print("Prova ja aplicada (%s) — no-op." % pasta)
        return

    # 4) checkout da pasta e OVERLAY: a track VIRA o repositorio do aluno
    git("checkout", "FETCH_HEAD", "--", pasta)
    # grava o SHA do template usado — o tamper-check (T3) compara contra ELE,
    # nao contra o HEAD futuro do template
    fetch_head = git("rev-parse", "FETCH_HEAD").stdout.strip()
    if fetch_head:
        with open(os.path.join(BASE, ".prova", "template-ref"), "w",
                  encoding="utf-8") as f:
            f.write(fetch_head + "\n")
    origem = os.path.join(BASE, pasta)
    BLOQUEADOS = {"scripts", ".github", "docs", ".gitignore", ".prova", "tests"}
    colisoes = sorted(set(os.listdir(origem)) & BLOQUEADOS)
    if colisoes:
        print("ABORTADO: pasta da prova contem item que pertence ao esqueleto: %s"
              % ", ".join(colisoes))
        return
    for nome in sorted(os.listdir(origem)):
        if nome == "AVISO-DUMMY.md":
            continue  # aviso interno do dummy nao vai para o repo do aluno
        if nome == "tests_publicos.py":
            destino = os.path.join(BASE, "tests", "public", "test_publicos.py")
        else:
            destino = os.path.join(BASE, nome)
        if os.path.isdir(destino) and not os.path.islink(destino):
            shutil.rmtree(destino)
        elif os.path.exists(destino):
            os.remove(destino)
        if os.path.dirname(destino):
            os.makedirs(os.path.dirname(destino), exist_ok=True)
        shutil.move(os.path.join(origem, nome), destino)
    git("rm", "-r", "--quiet", "--cached", pasta)
    if os.path.isdir(origem):
        shutil.rmtree(origem)

    with open(sentinela, "w", encoding="utf-8") as f:
        f.write(pasta + "\n")
    with open(os.path.join(BASE, ".prova", "exam-dir"), "w", encoding="utf-8") as f:
        f.write(pasta + "\n")

    # 5) janela (enforcement e divulgação usam janela_minutos da rubrica) e
    #    variante agora computavel
    janela = 120
    rubrica_path = os.path.join(BASE, "rubrica.json")
    if os.path.exists(rubrica_path):
        janela = int(json.load(open(rubrica_path, encoding="utf-8"))
                     .get("janela_minutos", 120))
    v = variante(REPO)
    os.makedirs(os.path.join(BASE, "variante"), exist_ok=True)
    with open(os.path.join(BASE, "variante", "params.json"), "w", encoding="utf-8") as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
    # selecao ja aconteceu: o lembrete de /track sai (entra neste commit)
    lembrete = os.path.join(BASE, ".prova", "track-lembrete")
    if os.path.exists(lembrete):
        os.remove(lembrete)

    # 6) commit do bot (t0 da janela) + push
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email",
        "41898282+github-actions[bot]@users.noreply.github.com")
    git("add", "-A")
    git("commit", "-m", "chore: aplicar prova %s (janela: %d min)" % (pasta, janela))
    git("pull", "--rebase")
    r = git("push")
    if r.returncode != 0:
        print("push falhou:", r.stderr)
        return

    # 7) comentario na issue UNICA da prova (nada de issue nova)
    if TOKEN and REPO_FULL:
        n_issue = prova_issue.numero()
        DESCRICOES = {
            "PREFIXO": "nome que a suíte envia em `/saudar` (o `nome` da sua saudação)",
            "RAZAO_PREFERENCIAL": "valor de `repeticoes` usado no teste da sua variante",
            "PORTA_API": "porta em que a suíte sobe SEU container (mapeada para 8080 dentro dele)",
            "EXAM_DIR": "pasta da prova aplicada",
        }
        params = "\n".join(
            "- `%s` = %s — %s" % (k, val, DESCRICOES[k]) if k in DESCRICOES
            else "- `%s` = %s" % (k, val)
            for k, val in v.items() if k != "slug")
        corpo = ("## ✅ Prova aplicada neste repositorio\n\n"
                 "Pasta: `%s` — a janela da prova é de **%d minutos**, "
                 "contados a partir do commit de aplicacao. O relogio ja esta "
                 "rodando.\n\n"
                 "Sua variante (unica do seu repo):\n\n%s\n\n"
                 "> Leia o contrato, desenvolva, preencha `FONTES.md` se "
                 "consultar algo e de push antes do fim da janela. A nota "
                 "parcial sai no workflow *Auto-correcao* (Summary + "
                 "comentario nesta issue).\n\n"
                 "**Ao final, voce fecha esta issue para encerrar a prova** — "
                 "o sistema gera o `teacher.json` de entrega."
                 % (pasta, janela, params))
        if n_issue:
            api("POST", "/repos/%s/issues/%s/labels" % (REPO_FULL, n_issue),
                ["prova-aplicada"])
            api("POST", "/repos/%s/issues/%s/comments" % (REPO_FULL, n_issue),
                {"body": corpo})
            print("Comentario de aplicacao postado na issue #%s." % n_issue)
        else:
            print("Lock .prova/issue ausente — comentario de aplicacao nao postado.")
    print("Prova %s aplicada com sucesso." % pasta)


if __name__ == "__main__":
    main()
