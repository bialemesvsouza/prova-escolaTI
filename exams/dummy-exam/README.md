# Prova teste — Hello World

> Esta é a **sua prova-teste**: no momento da aplicação, esta pasta virou o
> seu repositório (contrato, rubrica e testes públicos estão na raiz). O
> esqueleto com os workflows de correção continua aqui, por trás. O objetivo
> é treinar o ciclo de entrega com o exercício mais simples possível: **um
> hello world em Python**.

Você implementa um servidor minúsculo (só stdlib, sem pip) que saúda quem
chama; a **suíte de testes define o contrato** (`contrato.json`) e confere a
saudação com os parâmetros **da sua variante** — derivados do nome do seu
repositório, então copiar de colega não funciona.

## O que vale nesta prova-teste

| Critério | Pontos |
| --- | --- |
| Testes públicos (5, em `tests/public/` — saudação da variante, defaults, validação, `src/`, `FONTES.md`) | 70 |
| Containerfile funcional (suíte sobe sem ajustes — `EXPOSE 8080` + comando de execução) | 20 |
| README com instruções de subida (local e container) | 10 |
| **Total** | **100** |

> Sem pontos extras e sem suíte escondida nesta prova-teste — a nota do CI já
> é a nota desta prova-teste. Nas provas reais, a nota do CI é **parcial**: a
> suíte escondida não roda no CI do aluno e a nota definitiva é apurada pelo
> professor fora dele — correção manual ou via Actions do repo privado do
> professor, com a data de criação dos testes verificável pelos alunos.

## Suas ferramentas neste repo

- **Contrato**: `contrato.json` (endpoints, regras da saudação, variante)
- **Sua variante**: `variante/params.json` (gerada na aplicação; única do seu repo)
- **Testes públicos**: `bash scripts/rodar_testes.sh` (requer Docker)
- **Nota**: rode `/auto-correcao` na issue "🎯 Prova" — a nota sai no
  Summary do workflow *Auto-correção* **e em comentário na issue** (atualizado
  no mesmo comentário). Obrigatório ao menos 1x antes de fechar.
- **Regras e rastreabilidade**: `docs/REGRAS.md` e `FONTES.md`

## Parâmetros da sua variante

Cada repositório tem a sua — derivados do **nome do repo**, então copiar de
colega não funciona. O comentário de aplicação na issue "🎯 Prova" lista os
seus valores; no `variante/params.json` eles aparecem assim:

| Parâmetro | O que a suíte faz com ele |
| --- | --- |
| `PREFIXO` | O **nome** que a suíte envia em `/saudar?nome=...` — sua saudação tem que sair com ele |
| `RAZAO_PREFERENCIAL` | O valor de `repeticoes` no teste da sua variante — quantas linhas a suíte espera |
| `PORTA_API` | A porta em que a suíte sobe **o seu container** (`docker run -p PORTA_API:8080`) |
| `EXAM_DIR` | A pasta da prova que foi aplicada no seu repo |

## Como este repo está organizado

| Caminho | Papel |
| --- | --- |
| `src/` | **Sua solução** — é aqui que você implementa |
| `Containerfile` | Como a suíte sobe o seu código em container |
| `tests/public/` | O que o CI roda a cada push (veio da pasta da prova) |
| `contrato.json` / `rubrica.json` | O contrato da prova e como ela vale |
| `variante/` | Os seus parâmetros |
| `FONTES.md` | Sua declaração de consultas (rastreabilidade) |
| `ALUNO.md` | Sua identidade (nome/RA) |
| `scripts/`, `.github/`, `docs/` | **Esqueleto do sistema — NÃO altere** (tamper-check zera a prova) |
| `teacher.json` | Gerado automaticamente quando você fecha a issue (entrega) |

## Regras da prova-teste

- **Janela**: 120 minutos (1h30), contados a partir do commit de aplicação
  ("chore: aplicar prova …", feito pelo bot). O relógio já está rodando —
  dê push antes do fim da janela.
- **Consulta é permitida — rastreabilidade obrigatória**: qualquer site ou IA
  usados vão para `FONTES.md` (URL/link + onde aparece no entregável). Se não
  usou nada, declare isso explicitamente lá.
- **IA como agente é proibida** (IA que edita arquivos ou executa comandos no
  seu lugar → nota 0, plágio). IA como consulta, com a conversa pública e
  registrada em `FONTES.md`, é permitida.
- **Não altere** `scripts/`, `.github/` ou `docs/` (conferido contra o
  template) nem `track.json`/`contrato.json`/`rubrica.json` depois da
  aplicação (conferido contra o commit de aplicação) — prova zerada.
- **Vermelho no job de testes NÃO é quebra do sistema** — é o feedback
  normal da correção: a nota sai mesmo assim (comentário na issue + Summary),
  junto com o que falhou. Corrija e rode `/auto-correcao` de novo.

## Como esta prova-teste chegou aqui

Esta pasta foi aplicada por overlay depois que **você selecionou a track**:
na issue única "🎯 Prova" o comentário foi `/track dummy-exam` — o sistema
validou, respondeu na hora (modo sandbox 🏖️) e aplicou esta pasta
automaticamente (o commit do bot que gravou sua seleção disparou a aplicação).
Nas provas reais o passo é o mesmo: `/track <nome-da-pasta>` na issue (a
seleção é **sempre obrigatória** — nada de aplicação automática sem escolha).

## Agora

1. Leia `contrato.json` **inteiro** antes de codar (são dois endpoints).
2. Implemente em `src/app.py` (apague o `TODO`) + confira o `Containerfile`.
3. Rode `bash scripts/rodar_testes.sh` localmente (requer Docker) e veja os
   5 testes passarem.
4. Commits pequenos, push antes do fim da janela — pushes **não** disparam
   correção.
5. Rode `/auto-correcao` na issue "🎯 Prova" e veja a nota (Summary +
   comentário na issue). **Obrigatório ao menos 1x.**
6. **Feche a issue "🎯 Prova"** — isso encerra a prova e gera o
   `teacher.json` de entrega. Fechar sem `/auto-correcao` reabre a issue com
   aviso. Boa prova! 🚀
