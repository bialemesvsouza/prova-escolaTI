# Track e lockfile (`track.json`) — como o sistema sabe o que disparar

> Documento de referência para **humanos e LLMs** que criam novas tracks,
> novos estilos de prova ou novos workflows. Leia inteiro antes de gerar ou
> alterar uma track.

## Ideia central

O repositório tem duas partes com vidas diferentes:

| Parte | Onde mora | Muda quando |
| --- | --- | --- |
| **Esqueleto** (workflows, scripts base, trampas, nota, docs) | raiz do template | raramente — evolução do sistema |
| **Track** (README, contrato, rubrica, testes, stubs) | `exams/<ano>/<track>/` | **a cada prova** — overlay vira a raiz do repo do aluno |

O **lockfile `track.json`** é a ponte: ele viaja com a track, pousa na raiz do
repo do aluno no momento da aplicação e **liga/desliga os jobs dos workflows**
do esqueleto. Assim o esqueleto pode ser completo (conter jobs para vários
estilos de prova) sem disparar o que não serve para a track atual.

## Semântica do lockfile

- **Ausente** = prova ainda não aplicada → **todos** os jobs de prova ficam
  `skipped` (o aluno pode dar push antes do dia D sem gerar ruído de CI).
- **Presente** = cada job só roda se sua chave em `workflows` for `true`.
- Chaves `workflows` desconhecidas são ignoradas (permitidas, para forward
  compatibility); chaves com tipo errado falham no `track_lock.py check`.
- O lockfile é **commitado pelo bot** no "commit de aplicação" — fora da
  janela de autoria do aluno e protegido por essa procedência (não comparecer
  no tamper-check contra o template).

## Schema (versão 1)

```json
{
  "track": "crud-fullstack",         // obrigatório, string — identidade da track
  "lockfile_version": 1,             // obrigatório, int — versão do schema
  "workflows": {                     // obrigatório, dict[str, bool]
    "auto-correcao.trampas": true,           // identidade, autoria, janela, integridade
    "auto-correcao.estrutura": true,         // entrega mínima (Containerfile, README)
    "auto-correcao.testes-publicos": true,   // suíte pública da track
    "auto-correcao.testes-escondidos": true, // suíte do repo de correção
    "auto-correcao.nota": true               // agregação da nota (base + extras)
  },
  "suites": {                        // opcional — metadados para o repo de correção
    "publicos":  { "path": "tests/public", "runner": "scripts/rodar_testes.sh" },
    "escondidos": { "via": "CORRECAO_REPO" }
  },
  "recursos": {                      // obrigatório, dict[str, bool] — declara capacidades da track
    "frontend": false,
    "docker": true,
    "variante": true
  }
}
```

### Chaves de workflow conhecidas (v1)

| Chave | Job | Desliga quando a track… |
| --- | --- | --- |
| `auto-correcao.trampas` | `trampas` | — (mantenha `true`; é o anti-cola e o gate da janela) |
| `auto-correcao.estrutura` | `estrutura` | não tiver Containerfile/README como entrega |
| `auto-correcao.testes-publicos` | `testes-publicos` | não tiver suíte pública (ex.: prova de debugging) |
| `auto-correcao.testes-escondidos` | `testes-escondidos` | não tiver suíte escondida |
| `auto-correcao.md` | `md` | não for de especificação (entregável em `.md`, critério E mecânico via `scripts/check_md.py`) |
| `auto-correcao.compila` | `compila` | não tiver camada de compilação (debugging; `scripts/check_build.py`, config `suites.compila`: `cmd`/`dir`/`pontos` — job inclui Java 17 + Maven) |
| `auto-correcao.sobe` | `sobe` | não tiver ambiente containerizado para subir (debugging; `scripts/check_sobe.py`, config `suites.sobe`: `compose_file`/`servicos_esperados`/`espera_s`/`pontos`) |
| `auto-correcao.smoke` | `smoke` | não tiver smoke de ponta a ponta (debugging; `scripts/smoke.py` cuida do ciclo compose, a track entrega as checagens em `smoke_track.py` na raiz — mesmo padrão do `tests_publicos.py`) |
| `auto-correcao.metodo` | `metodo` | não avaliar método de debug (commits hipótese→correção; `scripts/check_metodo.py`, config `suites.metodo`: `pontos`/`relatorio`) |
| `auto-correcao.nota` | `nota` | — (mantenha `true`; sem nota não há feedback) |

> Uma track de **especificação** (o aluno entrega só `.md`, sem app nem
> Containerfile) liga `md` e desliga `estrutura`/`testes-publicos`; o job `md`
> roda `scripts/check_md.py` com a config de `suites.md` do lockfile:
> `{"pontos": 15, "pts_por_arquivo": 3, "max_linhas_bloco": 20}` (bloco de
> código maior que o limite = fatal, nota 0 via job de nota).

> Uma track de **debugging** (app quebrada em containers, ciclo
> build→logs→corrigir) desliga `estrutura`/`testes-publicos`/`md` e liga os
> jobs próprios `compila`/`sobe`/`smoke`/`metodo` (tabela acima). O ambiente
> sobe com a variante injetada como variáveis de ambiente (`check_sobe.py` e
> `smoke.py` exportam todos os escalares de `variante/params.json` antes do
> `compose up`). A proporção fina por erro corrigido (dentro de cada camada)
> é refinada na correção docente — no CI cada camada é binária.

## CLI — `scripts/track_lock.py`

```bash
python scripts/track_lock.py get aplicada                                   # true/false
python scripts/track_lock.py get workflows.auto-correcao.testes-publicos    # true/false
python scripts/track_lock.py show     # imprime o lockfile resolvido
python scripts/track_lock.py check    # valida o schema (exit 1 se inválido)
```

