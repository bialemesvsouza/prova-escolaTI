# Prova 01 · Track 01 — Spec-Driven Development (Zona Azul Digital)

> No momento da aplicação, esta pasta virou o **seu repositório** (enunciado,
> contrato e rubrica estão na raiz). O esqueleto com os workflows de correção
> continua aqui, por trás.

Você **não escreve código**. Você escreve **especificações em Markdown** que,
na correção, são passadas por um modelo de IA fixo — **Kimi 2.8 (Preview
2026)**, **sem harness**: apenas o agente, com janela de **256k tokens**,
executando a tarefa proposta pelos seus `.md` (mesmo modelo e mesma
configuração para todos os alunos). A prova avalia sua capacidade de
**especificar**.

> [!NOTE]
> Os `.md` deste repositório usam *alerts* (`> [!NOTE]`, `> [!WARNING]`…),
> *footnotes*[^exemplo-footnote] e tabelas de propósito: markdown bem
> estruturado deixa a spec mais legível para o modelo que vai gerar o
> código.[^md-na-nota-e]

## O que vale nesta prova

| Critério | Pontos |
| --- | --- |
| A — Contrato REST (suíte de correção, UC1–UC4) | 30 |
| B — Casos de borda (suíte de correção, testes não revelados) | 25 |
| C — Requisitos além dos óbvios (suíte de correção, escondida) | 15 |
| D — SDLC do código gerado (Containerfile, manifesto de deps, README, testes próprios) | 15 |
| E — Qualidade mecânica dos `.md` (checklist público, verificado no CI) | 15 |
| **Total** | **100** |

> O feedback do CI cobre o **critério E** integralmente e valida o formato da
> entrega; **A–D são executados na correção do professor**: o código é gerado
> pelo **Kimi 2.8 (Preview 2026), sem harness** — só o agente em 256k tokens
> rodando sua especificação — e avaliado pela suíte escondida. A nota do CI é
> **parcial**.

## Suas ferramentas neste repo

- **Enunciado**: `ENUNCIADO.md` (contexto, contrato dos UC1–UC4, checklist do
  critério E) — leia **inteiro** antes de escrever
- **Contrato máquina-legível**: `contrato.json` (o mesmo contrato, para a
  correção)
- **Sua variante**: `variante/params.json` (gerada na aplicação; única do seu repo)
- **Nota parcial**: rode `/auto-correcao` na issue "🎯 Prova" — sai no Summary
  do workflow *Auto-correção* **e em comentário na issue**. Obrigatório ao
  menos 1x antes de fechar.
- **Regras e rastreabilidade**: `docs/REGRAS.md` e `FONTES.md`

## Parâmetros da sua variante

Cada repositório tem a sua — derivados do **nome do repo**.[^variante] O
comentário de aplicação na issue "🎯 Prova" lista os seus valores:

| Parâmetro | Significado |
| --- | --- |
| `TARIFA_HORA_CENTAVOS` | Valor da hora cheia, em centavos |
| `FRACAO_MINUTOS` | Granularidade mínima de cobrança (sempre arredondando **para cima**) |
| `TETO_DIARIO_CENTAVOS` | Valor máximo cobrado por bilhete |
| `TOLERANCIA_MINUTOS` | Minutos iniciais **grátis** (0, 10 ou 15) — passou, cobra desde o primeiro minuto |
| `PORTA_SERVICO` | Porta em que o serviço gerado deve escutar na correção |

## Regras

- **Janela**: 120 minutos (divulgada como 1h30), contados a partir do commit
  de aplicação ("chore: aplicar prova …", feito pelo bot). O relógio já está
  rodando — dê push antes do fim da janela.
- **Individual. Consulta é permitida — rastreabilidade obrigatória**: qualquer
  site ou IA usados vão para `FONTES.md` (URL/link público + onde aparece no
  entregável). Se não usou nada, declare isso explicitamente lá.
- **IA como agente é proibida** (IA que edita arquivos ou executa comandos no
  seu lugar → nota 0, plágio). IA como consulta, com a conversa pública e
  registrada em `FONTES.md`, é permitida.
- O entregável são **especificações em `.md`**. **Snippets de código de até
  20 linhas são aceitos** para elucidar o agente; passou de 20 linhas, é
  implementação — e implementação nos `.md` **zera a prova**, verificado
  automaticamente no CI.
- **Os testes escondidos podem cobrar todo o processo de gestão do SDLC da
  sua entrega** — organização, higiene de código, segredos no repo, linters
  genéricos da linguagem. Entregue como se fosse para produção.
- **Não altere** `scripts/`, `.github/` ou `docs/` (conferido contra o
  template) nem `track.json`/`contrato.json`/`rubrica.json`/`ENUNCIADO.md`
  depois da aplicação (conferido contra o commit de aplicação) — prova zerada.

> [!WARNING]
> O enunciado contém **um exemplo propositalmente inconsistente** com o
> contrato (`exemplo_inconsistente` no `contrato.json`). O contrato manda —
> não copie o exemplo.

> [!TIP]
> Nos seus `.md`, prefira tabelas para casos de teste, *alerts* para riscos e
> restrições, e *footnotes* para justificativas longas. O checklist do
> critério E é mecânico — markdown estruturado ajuda você a não esquecer
> itens.

## Agora

1. Leia `ENUNCIADO.md` **inteiro** (contexto + contrato + checklist do E).
2. Escreva seus `.md` de especificação (estrutura sugerida: `constitution.md`,
   `spec.md`, `plan.md`, `tasks.md`, `tests.md` — nomes e quantidade livres,
   pontuam os 5 melhores).
3. Faça **commits pequenos e frequentes** ao longo da prova — pushes **não**
   disparam correção.
4. Se usou qualquer consulta (site ou IA), preencha `FONTES.md` antes do push
   final.
5. Rode `/auto-correcao` na issue "🎯 Prova" e veja o critério E pontuado.
   **Obrigatório ao menos 1x.**
6. **Feche a issue "🎯 Prova"** — isso encerra a prova e gera o
   `teacher.json` de entrega. Fechar sem `/auto-correcao` reabre a issue com
   aviso. Boa prova! 🚀

[^exemplo-footnote]: É isso aqui: nota de rodapé. No GitHub, escreva `[^id]`
    no texto e defina `[^id]: texto` em qualquer lugar do arquivo.
[^md-na-nota-e]: O critério E pontua conteúdo (checklist mecânico), mas uma
    spec bem formatada é mais fácil de manter completa — e de ler.
[^variante]: A variante é derivada do nome do repositório por
    `scripts/variante.py`. Na correção ela é recalculada a partir do nome do
    seu repo, então o `params.json` de outro aluno não serve para você.
