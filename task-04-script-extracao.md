# Task 04 — Rerodar o script de extração (Pydantic + Ollama)

**Objetivo:** Executar `src/teste_extracao_slm.py` e forçar o SLM a devolver um JSON estruturado que segue a `FichaNormativa`.

**Comandos:**

```bash
# Ollama no ar + modelo baixado (Tasks 01 e 02)
python src/teste_extracao_slm.py

# Ou trocando pelo trecho de uma norma real da CVM (salvo em .txt):
python src/teste_extracao_slm.py --texto-arquivo data_lake/raw/exemplo_cvm.txt
```

**O que o script faz:**
1. Define a ficha rígida (JSON Schema) em `FichaNormativa`
2. Manda o trecho normativo para `qwen2.5:3b` via Ollama
3. Valida a resposta com Pydantic
4. Salva a saída em `tests/evidencia_extracao.json`

**Substitua o `TEXT_PADRAO`** no script por um trecho **real** da CVM (Resolução / Ofício do portal: `conteudo.cvm.gov.br/legislacao`). O exemplo já está trocado por CVM — confira se o assunto é coerente.

**Checklist:**
- [ ] Script roda sem erro
- [ ] JSON imprimido tem os 4 campos: `orgao`, `numero_norma`, `assunto_principal`, `possui_prazo_ou_multa`
- [ ] `tests/evidencia_extracao.json` gerado

**Referência:** doc Opção 4B + Checklist ("Saída em JSON gerada pelo script")