O job `config` do workflow *Auto-correção* usa exatamente esses `get` para
preencher seus `outputs`; os demais jobs consomem via
`needs.config.outputs.<flag> == 'true'`.

> **Seleção de track (issueops):** as candidatas são o **dummy permanente**
> (`exams/dummy-exam/`, fora da hierarquia de ano — prova-teste) + as tracks
> do **ano mais recente** (`exams/<ano>/<track>/`). A escolha é **sempre
> explícita**: o aluno comenta `/track <nome-da-pasta>` na issue única "🎯 Prova"
> (ex.: `/track crud-fullstack`, `/track dummy-exam`) — o *Preparar entrega*
> valida o nome contra as candidatas (`scripts/selecao.py`), comenta o
> feedback na hora (modo sandbox para o dummy) e grava `.prova/track` em
> commit de bot. Detalhe de plataforma: **pushes feitos com `GITHUB_TOKEN` (o
> bot) não disparam workflows** (regra anti-recursão do GitHub) — por isso o
> **próprio comentário `/track` dispara o *Aplicar prova*** (issue_comment) e
> aplica na hora, sem esperar o commit do bot; o schedule (≤10 min) é o
> backstop e o `.prova/track` gravado cobre repos clonados na mão e re-runs.
> Antes de qualquer seleção o
> *Aplicar prova* é **no-op silencioso** (o gatilho push do repo não gera
> barulho na criação); com `.prova/track` inválido ele trava e comenta um
> lembrete na issue (uma única vez — upsert + sentinela `.prova/track-lembrete`).
> Anos anteriores ficam no histórico do repo (fora da `main`) e não entram na
> seleção.
>
> **Auto-correção sob demanda (v3.4):** a correção completa (trampas +
> entrega + testes públicos + nota) **não roda a cada push** — o aluno a
> solicita comentando `/auto-correcao` na issue (ou via workflow_dispatch).
> Fechar a issue exige ao menos 1 correção: o *Fechar prova* procura o
> marcador `<!-- nota-parcial -->` (upsert do nota.py) nos comentários e,
> se ausente, **reabre a issue com aviso** em vez de gerar o `teacher.json`.
> Comandos na issue: `/track <nome>`, `/aplicar`, `/auto-correcao` e
> `/ajuda`/`--help` (lista, atendido pelo *Preparar entrega*).

## Como criar uma NOVA track (checklist para LLM/humano)

1. **Crie a pasta** `exams/<ano>/<sua-track>/` espelhando a raiz do repo do
   aluno: `README.md` (visão da prova), `contrato.json`, `rubrica.json`,
   `tests_publicos.py` (se houver), stubs de entrega (`Containerfile`, `src/`…).
   O único arquivo que NÃO vai para o aluno é `AVISO-*.md` (o overlay pula).
2. **Escreva o `track.json`** obrigatório: `track`, `lockfile_version: 1`,
   `workflows` (ligue só o que a track usa), `recursos`. Valide com
   `python scripts/track_lock.py check` (simule o overlay: copie o
   `track.json` para a raiz de um clone de teste e rode o check lá).
3. **Contrato**: siga o schema de `contrato.json` (seção `variante` com as
   tabelas de parâmetros — a variante do aluno deriva do nome do repo;
   `endpoints` detalhados; bloco `frontend` se `recursos.frontend`).
   Tabelas de variante: as chaves núcleo (`PREFIXOS`, `RAZOES`, `PORTA_BASE`,
   `FAIXA`) cobrem tracks estilo API/juiz; tracks com outros parâmetros usam
   `variante.extras` — cada entrada é `{"opcoes": [...]}` (escolha por módulo)
   ou `{"base": N, "passo": M, "faixa": F}` (`base + (h % faixa) * passo`).
   Com `extras` presente, as chaves núcleo são opcionais; sem `extras`, elas
   são obrigatórias (validado pelo `validar_exams.py`).
4. **Rubrica**: `nota_max`, `extras_max` (0 se não houver extras),
   `janela_minutos` (enforcement e divulgação — `aplicar_prova.py` divulga o
   valor real na issue da prova), pesos dos critérios.
5. **Testes públicos**: autossuficientes (só stdlib), leem a variante com
   `from variante import slug_do_repo, variante`, e falham com mensagem que
   ajuda o aluno (sem revelar os casos escondidos).
6. **Teste o ciclo inteiro** com um repo de teste gerado do template:
   setup → issue → comentar "aplicar" → conferir overlay (track.json na raiz)
   → push de código → jobs que o lockfile ligou devem rodar, os demais
   `skipped` → nota no Summary.
7. **Nunca** edite `scripts/`, `.github/workflows/` do esqueleto dentro da
   pasta da track — eles não são da track.

## Estender o sistema (nova chave de workflow / novo job)

1. Adicione o job ao workflow do esqueleto com `if` condicionado a um novo
   output do job `config` (seguindo o padrão dos jobs existentes).
2. Registre a chave em `KNOWN_WORKFLOW_KEYS` em `scripts/track_lock.py` e
   neste documento.
3. As tracks antigas sem a chave continuam funcionando (default = `false`).

## Anti-padrões

- ❌ Hardcodar comportamento da track no esqueleto (o esqueleto é agnóstico).
- ❌ Commitar `track.json` na raiz do **template** (ele só existe pos-overlay).
- ❌ Esquecer `lockfile_version` — sem ele o `check` falha.
- ❌ Depender de recursos fora do repo do aluno (a suíte escondida mora no
  repo de correção, acessado só via `CORRECAO_TOKEN`).
