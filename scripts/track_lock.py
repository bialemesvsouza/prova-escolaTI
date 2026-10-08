#!/usr/bin/env python3
"""Lockfile da track — liga/desliga workflows e recursos da prova.

Pos-overlay, o `track.json` fica na RAIZ do repo (veio de
`exams/<ano>/<track>/`). SEM lockfile = prova ainda nao aplicada: todos os
workflows de prova ficam DESLIGADOS. Com lockfile, cada job do workflow
*Auto-correcao* so roda se sua chave em `workflows` for true.

Uso:
    python scripts/track_lock.py get aplicada
    python scripts/track_lock.py get workflows.auto-correcao.testes-publicos
    python scripts/track_lock.py show          # resumo humano
    python scripts/track_lock.py check         # valida o schema (exit 1 se invalido)

Ver docs/TRACKS.md para o schema completo e para criar novas tracks.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED = {
    "track": str,
    "lockfile_version": int,
    "workflows": dict,
    "recursos": dict,
}
KNOWN_WORKFLOW_KEYS = {
    "workflows.auto-correcao.trampas",
    "workflows.auto-correcao.estrutura",
    "workflows.auto-correcao.testes-publicos",
    "workflows.auto-correcao.testes-escondidos",
    "workflows.auto-correcao.md",
    "workflows.auto-correcao.compila",
    "workflows.auto-correcao.sobe",
    "workflows.auto-correcao.smoke",
    "workflows.auto-correcao.metodo",
    "workflows.auto-correcao.nota",
}


def lockfile_path(base: str = BASE):
    """track.json da raiz (pos-overlay) ou da pasta da prova (se ainda nao overlayed)."""
    raiz = os.path.join(base, "track.json")
    if os.path.exists(raiz):
        return raiz
    marcador = os.path.join(base, ".prova", "exam-dir")
    if os.path.exists(marcador):
        pasta = open(marcador, encoding="utf-8").read().strip()
        candidato = os.path.join(base, pasta, "track.json")
        if os.path.exists(candidato):
            return candidato
    return None


def load(base: str = BASE) -> dict:
    caminho = lockfile_path(base)
    if not caminho:
        return {}
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def get(chave: str, base: str = BASE):
    """Valor de uma chave pontilhada. Aceita aninhado OU chave flat com
    pontos ("workflows.auto-correcao.testes-publicos"). 'aplicada' = lockfile
    existe. Default = False para qualquer chave ausente."""
    if chave == "aplicada":
        return lockfile_path(base) is not None
    dados = load(base)
    if not dados:
        return False
    partes = chave.split(".")
    atual = dados
    for i, parte in enumerate(partes):
        if isinstance(atual, dict) and parte in atual:
            atual = atual[parte]
        elif isinstance(atual, dict) and ".".join(partes[i:]) in atual:
            atual = atual[".".join(partes[i:])]
            break
        else:
            return False
    return atual


def check(base: str = BASE):
    """Valida o schema. Retorna lista de erros (vazia = ok)."""
    caminho = lockfile_path(base)
    if not caminho:
        return ["track.json ausente — prova nao aplicada (isso NAO e erro pos-setup)"]
    try:
        dados = json.load(open(caminho, encoding="utf-8"))
    except ValueError as e:
        return ["track.json invalido: %s" % e]
    erros = []
    for chave, tipo in REQUIRED.items():
        if chave not in dados:
            erros.append("campo obrigatorio ausente: %s" % chave)
        elif not isinstance(dados[chave], tipo):
            erros.append("campo %s deve ser %s" % (chave, tipo.__name__))
    for chave, valor in dados.get("workflows", {}).items():
        if not isinstance(valor, bool):
            erros.append("workflows.%s deve ser true/false" % chave)
    return erros


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    comando, resto = args[0], args[1:]
    if comando == "get" and resto:
        print(str(get(resto[0])).lower())
    elif comando == "show":
        caminho = lockfile_path()
        print("lockfile:", caminho or "(ausente — prova nao aplicada)")
        dados = load()
        if dados:
            print(json.dumps(dados, ensure_ascii=False, indent=2))
    elif comando == "check":
        erros = check()
        falhas = [e for e in erros if "prova nao aplicada" not in e]
        for e in erros:
            print(("INFO" if "prova nao aplicada" in e else "ERRO") + ": " + e)
        sys.exit(1 if falhas else 0)
    else:
        print("comando desconhecido: %s" % comando)
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
