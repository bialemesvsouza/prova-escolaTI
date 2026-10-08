"""TODO (aluno): implemente aqui o servidor da prova-teste — Hello World.

Contrato (contrato.json na raiz):

- GET /healthz              -> 200 {"status": "ok"}
- GET /saudar?nome=...      -> 200 text/plain, uma linha "{saudacao}, {nome}{sufixo}"
                               por repetição (saudacao default "Ola", sufixo
                               default "!", repeticoes default 1, inteiro 1..10)
- parametros invalidos      -> 400 {"erro": "nome_ausente" | "repeticoes_invalidas"}

Dica: dá para fazer só com a stdlib (http.server) — sem pip, sem requirements.
O servidor deve escutar em 0.0.0.0:8080 (env PORT sobrescreve, só para local).
"""
