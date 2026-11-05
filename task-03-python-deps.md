# Task 03 — Python: instalar dependências

**Objetivo:** Instala `ollama` (client Python) + `pydantic` no ambiente local.

**Comandos:**

```bash
# na raiz do projeto
pip install -r requirements.txt
```

> O repo já tem `requirements.txt` criado. O doc menciona `pip install ollama pydantic` — o requirements.txt formaliza isso.

**Confirmação:**

```bash
python -c "import ollama, pydantic; print('Instalação validada com sucesso!')"
```

**Checklist:**
- [ ] `ollama` importa sem erro
- [ ] `pydantic` importa sem erro

**Referência:** doc Opção 4B ("Instale a biblioteca do Ollama e Pydantic")
