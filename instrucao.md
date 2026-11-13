# INSTRUÇÃO — SLM-CVM (Trilha B: IA & SLM — Kelvin)

Runbook para rodar o pipeline de **organização + compreensão de assunto** das resoluções CVM
com SLM local (Ollama). Leia de cima para baixo.

---

## 0. O que este projeto faz (resumo em 1 linha)

> Limpa as 253 resoluções CVM de `docs/resolucoes/` e faz um SLM local **entender
> apenas o assunto** de cada uma — em português, sem código, sem história.

Pipeline em 2 estágios:

```
docs/resolucoes/**/*.md        (bruto: fonte, mirror, PDFs, rodapé, assinatura)
        │  [ESTÁGIO 1]  src/organizar_resolucoes.py
        ▼
data_lake/processed/           (texto normativo puro + índice de assuntos)
        │  [ESTÁGIO 2]  src/compreender_resolucoes.py   (Ollama + Pydantic)
        ▼
tests/compreensao_resolucoes.json   (253 fichas: norma, assunto, se_aplica_a, prazo/multa)
```

---

## 1. Pré-requisitos

| Item | Como checar |
|---|---|
| Python 3.10+ (aqui: 3.11) | `python --version` |
| Ollama no ar (porta 11434) | `curl http://127.0.0.1:11434/api/version` → `{"version":"..."}` |
| Modelo SLM instalado | `ollama list` → `qwen2.5-coder:7b` |
| Ollama client + Pydantic | `.venv` com `ollama` e `pydantic` (etapa 2 abaixo) |

> O Ollama pode ser **nativo** (app na bandeja do Windows — é o caso deste ambiente)
> ou **Docker** (`docker-compose.yml`). Os comandos dos scripts funcionam nos dois;
> só muda a porta/hostname em `OLLAMA_HOST` (padrão `http://127.0.0.1:11434`).

---

## 2. Preparar o ambiente Python (uma vez só)

