# ENUNCIADO — Prova 01 · Carreira 02 · Cadastro de Produtos

**Tempo: 1h30.** App de cadastro de produtos (backend Spring Boot + Maven,
frontend React, banco PostgreSQL, orquestração Docker Compose). **Está quebrada
de propósito.** Faça `docker compose up --build` subir backend + frontend de
ponta a ponta.

## Seus alvos (variante)

Rode `python scripts/variante.py`. Os valores abaixo **mudam de aluno para aluno** (exceto a origem,
fixa em `http://localhost:3000`) — a correção valida exatamente estes:

| Parâmetro | Alvo correto |
| --- | --- |
| `PORTA_PUBLICADA` | Porta no host em que o backend deve ficar acessível |
| `BANCO` | Nome do banco PostgreSQL (compose + backend devem concordar) |
| `ORIGEM_FRONTEND` | Origem permitida no CORS do backend |

## Contrato de "saudável" (o que a correção verifica)

1. `docker compose up --build` sobe `db`, `backend` e `frontend` sem sair;
2. `GET http://localhost:{PORTA_PUBLICADA}/produtos` → **200** JSON array
   (inicialmente vazio) **com header `Access-Control-Allow-Origin` compatível**
   com a origem do frontend;[^cors]
3. `POST http://localhost:{PORTA_PUBLICADA}/produtos` com
   `{"nome": "Teclado", "precoCentavos": 15000, "quantidade": 7}` → **201**;
4. `GET` seguinte lista o produto criado;
5. `http://localhost:3000` (frontend) abre e lista os produtos do backend.

> [!CAUTION]
> Este "exemplo de fluxo saudável" foi anotado por um monitor da turma anterior
> e **contradiz o contrato** acima — ele está aqui de propósito. Confie no
> contrato, não no exemplo.
>
> `POST /produto` retornando `{"ok": true}`

## Camadas com erros (quantidade por camada não é revelada)

- **Compilação** — `docker compose build` falha;
- **Configuração** — build ok, mas variáveis/portas/banco impedem a subida;
- **Startup/lógica** — sobe e cai, ou sobe com comportamento errado
  (diagnóstico via `docker compose logs`).

## Restrições

- Corrigir ≠ reescrever. Trocar a stack, remover funcionalidade ou "consertar"
  apagando endpoints vale **zero no critério A** (regressão).
- O `Containerfile` de cada serviço deve continuar funcionando — a correção
  reconstrói tudo do zero.
- Método conta: commits pequenos com mensagens no padrão
  `fix: <hipótese> → <correção>` (ou relatório equivalente no `README.md`
  do backend) pontuam no critério E.

[^cors]: O browser bloqueia chamadas entre origens diferentes
    ( Same-Origin Policy ) quando o servidor não responde o header
    `Access-Control-Allow-Origin` correspondente. Se o frontend "não lista
    nada" mas o backend responde no `curl`, o CORS é o primeiro suspeito.
