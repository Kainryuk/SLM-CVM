# SLM-CVM: Extração e Inteligência Regulatória com Small Language Models

Projeto de Iniciação Científica focado no processamento, extração estruturada e recuperação inteligente (RAG) de normas da **CVM (Comissão de Valores Mobiliários)** utilizando modelos de linguagem de pequeno porte (**SLMs — Small Language Models**) em ambiente local e seguro, aliado a um banco de dados relacional e vetorial.

---

## 👥 Dupla e Trilhas de Pesquisa

O projeto é conduzido em conjunto, organizado em duas trilhas complementares:

| Pesquisador | Trilha | Foco Principal |
|---|---|---|
| **Kelvin** | **Trilha B: IA & SLM** | Infraestrutura de inferência local (Ollama/Docker), seleção de modelos SLM (`qwen2.5:3b`), engenharia de prompts, validação estruturada com Pydantic e geração de embeddings. |
| **Yuri** | **Trilha A: Dados & Banco** | Modelagem relacional/vetorial (`pgvector`), governança do Data Lake, ingestão documental, deduplicação por hash (SHA-256) e catalogação do acervo da CVM. |

---

## 🏗️ Arquitetura da Solução

```
[Acervo Normativo CVM (PDF/HTML/TXT)]
                 │
                 ▼
       ┌──────────────────┐
       │    Data Lake     │ ── (raw / processed / quarantine / silo)
       └──────────────────┘
                 │
                 ▼
       ┌────────────────────────┐
       │ Pipeline Python        │
       │ (src/teste_extracao.py)│
       └────────────────────────┘
            │               │
     (Inferência local) (JSON Schema)
            │               │
            ▼               ▼
   ┌─────────────────┐ ┌─────────────┐
   │  Ollama Server  │ │  Pydantic   │
   │  (qwen2.5:3b)   │ │  Validação  │
   └─────────────────┘ └─────────────┘
            │
            ▼
    [JSON Estruturado] ──► [PostgreSQL 16 + pgvector]
```

### Componentes Principais

1. **Ollama (Inferência Local e Privada)**:
   - Executado em container Docker isolado.
   - Modelo utilizado: `qwen2.5:3b` — modelo compacto, rápido e capaz de seguir esquemas estruturados via JSON Schema sem custos de API em nuvem.
2. **PostgreSQL com pgvector**:
   - Banco de dados relacional e vetorial na porta `5432`.
   - Suporte a busca vetorial para embeddings de até 1024 dimensões (otimizado para modelos como `BGE-M3`).
3. **Extração com Pydantic**:
   - Imposição de uma "ficha normativa" rígida via JSON Schema garantindo que a resposta do modelo contenha campos tipados (`orgao`, `numero_norma`, `assunto_principal`, `possui_prazo_ou_multa`).
4. **Data Lake & Docs CVM**:
   - Estrutura de zonas para trânsito de dados (`raw`, `processed`, `quarantine`, `silo`).
   - Mapeamento das categorias regulatórias da CVM em `docs/`.

---

## 📁 Estrutura do Repositório

```text
SLM-CVM/
├── data_lake/                     # Estrutura de armazenamento de dados brutos e processados
│   ├── processed/                 # Documentos já normalizados/convertidos
│   ├── quarantine/                # Arquivos com erro ou validação pendente
│   ├── raw/                       # Documentos originais baixados da CVM
│   └── silo/                      # Armazenamento arquivado/imutável
├── db/
│   └── init.sql                   # DDL inicial do PostgreSQL (pgvector, tabelas e índices)
├── docs/                          # Mapeamento do acervo e categorias regulatórias CVM
│   ├── Agenda Regulatória CVM/
│   ├── Audiências e Consultas Públicas/
│   ├── Custo de Observância Regulatória/
│   ├── Deliberações/
│   ├── Instruções/
│   ├── Notas Explicativas/
│   ├── Pareceres de Orientação/
│   ├── Portarias/
│   ├── Resoluções/
│   ├── Revisão e Consolidação de Normas/
│   └── Sandbox Regulatório/
├── src/
│   └── teste_extracao_slm.py     # Script de extração de metadados com Ollama + Pydantic
├── tests/
│   └── evidencia_extracao.json    # Evidência de execução com JSON estruturado
├── docker-compose.yml             # Orquestração dos containers (pgvector + ollama)
├── requirements.txt               # Dependências Python do projeto
├── .gitignore                     # Configuração de arquivos ignorados no repositório
└── README.md                      # Documentação do projeto
```