Na raiz do projeto:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows
# source .venv/bin/activate         # Linux/macOS
pip install -r requirements.txt
```

Verificação:

```bash
.venv\Scripts\python -c "import ollama, pydantic; print('ok')"
```

---

## 3. Subir o Ollama (se não estiver)

**Nativo (Windows):** abrir o app Ollama (bandeja) — ou `ollama serve` num terminal.
Confirme que a porta responde:

```bash
curl http://127.0.0.1:11434/api/version
```

**Docker (alternativa):**

```bash
docker compose up -d
docker exec -it ollama ollama pull qwen2.5:3b
```

> Se quiser usar o `qwen2.5:3b` (plano B), puxe-o e chame o script com `--modelo qwen2.5:3b`.
> O padrão aqui é `qwen2.5-coder:7b` (já instalado).

---

## 4. ESTÁGIO 1 — Organizar o acervo

Gera os dados limpos que o modelo vai ler.

```bash
.venv\Scripts\python src\organizar_resolucoes.py
```

**O que ele faz:**
- Lê cada `docs/resolucoes/**/resol*.md` (ignora `_indice.md` e `anexos/`).
- Corta o ruído: linhas `Fonte / Espelhado em / Status`, seção `Documentos/Anexos`
  (só apontava PDF/DOC), marcações `<sub>Fonte</sub>`, rodapé de espelho, bloco de assinatura.
- Guarda **cabeçalho de metadados + texto normativo puro** em `data_lake/processed/<subpasta>/`.
  - Subpasta = nome da pasta de origem do acervo (único, evita colisão de normas
    multi-tag com mesmo número, ex. `resol202` em `Companhia/` e `Ritos_CVM/`).
- Emite `data_lake/processed/_indice_assuntos.json` (índice p/ RAG).

**Confirmação (253/253, sem ruído):**

```bash
# contagem de arquivos organizados
ls data_lake/processed/*/resol*.md 2>/dev/null | wc -l     # esperado: 253

# nenhum arquivo deve ter ficado com cruft
grep -rl "Espelho textual" data_lake/processed | wc -l      # esperado: 0
grep -rl "Assinado eletronicamente" data_lake/processed | wc -l  # esperado: 0
```

Abra `data_lake/processed/_indice_assuntos.json` e confira que cada entrada tem:
`orgao, norma, data, tag, assunto, arquivo_limpo`.

> ⚠️ Rode de novo **só** se o `docs/resolucoes/` atualizou. Ele reescreve tudo.

---

## 5. ESTÁGIO 2 — Compreender o assunto (o SLM)

Força o modelo a responder **apenas o assunto**, em português, sem código, sem história,
restrito a CVM/resoluções.

```bash
# Amostra (rápido, ~5 normas) — faça isso primeiro pra conferir a qualidade:
.venv\Scripts\python src\compreender_resolucoes.py --limite 5

# Se ok, rode o acervo inteiro (253 normas, ~19 min com o 7b):
.venv\Scripts\python src\compreender_resolucoes.py

# Ou restrinja a uma categoria:
.venv\Scripts\python src\compreender_resolucoes.py --limitar "Companhia"
```

**Schemas / trava do modelo (no `compreender_resolucoes.py`):**
- System-prompt: PT-BR · só objeto da norma · **sem código** · **sem história** · só CVM.
- Saída forçada ao schema `CompreensaoAssunto`:
  `norma`, `assunto`, `se_aplica_a`, `tem_prazo_ou_multa`.

**Confirmação:** o JSON em `tests/compreensao_resolucoes.json`:

```bash
.venv\Scripts\python -c "
import json
d=json.load(open('tests/compreensao_resolucoes.json',encoding='utf-8'))
print('processados:',d['processados'],'| erros:',d['erros'],'| modelo:',d['modelo'])
for r in d['resultados'][:3]:
    print('-',r['norma'],'->',r['assunto'][:60])
"
```

**Inspeção manual de 1 norma** (ver se está limpo e em PT-BR):

```bash
.venv\Scripts\python -c "
import json
d=json.load(open('tests/compreensao_resolucoes.json',encoding='utf-8'))
r=d['resultados'][0]
print(json.dumps(r,ensure_ascii=False,indent=2))
"
```

Critérios de "passou":
- [ ] texto em português
- [ ] descreve **o assunto/objeto**, não a história
- [ ] **não** contém código
- [ ] **não** cita ANS/ANVISA/Conselho (só CVM)

---

## 6. (Opcional) Extração de metadados — script original

A ficha normativa rígida `FichaNormativa` sobre **um trecho** (a base da Trilha B):

```bash
# trecho padrão embutido
.venv\Scripts\python src\teste_extracao_slm.py

# ou um arquivo real do acervo
.venv\Scripts\python src\teste_extracao_slm.py --texto-arquivo docs/resolucoes/Atos\ expedidos\ pela\ CVM/resol001.md
# -> tests/evidencia_extracao.json
```

---

## 7. Trava de domínio CVM — modelo `cvm-resolucoes` (funciona em qualquer executor/IDE)

Modelo-alias registrado **com a trava já embutida no próprio modelo** (não no "primeiro
prompt"). Qualquer executor, IDE ou chamada nua (`/v1/chat/completions`, `/api/chat`,
`ollama run`) já nasce restrito ao assunto CVM — **sem precisar passar system prompt**:

- assunto CVM (resoluções/atos normativos do mercado de valores mobiliários)
  → responde em pt-BR, só o assunto, **sem código, sem história**.
- qualquer outro assunto → devolve exatamente:
  **`Não consta na base de conhecimento da CVM.`**

### Criar (uma vez por atualização do prompt)

```bash
.venv\Scripts\python src\criar_modelo_trava.py
# -> /api/create a partir de qwen2.5-coder:7b + system prompt de domínio CVM
```

### Testar a trava SEM passar system prompt

```bash
.venv\Scripts\python src\testar_trava_cvm.py
# roda 3 perguntas CVM + 4 fora do tema; fora deve devolver a trava exata
```

### Usar em qualquer executor/IDE (OpenAI-compatible — a rota que os plugins usam)

```
base_url : http://127.0.0.1:11434/v1
model    : cvm-resolucoes
```

```bash
curl -s -X POST http://127.0.0.1:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"cvm-resolucoes","messages":[{"role":"user","content":"O que regula a Resolução CVM nº 88?"}]}'
```

Outras formas equivalentes:

```bash
ollama run cvm-resolucoes                      # interativo (CLI)
curl -s -X POST http://127.0.0.1:11434/api/chat \
  -d '{"model":"cvm-resolucoes","messages":[{"role":"user","content":"..."}],"stream":false}'
```

> Em IDEs (ex.: plugins que aceitam um endpoint OpenAI): aponte a base URL para
> `http://127.0.0.1:11434/v1` e deixe `model = cvm-resolucoes`. A trava já nasce no
> modelo — não é preciso colar o system prompt no workspace da IDE.
> Atualizou o prompt? Re-crie o alias: `python src/criar_modelo_trava.py`.

---

## 8. Usar em outros apps / IDEs (harness OpenAI-compatible)

A trava vive **no modelo** (não no prompt). Qualquer app que aceite um endpoint
OpenAI-compatible funciona: aponta a base URL local e nomeia o modelo. A trava
dispara sozinha — o app **não** precisa passar system prompt.

**Receita única (serve pra todos):**

```
base_url : http://127.0.0.1:11434/v1
model    : cvm-resolucoes
api_key  : (qualquer string — Ollama local não valida; ex.: "ollama")
```

> O Ollama precisa estar no ar (`curl http://127.0.0.1:11434/api/version`).
> Se o app for remoto/outro máquina, use o IP da máquina: `http://<ip>:11434/v1`
> e exporte `OLLAMA_HOST` / `OLLAMA_ORIGINS=*` pra liberar.

### 8.1. Hermes Desktop

> ⚠️ **O Hermes Agent exige janela de contexto ≥ 64K.** O `cvm-resolucoes` na base
> padrão (`qwen2.5-coder:7b`, janela 32K) é **rejeitado no init** ("below the minimum
> 64,000 required by Hermes Agent"). Pra usá-lo no Hermes, recrie o alias na base 30b:
>
> ```bash
> .venv\Scripts\python src\criar_modelo_trava.py --base qwen3-coder:30b
> ```
>
> (só volte pro 7b quando for usar em harness que não exija 64K — ver 8.2+).
>
> Se a máquina aguentar o 30b, registre no `~/.hermes/config.yaml`:

```yaml
providers:
  cvm:
    api_mode: chat_completions
    base_url: http://127.0.0.1:11434/v1
    discover_models: false
    model: cvm-resolucoes
    models:
      cvm-resolucoes: {}
    name: CVM Resolucoes (Ollama local - trava de dominio)
model_aliases:
  cvm:
    model: cvm-resolucoes
    provider: cvm
```

Trocar de modelo na conversa: `/model cvm`. Ele responde só CVM (pt-BR, sem código,
sem história); fora do tema devolve `Não consta na base de conhecimento da CVM.`
Reverter: `/model agnes` (o padrão).

### 8.2. OpenCode / OpenHands / Roo / Aider (config de provider)

Qualquer app com seção de "custom provider" (OpenAI-compatible):

```jsonc
// opencode — .opencode/opencode.json (ou config da ferramenta)
{
  "provider": {
    "cvm": {
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "http://127.0.0.1:11434/v1",
        "apiKey": "ollama"
      },
      "models": { "cvm-resolucoes": { "name": "CVM Resolucoes" } }
    }
  }
}
```

Aider (`.aider.conf.yml`):

```yaml
model: ollama/cvm-resolucoes
base_url: http://127.0.0.1:11434
```

### 8.3. Cursor / Cline / Continue (UI de provider)

- Cursor → *Settings → Models → Add Provider → OpenAI-compatible* → `Base URL
  http://127.0.0.1:11434/v1`, model id `cvm-resolucoes`.
- Cline (VS Code) → *Settings → API Provider: OpenAI Compatible*, mesma base URL.
- Continue → `.continue/config.yaml`:

```yaml
models:
  - name: CVM Resolucoes
    provider: openai
    model: cvm-resolucoes
    apiBase: http://127.0.0.1:11434/v1
```

### 8.4. Python (cliente OpenAI SDK)

```python
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")
r = client.chat.completions.create(
    model="cvm-resolucoes",
    messages=[{"role": "user", "content": "O que regula a Resolução CVM nº 88?"}],
)
print(r.choices[0].message.content)   # pt-BR · sem código · fora do tema → trava
```

### 8.5. curl / qualquer REST (nativo Ollama)

```bash
curl -s http://127.0.0.1:11434/api/chat \
  -d '{"model":"cvm-resolucoes","messages":[{"role":"user","content":"..."}],"stream":false}'
```

> **Por que funciona em todos sem system prompt:** a trava foi queimada em
> `cvm-resolucoes` na criação (`src/criar_modelo_trava.py`). O modelo já "acorda"
> restrito ao domínio — o app só escolhe o nome `cvm-resolucoes` e herda o
> comportamento. Atualizou o prompt de domínio? Recrie: `python src/criar_modelo_trava.py`.

---

## 9. Avaliação quantitativa (bateria automática, sem RAG)

`src/avalia_bateria_cvm.py` varre N números do acervo (padrão 30), pergunta
"O que disciplina a Resolução CVM nº N?" ao `cvm-resolucoes` **sem system prompt**
e classifica cada resposta comparando o significado com a ementa autoritativa
(`data_lake/processed/_indice_assuntos.json`).

| classe | critério |
|---|---|
| ok | palavras-chave da ementa ≥ 35% na resposta |
| parcial | 20–35% |
| divergente | < 20% (pegou a linha errada / alucinou) |
| falso_neg | devolveu a trava sendo in-domain |
| over_trigger | prefixo "premissa não confere" em pergunta neutra |

```bash
.venv\Scripts\python src\avalia_bateria_cvm.py 30      # amostra 30 (~15 min no 7b)
.venv\Scripts\python src\avalia_bateria_cvm.py 0       # todos os 250
# -> tests/avaliacao_cvm.json (resumo + casos)
```

### Teto do modo SÓ-PROMPT (medido, 7b, tabela de 250 linhas queimada)

| versão | prompt | ok/30 | aceitável | observação |
|---|---|---|---|---|
| v4 (ótima) | trava + tabela 3-dígitos + regra 7 anti-confusão | **47%** | **67%** | config registrada em `criar_modelo_trava.py` |
| v5 | v4 + procedimento de localização explícito | 40% | 63% | super-restricionou o 7b; **saiu pior** |

**Conclusão:** o modo só-prompt chegou a ~2/3 aceitável. O terço restante de erros
é **confusão nº↔linha** (ex.: nº89 respondendo com o texto da nº88; nº209 com
outro assunto de oferta pública) — falha de lookup em tabela de 250 linhas num
contexto de ~34K. É exatamente isso que o **RAG elimina por construção** (injeta
só a linha certa; o modelo não precisa procurar). Não vale insistir no prompt
além daqui; o próximo salto é o RAG (seção 10).

Arquivos de evidência (versionar na TCC):
- `tests/avaliacao_v5_cvm.json` (amostra 30, v5) e `tests/bateria_cvm_v1/v2/v3.json`.

---

## 10. (Próxima — Semana 02) RAG / busca semântica

Tudo já está no lugar:

- **Embeddings:** modelo `bge-m3` (1024 dimensões) **já está instalado** no Ollama.
- **Banco:** `db/init.sql` cria `chunks_regulatorios` com `embedding vector(1024)` (pgvector).

Próximos passos (fora do escopo desta UC01):
1. Subir o Postgres: `docker compose up -d postgres_vector` (ou rodar o `init.sql`).
2. Chunking respeitando a hierarquia (artigo > parágrafo > inciso) dos dados em
   `data_lake/processed/`.
3. Gerar embeddings com `bge-m3` e gravar em `chunks_regulatorios`.
4. Perguntar por similaridade: *"o que a CVM regulou sobre [assunto]"* → SLM responde
   ancorado no texto normativo.

---

## Tabela de saída rápida

| Arquivo | O que é | Gerado por |
|---|---|---|
| `data_lake/processed/<subpasta>/resolNNN.md` | Norma limpa (metadados + texto) | estágio 1 |
| `data_lake/processed/_indice_assuntos.json` | Índice de assuntos (p/ RAG) | estágio 1 |
| `tests/compreensao_resolucoes.json` | 253 fichas de assunto (SLM) | estágio 2 |
| `tests/evidencia_extracao.json` | Ficha normativa de 1 trecho | `teste_extracao_slm.py` |
