# SLM-CVM: Extração e Inteligência Regulatória com Small Language Models

Projeto de Iniciação Científica focado no processamento, extração estruturada e recuperação inteligente (RAG) de normas da **CVM (Comissão de Valores Mobiliários)** utilizando modelos de linguagem de pequeno porte (**SLMs — Small Language Models**) em ambiente local e seguro, aliado a um banco de dados relacional e vetorial.

---

## 👥 Dupla e Trilhas de Pesquisa

O projeto é conduzido em conjunto, organizado em duas trilhas complementares:

| Pesquisador | Trilha | Foco Principal |
|---|---|---|
| **Kelvin** | **Trilha B: IA & SLM** | Infraestrutura de inferência local (Ollama nativo ou Docker), seleção de modelos SLM (`qwen2.5-coder:7b`), organização do acervo (`organizar_resolucoes.py`), compreensão do assunto por prompt trava (`compreender_resolucoes.py`), validação estruturada com Pydantic e geração de embeddings. |
| **Yuri** | **Trilha A: Dados & Banco** | Modelagem relacional/vetorial (`pgvector`), governança do Data Lake, ingestão documental, deduplicação por hash (SHA-256) e catalogação do acervo da CVM. |

---

## 🏗️ Arquitetura da Solução

```
[Acervo Normativo CVM (docs/resolucoes/**/*.md)]
                 │
                 ▼
       ┌──────────────────────────┐
       │ 1. organizar_resolucoes  │  limpa ruído (fonte/mirror/PDF/rodapé)
       │    (src/)                 │  → data_lake/processed/ + _indice_assuntos.json
       └──────────────────────────┘
                 │
                 ▼
       ┌──────────────────────────┐
       │ 2. compreender_slm       │  SLM explica APENAS o assunto
       │    (compreender_...)     │  PT-BR · sem código · sem história
       └──────────────────────────┘
            │               │
     (Ollama local) (JSON Schema Pydantic)
            │               │
            ▼               ▼
   Ollama (qwen2.5-coder:7b) ──► [fichas de assunto JSON]
            │
            ▼
   [PostgreSQL 16 + pgvector (BGE-M3)]  ← etapa 02 (RAG)
```

### Componentes Principais

1. **Ollama (Inferência Local e Privada)**:
   - Roda **nativo** (porta `11434`) ou em Docker (`docker-compose.yml`).
   - Modelo utilizado: `qwen2.5-coder:7b` — compacto, segue JSON Schema via `format`, sem custo de nuvem. O `qwen2.5:3b` ficou como plano B; o que está instalado e em uso é o 7b.
2. **Organização do acervo (`src/organizar_resolucoes.py`)**:
   - Remove do `.md` bruto as linhas de fonte/espelho, a seção de anexos (PDF/DOC), as marcações `<sub>Fonte</sub>`, o rodapé de espelho e o bloco de assinatura.
   - Mantém cabeçalho de metadados + **texto normativo puro**, escreve em `data_lake/processed/<subpasta>/` e emite `data_lake/processed/_indice_assuntos.json`.
   - 253 resoluções organizadas, com colisão à prova de path (2 normas multi-tag com mesmo número saíram em pastas distintas).
3. **Compreensão do assunto (`src/compreender_resolucoes.py`)**:
   - System-prompt trava: **pt-BR, apenas o objeto da norma, sem código, sem história, só CVM/resoluções**.
   - Saída forçada ao schema `CompreensaoAssunto` (`norma`, `assunto`, `se_aplica_a`, `tem_prazo_ou_multa`) via JSON Schema.
   - Execução: 253 fichas em ~19 min, 0 erro → `tests/compreensao_resolucoes.json`.
4. **Extração de metadados (`src/teste_extracao_slm.py`)**:
   - A "ficha normativa" rígida `FichaNormativa` via Pydantic (`orgao`, `numero_norma`, `assunto_principal`, `possui_prazo_ou_multa`). Aceita `--texto-arquivo` e `--modelo`.
5. **PostgreSQL + pgvector (etapa 02 — RAG)**:
   - Tabela `chunks_regulatorios` com `embedding vector(1024)` (`db/init.sql`), pronta para BGE-M3 e busca semântica.
