# Implemente aqui sua solução conforme o `contrato.json` da raiz

- Servidor HTTP escutando em **0.0.0.0:8080** (dentro do container);
- `GET /healthz` → 200 `{"status": "ok"}` — a suíte espera por ele para começar;
- `GET /saudar` → saudação em texto puro, com os defaults e validações do contrato;
- **só stdlib** (`http.server`) já basta — esta prova-teste não precisa de pip;
- `python3 src/app.py` sobe o servidor localmente; o `Containerfile` da raiz já
  sabe rodá-lo no container.
