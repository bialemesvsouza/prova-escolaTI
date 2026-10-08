"""Testes PUBLICOS da Prova 01 — Track 03 · Fila de Atendimento (exams/2026/track-03-crud).

Cada pasta do ano pode trazer seus proprios testes publicos; o workflow
*Aplicar prova* copia este arquivo para tests/public/ no repo do aluno.

A suíte sobe o container do aluno (scripts/rodar_testes.sh) e testa a API
contra os parametros da SUA variante — derivados do nome do repositorio
pelas mesmas tabelas do contrato (mesmo mecanismo de scripts/variante.py:
hash sha256 do slug, modulo o tamanho de cada tabela).

A suíte escondida da correcao segue o mesmo contrato, com muito mais casos —
ela NAO roda no CI do aluno (nota do CI e parcial).
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from variante import slug_do_repo, variante  # noqa: E402

V = variante(os.environ.get("REPO_SLUG", slug_do_repo()))
BASE = os.environ.get("BASE_URL", "http://localhost:%d" % V["PORTA_API"])
PREFIXO = V["PREFIXO"]
RAZAO = V["RAZAO_PREFERENCIAL"]


def req(metodo, caminho, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + caminho, data=data, method=metodo)
    if data:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except ValueError:
            return e.code, {}
    except Exception as e:  # conexao recusada etc.
        raise AssertionError("falha ao chamar %s%s: %s — o app esta no ar? "
                             "(bash scripts/rodar_testes.sh sobe o container)"
                             % (BASE, caminho, e))


def test_01_emissao_de_senha():
    """POST /senhas emite senha com o PREFIXO da variante e valida tipo."""
    # emite PREFERENCIAL (nao normal) para nao interferir na fila de normais
    # que o test_02 rastreia pela intercalacao da variante
    status, corpo = req("POST", "/senhas", {"tipo": "preferencial"})
    assert status == 201, "esperado 201, veio %d (%s)" % (status, corpo)
    assert re.match(r"^%s\d{3}$" % PREFIXO, corpo.get("codigo", "")), \
        "codigo deve seguir %sNNN, veio %r" % (PREFIXO, corpo.get("codigo"))
    assert corpo.get("status") == "aguardando"

    status, corpo = req("POST", "/senhas", {"tipo": "vip"})
    assert status == 422, "tipo invalido deve dar 422, veio %d" % status
    assert corpo.get("erro") == "tipo_invalido"


def test_02_intercalacao_da_variante():
    """A prioridade chama RAZAO preferenciais antes de 1 normal (SUA razao)."""
    # emite 1 normal + RAZAO preferenciais (fresh, rastreando os codigos)
    _, normal = req("POST", "/senhas", {"tipo": "normal"})
    prefs = [req("POST", "/senhas", {"tipo": "preferencial"})[1]
             for _ in range(RAZAO)]

    chamadas = []
    for _ in range(RAZAO + 1):
        status, corpo = req("GET", "/senhas/proxima")
        assert status == 200, "esperado 200, veio %d (%s)" % (status, corpo)
        chamadas.append(corpo)

    tipos = [c.get("tipo") for c in chamadas]
    esperado = ["preferencial"] * RAZAO + ["normal"]
    assert tipos == esperado, "intercalacao deve ser %s, veio %s" % (esperado, tipos)
    assert chamadas[-1].get("codigo") == normal.get("codigo"), \
        "a normal chamada deve ser a que este teste emitiu"
    assert all(c.get("status") == "chamada" for c in chamadas)
    _ = prefs  # preferenciais consumidas acima; mantidas para legibilidade