---

## 📌 Status Atual do Projeto (UC01 — Sem01)

- [x] **Setup de Infraestrutura Docker**: Arquivo `docker-compose.yml` configurado com os serviços `postgres_vector` (PostgreSQL 16 com `pgvector`) e `ollama`.
- [x] **Modelo SLM Configurado**: Download do modelo `qwen2.5:3b` via Ollama concluído e testado.
- [x] **Modelagem de Dados Inicial (`db/init.sql`)**:
  - Habilitação da extensão vetorial `vector`.
  - Tabela `documentos_regulatorios` com controle de integridade via `hash_sha256`.
  - Tabela `chunks_regulatorios` com campo `embedding vector(1024)` para busca semântica.
- [x] **Estruturação do Acervo CVM**: Pastas organizadas em `docs/` e zonas em `data_lake/`.
- [x] **Script de Extração Normativa (`src/teste_extracao_slm.py`)**:
  - Classe Pydantic `FichaNormativa` implementada.
  - Comunicação com a API do Ollama forçando saída via `FichaNormativa.model_json_schema()`.
  - Suporte a arquivo de entrada personalizado (`--texto-arquivo`) ou trecho padrão.
- [x] **Evidência de Execução**: Teste executado com sucesso sobre a Resolução CVM nº 88/2022, com resultado persistido em `tests/evidencia_extracao.json`.

### Exemplo de Saída Estruturada Gerada

Trecho extraído da **Resolução CVM nº 88/2022**:

```json
{
  "orgao": "CVM",
  "numero_norma": "88",
  "assunto_principal": "Divulgação de Informações",
  "possui_prazo_ou_multa": true
}
```

---

## 🚀 Como Executar o Projeto

### 1. Pré-requisitos
- [Docker](https://www.docker.com/) e Docker Compose instalados.
- [Python 3.10+](https://www.python.org/) instalado.
- Git instalado.

### 2. Subir os Serviços com Docker Compose

Na raiz do projeto:

```bash
docker compose up -d
```

Verifique se os containers estão em execução:

```bash
docker compose ps
```

### 3. Baixar o Modelo no Ollama

Baixe o modelo leve `qwen2.5:3b` dentro do container do Ollama:

```bash
docker exec -it ollama ollama pull qwen2.5:3b
```

### 4. Configurar o Ambiente Python

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

### 5. Executar o Script de Extração

Para executar com o texto normativo padrão (Resolução CVM nº 88):

```bash
python src/teste_extracao_slm.py
```

Para executar informando um arquivo de texto específico:

```bash
python src/teste_extracao_slm.py --texto-arquivo caminho/para/norma.txt
```

O resultado será exibido no terminal e salvo automaticamente em `tests/evidencia_extracao.json`.

---

## 🔮 Próximos Passos (Roadmap)

- **Semana 02**:
  - Ingestão contínua de normas e cálculo de hash SHA-256 no banco relacional.
  - Pipeline de chunking com respeito à hierarquia da norma (Artigos, Parágrafos, Incisos).
  - Geração de embeddings com modelo BGE-M3 (vetores de 1024 dimensões) persistidos em `chunks_regulatorios`.
  - Construção de mecanismo de busca semântica e avaliação de respostas do SLM contra o texto regulatório oficial.
