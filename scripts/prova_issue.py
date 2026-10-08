#!/usr/bin/env python3
"""Issue unica da prova — helper compartilhado (lock em .prova/issue).

O setup cria UMA issue "🎯 Prova" que vive durante todo o ciclo (preparacao,
selecao, aplicacao, nota parcial e fechamento). O numero fica gravado em
`.prova/issue` (lockfile, commit do bot). Motivo do lock: o aluno pode usar
os proprios issues do repo para se organizar — a nossa issue e identificavel
pelo lock, nao pelo titulo de evento.

Caso de corrida (v3.3): a geracao do repo a partir do template dispara DOIS
pushes quase simultaneos -> dois runs de setup em paralelo -> duas issues.
A sentinela LOCAL nao basta (TOCTOU — ambos leem antes de qualquer um
escrever). Por isso a idempotencia e de RECURSO (setup adota/reconcilia) e
este helper AUTO-CURA locks antigos: se `.prova/issue` apontar para issue
inexistente/fechada/trocada, adota a issue aberta "🎯 Prova" e regrava o
lock (commit de bot, quando possivel; senao so em memoria).

    numero()                            -> int | None
    comentar(texto)                     -> cria comentario (one-shot)
    atualizar_comentario(marcador, txt) -> upsert: edita o comentario que
        comeca com `<!-- marcador -->`, senao cria — para nao spammar a
        issue a cada push.

Usa GH_TOKEN e REPO_FULL do ambiente (mesmo contrato dos demais scripts).
"""
import json
import os
import subprocess
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TOKEN = os.environ.get("GH_TOKEN", "")
REPO_FULL = os.environ.get("REPO_FULL", "")
TITULO = "🎯 Prova"


def _api(method, path, payload=None):
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


def _aberta_na_api():
    """Numero da issue aberta com titulo exato TITULO, ou None."""
    if TOKEN and REPO_FULL:
        status, dados = _api("GET", "/repos/%s/issues?state=open&per_page=50"
                             % REPO_FULL)
        if status == 200 and isinstance(dados, list):
            for issue in dados:
                if issue.get("title") == TITULO:
                    return issue.get("number")
    return None


def _lock_stale(n):
    """True se a issue do lock nao existir, estiver fechada ou for outra."""
    if not (TOKEN and REPO_FULL):
        return False  # sem API nao da para validar — confia no lock
    status, dados = _api("GET", "/repos/%s/issues/%s" % (REPO_FULL, n))
    return not (status == 200 and dados.get("state") == "open"
                and dados.get("title") == TITULO)


def _gravar_lock(n):
    """Regrava .prova/issue em commit de bot (best-effort)."""
    try:
        os.makedirs(os.path.join(BASE, ".prova"), exist_ok=True)
        with open(os.path.join(BASE, ".prova", "issue"), "w",
                  encoding="utf-8") as f:
            f.write("%d\n" % n)
        for args in (["config", "user.name", "github-actions[bot]"],
                     ["config", "user.email",
                      "41898282+github-actions[bot]@users.noreply.github.com"],
                     ["add", ".prova/issue"],
                     ["commit", "-m", "chore: lock da issue corrigido (#%d)" % n],
                     ["pull", "--rebase"],
                     ["push"]):
            subprocess.run(["git"] + args, cwd=BASE, capture_output=True)
    except OSError:
        pass


def numero(base: str = BASE):
    """Numero da issue da prova.

    Lock valido -> o numero. Lock stale (issue fechada/inexistente/outra —
    ex.: corrida antiga do setup) -> adota a aberta e regrava o lock. Sem
    lock -> fallback via API. Sem API -> confia no que estiver em disco.
    """
    lock = os.path.join(base, ".prova", "issue")
    n = None
    if os.path.exists(lock):
        try:
            n = int(open(lock, encoding="utf-8").read().strip())
        except ValueError:
            n = None
    if n is not None:
        if not _lock_stale(n):
            return n
        adotada = _aberta_na_api()
        if adotada and adotada != n:
            print("Lock .prova/issue #%d stale — adotando issue #%d." % (n, adotada))
            _gravar_lock(adotada)
            return adotada
        return n  # ex.: prova encerrada de proposito — mantem o lock
    return _aberta_na_api()


def comentar(texto: str):
    """Cria comentario na issue da prova. Retorna id ou None."""
    n = numero()
    if not (n and TOKEN and REPO_FULL):
        return None
    status, dados = _api("POST", "/repos/%s/issues/%s/comments" % (REPO_FULL, n),
                         {"body": texto})
    return dados.get("id") if status == 201 else None


def atualizar_comentario(marcador: str, texto: str):
    """Upsert de comentario identificado por `<!-- marcador -->`."""
    n = numero()
    if not (n and TOKEN and REPO_FULL):
        return None
    marcacao = "<!-- %s -->" % marcador
    corpo = (marcacao + "\n" + texto).strip()
    status, comentarios = _api("GET", "/repos/%s/issues/%s/comments?per_page=100"
                               % (REPO_FULL, n))
    if status == 200 and isinstance(comentarios, list):
        for c in comentarios:
            if (c.get("body") or "").startswith(marcacao):
                _api("PATCH", "/repos/%s/issues/comments/%s"
                     % (REPO_FULL, c.get("id")), {"body": corpo})
                return c.get("id")
    status, dados = _api("POST", "/repos/%s/issues/%s/comments" % (REPO_FULL, n),
                         {"body": corpo})
    return dados.get("id") if status == 201 else None
