# ℹ️ AVISO — pasta DUMMY (prova-teste permanente)

> [!NOTE]
> `exams/dummy-exam/` **não é uma prova real** — é a **prova-teste permanente
> do sistema**: um hello world em Python para validar o sistema e treinar o
> ciclo de entrega (fetch do template → `/track` na issue única → overlay na
> raiz → commit do bot → auto-correção → nota no Summary e na issue → aluno
> fecha a issue → `teacher.json`).
>
> **Ela fica publicada na `main` para sempre**, de propósito:
>
> 1. **Mora fora da hierarquia de ano** — não é `exams/<ano>/<track>/`, então
>    o ano mais recente nunca a "engole"; ela é candidata de seleção em
>    qualquer ano.
> 2. **Nunca aplicada sozinha** — a seleção é **sempre explícita**:
>    `/track dummy-exam` na issue única "🎯 Prova" é a escolha de teste do
>    aluno/professor; a aplicação acontece automaticamente em seguida (o push
>    do bot da seleção dispara o aplicar). Sem seleção o aplicar é no-op
>    silencioso; nome inválido gera lembrete na issue (uma única vez) — o
>    dummy não pode ser aplicado por engano no dia de uma prova real.
> 4. **Anos antigos acumulam no histórico** — pastas `exams/<ano>/` de anos
>    anteriores ficam no histórico do repo para consulta; fora da `main`, não
>    entram na seleção (só o ano mais recente + o dummy são candidatos).
>
> Não delete esta pasta. Se ela sumir da `main`, o template perde a prova-teste
> para todas as turmas seguintes.

## Layout de uma pasta de prova (`exams/<ano>/<track>/`)

A pasta **é o repositório do aluno**: cada item do topo vira um arquivo/pasta
na raiz do repo dele no momento da aplicação (o dummy segue exatamente este
mesmo layout):

| Item | Vira no repo do aluno |
| --- | --- |
| `README.md` | README raiz (a visão da prova) |
| `contrato.json` | contrato raiz (endpoints, regras, variante) |
| `rubrica.json` | rubrica raiz (pesos, extras, janela) |
| `track.json` | **lockfile raiz** — liga/desliga os workflows (ver `docs/TRACKS.md`; `recursos` é obrigatório) |
| `tests_publicos.py` | `tests/public/test_publicos.py` |
| `Containerfile`, `src/` | stubs de entrega na raiz |

O que **não** está na pasta (workflows, scripts base, trampas, nota) é o
esqueleto ano-agnóstico — protegido pelo tamper-check e mantido no template.
