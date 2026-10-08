# Prova teste — Hello World (Python, só stdlib).
# A suíte faz: docker build -t prova . && docker run -p <PORTA>:8080 prova
# Requisitos do contrato (contrato.json -> servidor):
#   - a API escuta na porta 8080 DENTRO do container (env PORT sobrescreve,
#     só para testes locais);
#   - nenhuma variável de ambiente obrigatória;
#   - GET /healthz deve responder 200 {"status": "ok"} (a suíte espera por ele).
FROM python:3.12-slim

WORKDIR /app
COPY src/ ./src/
EXPOSE 8080
CMD ["python3", "src/app.py"]