6. **Modelo-alias com trava de domínio (`cvm-resolucoes`)**:
   - Registro no Ollama (via [`src/criar_modelo_trava.py`](./src/criar_modelo_trava.py)) a partir de `qwen2.5-coder:7b` (`num_ctx=16384`, `temperature=0`, `repeat_penalty=1.1`) com system prompt **embutido no modelo**.
   - **Escopo estrito e triagem temática:** focado **exclusivamente nas Resoluções da CVM** em português (`pt-BR`), sem RAG/pgvector nesta fase. Antes de recusar perguntas de programação ou do dia a dia, verifica se há vínculo com alguma Resolução da biblioteca de 250 normas (23.724 chars / ~8,6K tokens); se houver, responde sob a ótica das Resoluções (sem código); se não houver, devolve exatamente: `Não consta na base de conhecimento da CVM.`
   - **Validação da trava (`src/testar_trava_cvm.py`):** 7/7 testes aprovados (CVM + bloqueio de Python, história, receita e esportes).
   - **Desempenho e Hardware:** consulte **[`DESEMPENHO.md`](./DESEMPENHO.md)** para benchmarks medidos em CPU-only (`num_gpu=0`), modo híbrido de ~4 GB na GPU (`num_gpu=16`) e limite de 4 vs. 2 núcleos (`num_thread`).
   - Uso: `ollama run cvm-resolucoes`, `POST /api/chat` ou a rota OpenAI-compatible `POST /v1/chat/completions` (`http://127.0.0.1:11434/v1`) — é essa última que os plugins de IDE consomem.
   - **Hermes Desktop:** rejeita modelos com janela < 64K no init (o 7b tem 32K).
     Se a máquina aguentar o 30b, dá pra usar via `--base qwen3-coder:30b` — ver
     seção 8.1 de [`instrucao.md`](./instrucao.md).
   - **Outros apps/IDEs (VS Code/Cline, OpenCode, Cursor, Aider, Python-SDK, curl):**
     seção **8** de [`instrucao.md`](./instrucao.md) traz a receita única `base_url
     http://127.0.0.1:11434/v1` + `model cvm-resolucoes` — a trava vem queimada no
     modelo, o app só nomeia ele.
   - **Avaliação quantitativa:** `src/avalia_bateria_cvm.py` (bateria automática
     30/250 normas, sem RAG) → `tests/avaliacao_cvm.json`. Evidências em
     `tests/bateria_cvm_v1.json`, `bateria_cvm_v2.json`, `avaliacao_v5_cvm.json`.

---

## 📁 Estrutura do Repositório

```text
SLM-CVM/
├── data_lake/                     # Zonas do Data Lake (raw / processed / quarantine / silo)
│   └── processed/                 # Resoluções LIMPAS (metadados + texto normativo)
│       ├── <subpasta_cvm>/        # ex.: Normas_Contabeis, Ofertas_Publicas, ...
│       │   └── resolNNN.md
│       └── _indice_assuntos.json  # índice p/ RAG: norma, data, tag, ementa, caminho
├── db/
│   └── init.sql                   # DDL PostgreSQL (pgvector, documentos_regulatorios, chunks_regulatorios)
├── docs/
│   ├── resolucoes/                # acervo BRUTO da CVM (espelho do site, 253 .md + anexos)
│   └── (deliberações, pareceres, ofícios, sandbox, ... )
├── src/
│   ├── criar_modelo_trava.py      # Cria/atualiza o modelo cvm-resolucoes no Ollama
│   ├── testar_trava_cvm.py        # Bateria rápida de validação da trava (7 testes)
│   ├── organizar_resolucoes.py    # Etapa 1: limpa docs/resolucoes → data_lake/processed
│   ├── compreender_resolucoes.py  # Etapa 2: SLM explica o assunto (PT-BR, trava de schema)
│   ├── treino_resolucoes.py       # Batch de extração FichaNormativa sobre docs/resolucoes
│   └── teste_extracao_slm.py      # Extração de metadados (ficha rígida) p/ um trecho
├── tests/
│   ├── evidencia_extracao.json         # saída de teste_extracao_slm.py
│   ├── treino_resolucoes_evidencia.json
│   └── compreensao_resolucoes.json     # 253 fichas de assunto (etapa 2)
├── docker-compose.yml             # pgvector + ollama
├── requirements.txt               # ollama + pydantic
├── DESEMPENHO.md                  # Especificações de hardware e benchmarks reais
├── instrucao.md                   # runbook passo a passo
├── .gitignore
└── README.md
```

---

## 📌 Status Atual do Projeto (UC01 — Sem01)

- [x] **Infraestrutura de inferência local**: Ollama disponível (nativo na porta `11434` ou via `docker-compose.yml`). Modelo em uso: `qwen2.5-coder:7b`.
- [x] **Modelagem de Dados (`db/init.sql`)**: extensão `vector` (pgvector), `documentos_regulatorios` (dedup por `hash_sha256`), `chunks_regulatorios` com `embedding vector(1024)` — pronta para a etapa de RAG.
- [x] **Acervo CVM espelhado**: `docs/resolucoes/` com 253 resoluções em `.md` (+ anexos PDF/DOCX/DOC).
- [x] **Organização do acervo (`src/organizar_resolucoes.py`)**: 253 normas limpas em `data_lake/processed/` + `_indice_assuntos.json` (cabeçalho de metadados + texto normativo puro; colisão à prova de path).
- [x] **Compreensão do assunto (`src/compreender_resolucoes.py`)**: 253 fichas de assunto (PT-BR, sem código, sem história, só CVM) em `tests/compreensao_resolucoes.json` — 0 erro, ~19 min.
- [x] **Script de Extração de Metadados (`src/teste_extracao_slm.py`)**: ficha `FichaNormativa` via Pydantic, saída em `tests/evidencia_extracao.json`.

