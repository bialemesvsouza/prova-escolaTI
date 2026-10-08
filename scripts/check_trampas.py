#!/usr/bin/env python3
"""Trampas — identidade, autoria, janela (auto-ancorada) e integridade.

Versao exam-escola-ti: a janela nao vem de ISO manual — ela e ancorada no
commit de aplicacao da prova ("chore: aplicar prova ...") + `janela_minutos`
da rubrica da pasta do ano. Inputs JANELA_INICIO/FIM continuam como fallback.

fatal  -> zera a prova automaticamente.
alerts -> suspeita, vai para revisao manual (nao zera sozinho).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
from variante import pasta_do_ano  # noqa: E402

# So o que o overlay do ano NUNCA toca entra aqui — contrato/rubrica/tests
# vivem na raiz pos-aplicacao e sao protegidos pela procedencia do commit de
# aplicacao, nao pela comparacao com o template.
PROTECTED = ["scripts", ".github", "docs"]
REPO = os.environ.get("REPO_SLUG") or os.path.basename(BASE)

alerts, fatal = [], []
login_aluno = ""


def sh(*args):
    return subprocess.run(list(args), capture_output=True, text=True, cwd=BASE).stdout


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def arvore(path):
    out = {}
    if os.path.isfile(path):
        out[os.path.basename(path)] = sha(path)
        return out
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            if name.endswith((".pyc", ".pyo")):
                continue
            full = os.path.join(root, name)
            out[os.path.relpath(full, path)] = sha(full)
    return out


# ---- T2: identidade canonica ----
id_path = os.path.join(BASE, ".prova", "id")
if not os.path.exists(id_path):
    alerts.append("FALTA .prova/id — rode `python scripts/variante.py` (ou aguarde o setup da prova).")
else:
    gravado = open(id_path, encoding="utf-8").read().strip()
    if gravado != REPO:
        fatal.append(".prova/id ('%s') != nome do repositorio ('%s') — "
                     "copia de outro repositorio detectada." % (gravado, REPO))

# ---- T5: ALUNO.md e autoria (ignorando commits de bot) ----
aluno_path = os.path.join(BASE, "ALUNO.md")
ra = None
if not os.path.exists(aluno_path):
    alerts.append("FALTA ALUNO.md (nome e RA) — obrigatorio na montagem da nota.")
else:
    texto = open(aluno_path, encoding="utf-8").read()
    m = re.search(r"RA\s*[:：]?\s*([0-9]{5,})", texto)
    if not m:
        alerts.append("ALUNO.md sem RA valido (5+ digitos).")
    else:
        ra = m.group(1)
    m_login = re.search(r"Conta GitHub\s*[:：]?\s*@?([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))",
                        texto)
    if m_login:
        login_aluno = m_login.group(1).lower()
    if "PREENCHER" in texto:
        alerts.append("ALUNO.md ainda com placeholder de RA.")
    if not re.search(r"nome\s*[:：]", texto, re.IGNORECASE):
        alerts.append("ALUNO.md sem campo Nome.")

log = sh("git", "log", "--format=%an|%ae|%ad", "--date=format:%Y-%m-%dT%H:%M:%S")
commits_todos = [l for l in log.splitlines() if l.strip()]


def eh_bot(linha):
    alvo = linha.lower()
    return any(m in alvo for m in ("github-actions", "[bot]",
                                   "noreply@github", "dependabot"))


commits = [c for c in commits_todos if not eh_bot(c)]
commits_bot = len(commits_todos) - len(commits)
if len(commits) == 0:
    alerts.append("Sem commits do aluno ainda (somente commits de bot).")
else:
    if len(commits) < 2:
        alerts.append("Apenas %d commit do aluno — entrega em lote unico e suspeita." % len(commits))
    autores = {(l.split("|")[0], l.split("|")[1]) for l in commits}
    if len(autores) > 2:
        alerts.append("%d autores diferentes no historico (ignorando bots) — revisar." % len(autores))
    if login_aluno:
        locais = {email.split("@")[0].lower() for _, email in autores}
        if login_aluno not in locais:
            alerts.append("Conta GitHub de ALUNO.md (@%s) nao bate com o "
                          "local-part de nenhum e-mail de autor — revisar "
                          "identidade." % login_aluno)

# ---- Rastreabilidade: FONTES.md ----
obs_fontes = []
fontes_path = os.path.join(BASE, "FONTES.md")
if not os.path.exists(fontes_path):
    obs_fontes.append("FONTES.md ausente — se houve qualquer consulta (site ou IA), "
                      "preencha e commite antes do fim da prova.")
else:
    texto_fontes = open(fontes_path, encoding="utf-8", errors="replace").read()
    linhas = texto_fontes.splitlines()
    tem_link = any(re.match(r"^\|\s*\d", l) and re.search(r"https?://\S+", l)
                   for l in linhas)
    declarou_vazio = any(
        re.match(r"^\W{0,3}\s*Nenhum", l)
        and ("utilizada" in l.lower() or "consultado" in l.lower())
        for l in linhas)
    if not (tem_link or declarou_vazio):
        obs_fontes.append("FONTES.md ainda com placeholder — declare as fontes "
                          "usadas OU escreva explicitamente que nada foi consultado.")

# ---- T4: janela AUTO (commit de aplicacao) com fallback manual ----
ini = fim = ""
pasta = pasta_do_ano(BASE)
if pasta:
    minutos = 120
    for alvo in (os.path.join(BASE, "rubrica.json"),
                 os.path.join(BASE, pasta, "rubrica.json")):
        if os.path.exists(alvo):
            try:
                minutos = int(json.load(open(alvo, encoding="utf-8"))
                             .get("janela_minutos", 120))
            except Exception:
                pass
            break
    t0_linha = sh("git", "log", "--format=%ad|%s|%an",
                  "--date=format:%Y-%m-%dT%H:%M:%S",
                  "--grep=aplicar prova", "-1").strip()
    # so o commit do BOT ancora a janela — um commit do aluno com a mesma
    # mensagem NAO pode re-ancorar (fraude de janela/procedencia)
    fraude_ancora = False
    if t0_linha and "github-actions" not in t0_linha.split("|")[-1].lower():
        fatal.append("Commit 'aplicar prova' mais recente NAO e do bot "
                     "(autor: %s) — possivel tentativa de re-ancorar a janela. "
                     "Prova zerada, revisao manual."
                     % t0_linha.split("|")[-1])
        t0_linha = ""
        fraude_ancora = True
    if t0_linha:
        ini = t0_linha.split("|")[0].strip()
        t0 = datetime.strptime(ini, "%Y-%m-%dT%H:%M:%S")
        fim = (t0 + timedelta(minutes=minutos)).strftime("%Y-%m-%dT%H:%M:%S")
    elif not fraude_ancora:
        fatal.append("Pasta da prova presente mas commit 'aplicar prova' ausente "
                     "no historico (force-push?) — prova zerada, revisao manual.")

    # ---- Procedencia: arquivos da prova nao podem mudar apos a aplicacao ----
    t0_hash = sh("git", "log", "--format=%H", "--author=github-actions",
                 "--grep=aplicar prova", "-1").strip()
    if t0_hash:
        protegidos = ["track.json", "contrato.json", "rubrica.json"]
        # tracks de especificacao trazem ENUNCIADO.md — tambem intocavel
        if os.path.exists(os.path.join(BASE, "ENUNCIADO.md")):
            protegidos.append("ENUNCIADO.md")
        # testes publicos chegam via overlay no commit de aplicacao — o aluno
        # nao pode edita-los/apaga-los (editar = zerar)
        if os.path.isdir(os.path.join(BASE, "tests", "public")):
            protegidos.append("tests/public")
        r = subprocess.run(["git", "diff", "--quiet", t0_hash, "--"] + protegidos,
                           cwd=BASE)
        if r.returncode != 0:
            fatal.append("Arquivo da prova (%s) alterado apos o commit de "
                         "aplicacao — prova zerada." % "/".join(protegidos))
else:
    alerts.append("Prova ainda nao aplicada (sem pasta do ano) — janela T4 nao avaliada.")

if not (ini and fim):
    ini, fim = os.environ.get("JANELA_INICIO", ""), os.environ.get("JANELA_FIM", "")


def norm(t):
    t = t.strip().replace(" ", "T")
    return (t + ":00")[:19]


pre_aplicacao = []
if ini and fim:
    ini, fim = norm(ini), norm(fim)
    # janela pega so quem PASSOU do fim; commits ANTES do t0 sao fase de
    # preparacao (preencher RA, FONTES.md, selecionar track) — informativo
    tardios = [l for l in commits if l.split("|")[2] > fim]
    pre_aplicacao = [l for l in commits if l.split("|")[2] < ini]
    if tardios:
        alerts.append("%d commit(s) do aluno DEPOIS do fim da janela (%s) — revisar."
                      % (len(tardios), fim))
    if pre_aplicacao:
        obs_fontes.append("%d commit(s) do aluno ANTES da aplicacao (fase de "
                          "preparacao) — informativo." % len(pre_aplicacao))
else:
    obs_fontes.append("Janela indisponivel (sem aplicacao nem dispatch manual) — T4 desarmado.")

# ---- T3: integridade contra o template remoto ----
token = os.environ.get("CORRECAO_TOKEN", "")
tpl = os.environ.get("TEMPLATE_REPO", "")
if token and tpl:
    tmp = tempfile.mkdtemp(prefix="tpl_")
    url = "https://x-access-token:%s@github.com/%s.git" % (token, tpl)
    r = subprocess.run(["git", "clone", url, tmp],
                       capture_output=True, text=True)
    # T3 compara contra o SHA do template DA APLICACAO (gravado pelo bot em
    # .prova/template-ref) — um push de fix no template DURANTE a prova nao
    # pode gerar falso tamper nos alunos
    ref_path = os.path.join(BASE, ".prova", "template-ref")
    if r.returncode == 0 and os.path.exists(ref_path):
        ref = open(ref_path, encoding="utf-8").read().strip()
        if ref:
            subprocess.run(["git", "checkout", "--quiet", ref], cwd=tmp,
                           capture_output=True, text=True)
    if r.returncode != 0:
        alerts.append("Falha ao clonar template '%s' para tamper-check — T3 nao executado." % tpl)
    else:
        for rel in PROTECTED:
            local = os.path.join(BASE, rel)
            remoto = os.path.join(tmp, rel)
            if not os.path.exists(local):
                fatal.append("Arquivo protegido REMOVIDO: %s." % rel)
                continue
            if not os.path.exists(remoto):
                alerts.append("Caminho protegido '%s' ausente no template — ignorado." % rel)
                continue
            loc = arvore(local)
            rem = arvore(remoto)
            diffs = [k for k in set(loc) | set(rem) if loc.get(k) != rem.get(k)]
            if diffs:
                fatal.append("Tamper detectado em '%s': %d arquivo(s) alterado(s): %s — prova zerada."
                             % (rel, len(diffs), ", ".join(sorted(diffs)[:5])))
else:
    # informacao de configuracao, NAO suspeita — vai para obs, nao para alerts
    obs_fontes.append("CORRECAO_TOKEN/TEMPLATE_REPO ausentes — tamper-check remoto (T3) NAO executado.")

# ---- saida ----
resultado = {"job": "trampas", "repo": REPO, "commits": len(commits),
             "commits_bot": commits_bot,
             "commits_pre_aplicacao": len(pre_aplicacao),
             "alerts": alerts, "fatal": fatal, "obs": obs_fontes}
with open(os.path.join(BASE, "result-trampas.json"), "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)

print(json.dumps(resultado, ensure_ascii=False, indent=2))
ghout = os.environ.get("GITHUB_OUTPUT")
if ghout:
    with open(ghout, "a", encoding="utf-8") as f:
        f.write("zerado=%s\n" % ("true" if fatal else "false"))
sys.exit(1 if fatal else 0)
