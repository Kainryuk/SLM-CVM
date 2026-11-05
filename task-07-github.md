# Task 07 — GitHub: push do repositório

**Objetivo:** Subir o repositório com todos os artefatos da Sem01 (exigência do checklist UC01_Sem01).

**O que o repo deve conter (checklist §4 item 1):**
- `docker-compose.yml` ✅ (já criado)
- `db/init.sql` ✅ (já criado)
- `src/teste_extracao_slm.py` ✅ (já criado — Trilha B)
- `requirements.txt` ✅
- `data_lake/` (estrutura de pastas; `raw/` pode estar vazio ou com os 5 docs que o Yuri mapear — Trilha A)
- `tests/evidencia_extracao.json` ✅ (gerado pelo Task 04/05)
- `KELVIN_TASKS.md` + `task-*.md` ✅ (organização)

**Comandos:**

```bash
# na raiz do projeto
git init
git add .
git commit -m "Sem01 UC01: setup ambiente + Trilha B (IA/SLM) Kelvin-CVM"
git remote add origin <url-do-repo-cvm>
git push -u origin main
```

> **CVM é a agência da dupla (Kelvin + Yuri).** Se o repo já foi criado pelo Yuri (Trilha A), faça um **fork/branch** e abra o PR — não recrie. Confirme com ele qual repo usar.

**Checklist:**
- [ ] Repo no GitHub com os artefatos listados
- [ ] Commit inicial feito
- [ ] PR aberto (se repo compartilhado)

**Depende de:** Tasks 01–05 completas
