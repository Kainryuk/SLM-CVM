# Task 01 — Subir Ollama no Docker

**Objetivo:** Sobe o servidor Ollama via docker-compose (necessário para a Trilha B: IA & SLM).

**Por quê:** O SLM (`qwen2.5:3b`) roda localmente dentro do container — sem ele o script de extração não tem backend.

**Comandos (na raiz do projeto):**

```bash
# 1. Subir todos os containers (Postgres + Ollama)
docker compose up -d

# 2. Confirmar que o Ollama subiu
docker ps | grep ollama

# 3. O Ollama já está acessível em http://127.0.0.1:11434 (porta exposta no compose)
```

**Checklist:**
- [ ] `docker compose up -d` roda sem erro
- [ ] Container `ollama` aparece em `docker ps`
- [ ] Porta 11434 respondendo

**Tempo estimado:** ~30 min (a primeira subida baixa imagens)

**Referência:** Docker Compose Quickstart (doc §5 Material de Estudo)
