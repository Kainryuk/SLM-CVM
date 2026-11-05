# Task 05 — Evidência de execução (JSON)

**Objetivo:** A pasta `tests/` recebe o arquivo `evidencia_extracao.json` — é a prova exigida pelo checklist para a Trilha IA.

**Como:** o script `src/teste_extracao_slm.py` já salva a saída automaticamente em `tests/evidencia_extracao.json` (ver o bloco `[evidencia]` no final do `main()`).

**Formato esperado do JSON:**

```json
{
  "orgao": "CVM",
  "numero_norma": "88/2022",
  "assunto_principal": "Divulgação de informações por companhias abertas",
  "possui_prazo_ou_multa": true
}
```

**Checklist:**
- [ ] `tests/evidencia_extracao.json` existe
- [ ] Conteúdo é JSON válido (abra e confirme os 4 campos)
- [ ] Arquivo vai junto no repositório (Task 07)

**Referência:** doc Checklist ("Trilha IA: Saída em JSON gerada pelo script")
