#!/usr/bin/env python3
"""Variante do aluno — genérica, lê os parâmetros da pasta do ano.

A variante é DETERMINÍSTICA: derivada do nome do repositório + das tabelas da
seção `variante` do `contrato.json` da pasta do ano (`exams/<ano>/<track>/`).
A correção recompute os mesmos valores, então copiar arquivos de colega não
funciona.

Antes da prova ser aplicada não existe pasta do ano — variante() lança erro
nesse caso (setup da prova não depende de variante; só a aplicação e a
correção dependem).
"""
import glob
import hashlib
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def slug_do_repo() -> str:
    if os.environ.get("REPO_SLUG"):
        return os.environ["REPO_SLUG"]
    if len(sys.argv) > 1:
        return sys.argv[1]
    return os.path.basename(BASE)


def pasta_do_ano(base: str = BASE):
    """Localiza a pasta da prova aplicada (marcador .prova/exam-dir).

    Depois do overlay, o contrato vive na RAIZ do repo; o marcador guarda de
    onde veio (ex.: exams/dummy-exam). None se a prova nao foi aplicada.
    """
    marcador = os.path.join(base, ".prova", "exam-dir")
    if os.path.exists(marcador):
        pasta = open(marcador, encoding="utf-8").read().strip()
        if pasta:
            return pasta
    candidatas = sorted(
        set(m.group(1) for m in
            (re.match(r"(exams/\d{4}/[^/]+)/", os.path.relpath(p, base)) for p in
             glob.glob(os.path.join(base, "exams", "*", "*", "*")))
            if m))
    return candidatas[-1] if candidatas else None


def parametros_ano(pasta: str, base: str = BASE) -> dict:
    """Tabelas da variante: contrato.json da RAIZ (pos-overlay) ou da pasta."""
    for alvo in (os.path.join(base, "contrato.json"),
                 os.path.join(base, pasta, "contrato.json")):
        if os.path.exists(alvo):
            with open(alvo, encoding="utf-8") as f:
                return json.load(f)["variante"]
    raise SystemExit("contrato.json nao encontrado (raiz nem pasta %s)." % pasta)


def variante(slug: str, base: str = BASE) -> dict:
    pasta = pasta_do_ano(base)
    if not pasta:
        raise SystemExit("Prova ainda nao aplicada neste repositorio "
                         "(sem pasta do ano). Aguarde a publicacao ou rode "
                         "scripts/aplicar_prova.py.")
    p = parametros_ano(pasta, base)
    h = int(hashlib.sha256(slug.encode("utf-8")).hexdigest(), 16)
    v = {"slug": slug, "EXAM_DIR": pasta}
    # chaves nucleo (tracks estilo API/juiz) — computadas so se a tabela existir
    if "PREFIXOS" in p:
        v["PREFIXO"] = p["PREFIXOS"][h % len(p["PREFIXOS"])]
    if "RAZOES" in p:
        v["RAZAO_PREFERENCIAL"] = p["RAZOES"][h % len(p["RAZOES"])]
    if "PORTA_BASE" in p and "FAIXA" in p:
        v["PORTA_API"] = p["PORTA_BASE"] + (h % p["FAIXA"])
    # tabelas genericas da track (ex.: tarifa, teto, fracao): cada entrada e
    # {"opcoes": [...]} (escolha por modulo) ou {"base": N, "passo": M,
    # "faixa": F} (base + (h % faixa) * passo); "formato" opcional formata o
    # numero (ex.: "prova_%02d"). Deterministico como o nucleo.
    for nome, cfg in p.get("extras", {}).items():
        if "opcoes" in cfg:
            v[nome] = cfg["opcoes"][h % len(cfg["opcoes"])]
        else:
            numero = cfg["base"] + (h % cfg["faixa"]) * cfg.get("passo", 1)
            v[nome] = cfg["formato"] % numero if "formato" in cfg else numero
    return v


def main() -> None:
    slug = slug_do_repo()
    v = variante(slug)
    os.makedirs(os.path.join(BASE, "variante"), exist_ok=True)
    os.makedirs(os.path.join(BASE, ".prova"), exist_ok=True)
    with open(os.path.join(BASE, "variante", "params.json"), "w", encoding="utf-8") as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
    with open(os.path.join(BASE, ".prova", "id"), "w", encoding="utf-8") as f:
        f.write(slug + "\n")
    print("Variante deste repositorio (nome: %s, prova: %s):" % (slug, v["EXAM_DIR"]))
    for k, val in v.items():
        if k not in ("slug", "EXAM_DIR"):
            print("  %s = %s" % (k, val))
    print("\nArquivos gerados: variante/params.json e .prova/id — commite-os.")


if __name__ == "__main__":
    main()
