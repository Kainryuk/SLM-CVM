# Task 02 — Baixar o modelo qwen2.5:3b

**Objetivo:** Puxa o SLM leve dentro do container Ollama.

**Comando (Ollama já no ar):**

```bash
docker exec -it ollama ollama pull qwen2.5:3b
```

> O download é de alguns GB — depende da sua rede. Pode demorar.

**Confirmação:**

```bash
docker exec -it ollama ollama list
# deve listar: qwen2.5:3b
```

**Checklist:**
- [ ] `ollama pull` termina sem erro
- [ ] `ollama list` mostra `qwen2.5:3b`

**Referência:** doc Passo 2 ("Baixe o modelo de IA leve")