### Exemplo de Ficha de Assunto Gerada (etapa 2)

Para a **Resolução CVM nº 21** (dados organizados em `data_lake/processed/`):

```json
{
  "norma": "Resolução CVM nº 21",
  "assunto": "Exercício profissional de administração de carteiras de valores mobiliários",
  "se_aplica_a": "Administradores de carteiras de valores mobiliários",
  "tem_prazo_ou_multa": false
}
```

---

## 🚀 Como Executar o Projeto

> **Atalho:** para o fluxo completo passo a passo (comandos prontos, verificações e o que
> cada etapa entrega), use **[`instrucao.md`](./instrucao.md)**. Resumo abaixo.

### 1. Pré-requisitos
- [Python 3.10+](https://python.org/) (este projeto usa 3.11).
- Ollama **nativo** (recomendado aqui) — verifique: `ollama list` mostra `qwen2.5-coder:7b`
  e a porta `11434` responde. Alternativa: Docker (`docker-compose.yml`).
- Git.

### 2. Subir o Ollama

**Nativo (como está neste ambiente):** o Ollama já roda como app da bandeja do Windows. Confirme:

```bash
curl http://127.0.0.1:11434/api/version
ollama list
```

**Docker (alternativa — Postgres + Ollama em container):**

```bash
docker compose up -d
docker exec -it ollama ollama pull qwen2.5:3b
```

### 3. Configurar o Ambiente Python

Crie e ative um ambiente virtual:

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

### 4. Etapa 1 — Organizar o acervo (dado limpo para o modelo)

```bash
.venv/Scripts/python src/organizar_resolucoes.py
# -> data_lake/processed/<subpasta>/resolNNN.md   (texto normativo puro)
# -> data_lake/processed/_indice_assuntos.json
```

### 5. Etapa 2 — Compreender o assunto (SLM, PT-BR, trava de schema)

```bash
.venv/Scripts/python src/compreender_resolucoes.py               # todos (253)
.venv/Scripts/python src/compreender_resolucoes.py --limite 5    # amostra
.venv/Scripts/python src/compreender_resolucoes.py --limitar "Companhia"
# -> tests/compreensao_resolucoes.json
```

### 6. Extração de metadados (ficha rígida p/ um trecho)

```bash
.venv/Scripts/python src/teste_extracao_slm.py
.venv/Scripts/python src/teste_extracao_slm.py --texto-arquivo docs/resolucoes/Atos expedidos pela CVM/resol001.md
# -> tests/evidencia_extracao.json
```

### 7. Criar e rodar o `cvm-resolucoes` (nesta ou em outra máquina)

Para replicar o modelo focado em Resoluções da CVM em outra máquina:

```powershell
# 1. Clonar no Windows habilitando caminhos longos (necessário para docs/oficios-circulares)
git clone -c core.longpaths=true <URL-DO-REPOSITORIO>
cd SLM-CVM

# 2. Baixar o modelo base no Ollama e gerar o cvm-resolucoes
ollama pull qwen2.5-coder:7b
python src/criar_modelo_trava.py

# 3. Validar a trava de domínio e conversar
python src/testar_trava_cvm.py
ollama run cvm-resolucoes
```

> **Requisitos e Desempenho:** consulte **[`DESEMPENHO.md`](./DESEMPENHO.md)** para ver os testes reais de consumo de RAM/VRAM, limite de núcleos (`num_thread`) e simulação em GPU de 4 GB (`num_gpu=16`).

> **Backend nativo vs Docker:** os scripts usam `OLLAMA_HOST` (padrão `http://127.0.0.1:11434`).
> O modelo padrão é `qwen2.5-coder:7b`; troque com `--modelo` (ex.: `--modelo qwen2.5:3b` se
> rodar o Docker e tiver o 3b puxado). O PostgreSQL só é necessário na etapa 02 (RAG).

---

## 🔮 Próximos Passos (Roadmap)

- **Semana 02**:
  - Ingestão contínua de normas e cálculo de hash SHA-256 no banco relacional.
  - Pipeline de chunking com respeito à hierarquia da norma (Artigos, Parágrafos, Incisos).
  - Geração de embeddings com modelo BGE-M3 (vetores de 1024 dimensões) persistidos em `chunks_regulatorios`.
  - Construção de mecanismo de busca semântica e avaliação de respostas do SLM contra o texto regulatório oficial.
