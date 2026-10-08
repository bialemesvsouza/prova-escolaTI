# Regras comuns — Escola de TI (provas práticas)

> [!IMPORTANT]
> Estas regras valem para **todas** as provas aplicadas por este sistema. A
> fonte canônica da disciplina está no repositório
> [`endersonmenezes/talks`](https://github.com/endersonmenezes/talks)
> (`courses/escola-de-ti/evaluation/evaluation_04_practical_exam.md`) — este
> arquivo é a versão de bolso do aluno.

## Nota

- Prova vale **0–100** (`nota_max`), soma dos critérios publicados na pasta do
  ano (`rubrica.json`). Quando a rubrica define `extras_max`, a nota pode
  **ultrapassar 100** até o teto `nota_max + extras_max`.
- **A nota exibida no CI é parcial** — testes públicos + checagens (trampas e
  entrega). A nota definitiva inclui a **suíte escondida**, executada **fora
  do CI do aluno** (correção manual pelo professor ou Actions do repo privado
  `teacher-escola-ti` — o job de testes escondidos pula por design quando o
  repo de correção não está configurado; não é erro).
- Critérios objetivos: dúvida de correção se resolve **reexecutando o
  workflow**, não por negociação.

## Janela

- A janela começa no **commit de aplicação da prova** ("chore: aplicar prova …",
  feito pelo bot) e dura o que a pasta do ano definir (`janela_minutos`).
- O CI verifica commits do aluno fora da janela — suspeita vai para revisão.

## Consulta permitida — rastreabilidade obrigatória

- **Sites**: declare em `FONTES.md` como **linha numerada da tabela**
  (`| 1 | URL | o que usou | onde aparece |`). Links em texto corrido ou em
  exemplos **não contam** — só a linha numerada é verificada (mesma regra no
  CI e no `teacher.json`).
- **IA como consulta**: conversa **compartilhada e pública**, link registrado
  em `FONTES.md` indicando onde o conteúdo foi usado. O professor pode exigir o
  link a qualquer momento; você deve saber explicar qualquer trecho.
- **IA como agente** (edita arquivos, executa comandos no seu lugar) ou
  conteúdo sem declaração → **nota 0** (plágio).
- **Aviso de dissuasão**: o material da prova pode conter **canários para
  agentes de IA** (instruções ocultas em comentários, invisíveis para quem lê
  normalmente). Um artefato que contém a marca do canário evidencia que um
  agente escreveu no seu lugar **e** que você não revisou — vai para revisão
  manual. Quem resolve de verdade (lendo o contrato, não os comentários) não
  tem com o que se preocupar.

## Zeramento automático (o CI falha com "prova zerada")

- Alterar `scripts/`, `.github/` ou `docs/` (conferido contra o template
  remoto), ou alterar `track.json`/`contrato.json`/`rubrica.json` depois da
  aplicação (conferido contra o commit de aplicação — nem o lockfile nem o
  contrato são editáveis pelo aluno);
- Cópia de repositório de outro aluno (`.prova/id` não confere com o nome do
  repo);
- Violação de restrição específica da carreira (ex.: implementação completa em
  bloco de código nos `.md` da carreira de especificação).

## Suspeita → revisão manual (não zera sozinho)

- Commit único, múltiplos autores, commits fora da janela, `FONTES.md` com
  placeholder, aluno que não explica o próprio entregue.

## Documentação geral da disciplina

- Visão geral: [note_escola_de_ti](https://github.com/endersonmenezes/talks/blob/main/courses/escola-de-ti/note_escola_de_ti.md)
- Avaliação 04 (prova prática, 3 carreiras): [evaluation_04](https://github.com/endersonmenezes/talks/blob/main/courses/escola-de-ti/evaluation/evaluation_04_practical_exam.md)
- Provas anteriores: o histórico de exams (`exams/`) deste repositório — anos anteriores ficam disponíveis para consulta e evolução
