# UC01 Sem01 — Kelvin (Trilha B: IA & SLM) — CVM

> Documento-mãe: `UC01_Sem01_Setup_Ambiente_e_Mapeamento_Regulatorio.docx`
> Semana de referência: **Sem01** (Etapa 1 — 12h)
> Dupla: **Kelvin (CVM / Trilha B: IA & SLM)** + Yuri (CVM / Trilha A: Dados & Banco)
> Missão prática (12h): *"Subir servidor Ollama no Docker, estudar a estrutura das normas da CVM e criar o script Python + Pydantic que extrai metadados de um artigo da CVM."*

## O que é meu (Kelvin) — só a Trilha B
| Item | Fonte no doc |
|---|---|
| Subir Ollama no Docker | Passo 2 (services: ollama) + checklist |
| Ollama + Pydantic instalados | Opção 4B ("pip install ollama pydantic") |
| Script de extração de metadados | Opção 4B (`src/teste_extracao_slm.py`) |
| Evidência de execução (JSON) | Checklist ("Trilha IA: Saída em JSON gerada pelo script") |
| GitHub com docker-compose.yml + db/init.sql | Checklist (repositório) |

> **Não é meu** (é do Yuri / Trilha A): repositório CVM principal, `docs/mapeamento_fontes.md`, baixar os 5 documentos em `data_lake/raw/`, script `gerar_hash.py`. O ambiente aqui já contém os artefatos da Trilha A compartilhados porque a dupla usa a mesma base CVM.

## Tasks (só do Kelvin)

| # | Task | Arquivo | H |
|---|---|---|---|
| 1 | Docker: subir Ollama (serviço `ollama` do compose) | `task-01-ollama-docker.md` | 1 |
| 2 | Docker: pull do modelo `qwen2.5:3b` | `task-02-pull-modelo.md` | 1 |
| 3 | Python: instalar `ollama` + `pydantic` | `task-03-python-deps.md` | 0.5 |
| 4 | Criar/rodar `src/teste_extracao_slm.py` (extração Pydantic) | `task-04-script-extracao.md` | 3 |
| 5 | Evidência: salvar saída JSON em `tests/` | `task-05-evidencia-json.md` | 0.5 |
| 6 | Atualizar planilha S01 → Concluído + link do repositório | `task-06-planilha.md` | 0.5 |
| 7 | GitHub: push do repositório (compose + init.sql + script + evidência) | `task-07-github.md` | 0.5 |

Total direto: ~7h das 12h (restante = 2h de material de estudo + buffer de dublagem com o Yuri na Trilha A).

## Checklist de entrega (UC01_Sem01)
- [ ] Repositório GitHub com `docker-compose.yml`, `db/init.sql` e `src/teste_extracao_slm.py`
- [ ] Evidência: saída JSON do script de extração (Trilha IA)
- [ ] Planilha linha S01 → Status **Concluído** + link do repositório/PR
