#!/usr/bin/env python3
"""Pontua os testes publicos a partir do resultado do pytest.

O workflow roda `rodar_testes.sh` e salva a saida em pytest.log antes de
chamar este script.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_path = os.environ.get("PYTEST_LOG", os.path.join(os.getcwd(), "pytest.log"))
log = open(log_path, encoding="utf-8", errors="replace").read() if os.path.exists(log_path) else ""


def peso_total():
    """Peso do criterio testes_publicos vem da rubrica da pasta do ano
    (pos-overlay fica na raiz). Fallback: 20."""
    for alvo in ("rubrica.json",):
        if os.path.exists(alvo):
            try:
                return int(json.load(open(alvo, encoding="utf-8"))
                           ["criterios"]["testes_publicos"])
            except Exception:
                pass
    return 20

m = re.search(r"(\d+)\s+passed", log)
m_falha = re.search(r"(\d+)\s+failed", log)
m_erro = re.search(r"(\d+)\s+error", log, re.I)
passaram = int(m.group(1)) if m else 0
falharam = int(m_falha.group(1)) if m_falha else 0
erros = int(m_erro.group(1)) if m_erro else 0

total = peso_total()
n_testes = passaram + falharam + erros
# half-up: nao trunca o resto contra o aluno
pontos = min(total, (total * passaram + n_testes // 2) // n_testes) if n_testes else 0
obs = ["pytest: %d passed, %d failed, %d error" % (passaram, falharam, erros)]
if passaram == 0 and falharam == 0 and erros == 0:
    obs.append("pytest nao produziu resumo — container nao subiu? Ver logs do job.")
    # se nem chegou a rodar testes, os 20 pts ficam 0 (suíte não executável)
pontos = 0 if (passaram == 0 and falharam == 0 and erros == 0) else pontos

resultado = {"job": "publicos", "criterio": "Testes públicos",
             "pontos": pontos, "max": peso_total(), "obs": obs}
with open(os.path.join(BASE, "result-publicos.json"), "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)
print(json.dumps(resultado, ensure_ascii=False, indent=2))
