# Relatório Técnico — Análise de Alucinações do Modelo `cvm-resolucoes` (Sem RAG/pgvector) e Plano de Mitigação

**Data:** 17/11/2026  
**Modelo avaliado:** `cvm-resolucoes` (base `qwen2.5-coder:7b`, `num_ctx=16384`, sem RAG/pgvector)  
**Parâmetro de teste informado:** `/set parameter num_gpu 16`  
**Base de verificação:** Arquivos originais espelhados em `docs/resolucoes/` e implementação atual em `src/criar_modelo_trava.py`.

---

## 1. Consolidação dos 5 Testes Realizados

Todos os testes abaixo foram confrontados diretamente com os textos oficiais espelhados em `docs/resolucoes/`:

| Norma Testada | Resposta Obtida do Modelo | Verificação no Texto Oficial | Status |
|---|---|---|---|
| **Resolução CVM nº 24** (`05/03/2021`) | Afirmou que *"altera várias outras resoluções da CVM, incluindo a Resolução CVM nº 35 e a Resolução CVM nº 80"*. | Aprova o **Regimento Interno da CVM** (`Art. 1º` e `Art. 2º`). **Zero ocorrências** das Resoluções nº 35 ou nº 80. Ela própria foi alterada depois por 15 resoluções (40/21 a 246/26). | ❌ **Alucinação** |
| **Resolução CVM nº 175** (`23/12/2022`) | Afirmou que *"estabelece as regras para a constituição, funcionamento e divulgação de informações dos fundos de investimento"*. | Confere com a ementa oficial (*"Dispõe sobre a constituição, o funcionamento e a divulgação de informações dos fundos de investimento..."*). | ✅ **Correto** |
| **Resolução CVM nº 86** (`31/03/2022`) | Afirmou que *"altera a Resolução CVM nº 161"*. | Dispõe sobre oferta pública de distribuição de **contratos de investimento coletivo (CIC) hoteleiro** e revoga a Instrução CVM nº 602/18. **Zero ocorrências** de `161`. | ❌ **Alucinação** |
| **Resolução CVM nº 161** (`13/07/2022`) | Afirmou que *"altera a Resolução CVM nº 86"*. | Dispõe sobre registro e regras de **coordenadores de ofertas públicas** de valores mobiliários. **Zero ocorrências** da Resolução nº 86. | ❌ **Alucinação** |
| **Resolução CVM nº 193** (`20/10/2023`) | Afirmou que *"altera várias outras resoluções da CVM, incluindo a Resolução CVM nº 175 e a Resolução CVM nº 86"*. | Dispõe sobre elaboração e divulgação do relatório de **informações financeiras relacionadas à sustentabilidade (padrão ISSB)**. **Zero ocorrências** das Resoluções nº 175 ou nº 86. | ❌ **Alucinação** |

**Resultado da amostra:** **5/5 (100%) de acerto em número e data**, mas apenas **1/5 (20%) de precisão no conteúdo normativo** devido à invenção de relações entre normas.

---

## 2. Padrões Identificados

1. **Alucinação sistemática de relações ("altera X e Y"):**
   Quando o modelo não encontra detalhes suficientes no prompt ou tenta expandir uma resposta curta, o `qwen2.5-coder:7b` preenche a lacuna usando um clichê jurídico (*"Esta resolução altera várias outras resoluções..."*) e inventa vínculos com outras resoluções da CVM.
2. **Contaminação de contexto entre turnos (efeito eco):**
   Os números inventados se retroalimentam na mesma conversa: após testar a nº 86 (citando 161), ao perguntar pela nº 161 ele inverteu e citou a nº 86; em seguida, na nº 193, reciclou os números 175 e 86 que estavam recentes no histórico.
3. **Limitação estrutural do prompt atual (`src/criar_modelo_trava.py`):**
   * A função `limpar_ementa_compacta()` remove explicitamente a parte final das ementas que menciona `revoga`, `altera`, `dá nova` e `prorroga`, e trunca cada resumo em **95 caracteres** (`MAX_CHARS_ASSUNTO = 95`).
   * A tabela `BIBLIOTECA` traz apenas `NNN: assunto_curto` (sem data e sem indicação de normas alteradas/revogadas).
   * O `SISTEMA_TEMPLATE` atual não possui uma **regra proibitiva explícita** impedindo o modelo de afirmar que uma norma altera ou revoga outra quando isso não consta na tabela.
4. **Papel real do parâmetro `/set parameter num_gpu 16`:**
   * `num_gpu 16` define apenas quantas camadas da rede neural são alocadas na GPU (impactando velocidade e uso de VRAM), **não altera o raciocínio nem previne alucinações**. A causa dos erros é puramente informacional (lacuna no índice compactado + ausência de trava factual no prompt), não de hardware.

---

## 3. Como Resolver Sem Implementar `pgvector` ou RAG

É possível reduzir drasticamente essas alucinações mantendo a arquitetura atual 100% baseada em prompt e contexto no Ollama:

### A. Travar afirmações não presentes na tabela (Prompt Engineering)
Adicionar no topo e no rodapé do `SYSTEM_TEMPLATE` regras explícitas de fidelidade factual:
* **Proibição de inferência relacional:** *"NUNCA afirme que uma resolução altera, revoga ou substitui outra norma se isso não estiver escrito literalmente na linha correspondente da BIBLIOTECA."*
* **Admissão de limite:** *"Baseie-se EXCLUSIVAMENTE no texto da linha `NNN:` da BIBLIOTECA. Não complete a resposta com suposições ou detalhes de memória prévia fora da tabela."*

### B. Enriquecer a linha da `BIBLIOTECA` mantendo o tamanho enxuto
Em vez de descartar `revoga`/`altera` e a data na compactação:
* Preservar **data** e **relações reais** extraídas diretamente das ementas em um formato compacto:
  `NNN (DD/MM/AAAA): <assunto principal> | altera/revoga: <lista ou "nenhuma na ementa">`
* Para ~250 Resoluções, incluir data e campo explícito de alteração/revogação cabe dentro da janela `num_ctx=16384` já configurada no modelo, eliminando o "chute" do modelo sobre o que cada norma altera.

### C. Citação obrigatória antes da resposta (*Grounding*)
Instruir o modelo nos exemplos (*few-shot*) a sempre exibir primeiro o registro exato da biblioteca antes de redigir a explicação, por exemplo:
* *"Registro [024]: Regimento Interno da CVM (05/03/2021). Não há indicação de alteração de outras resoluções."*

### D. Isolamento de sessão nos testes + parâmetros determinísticos
* Nos testes interativos no Ollama, executar **`/clear`** entre perguntas de normas diferentes para evitar que números citados na resposta anterior contaminem a próxima.
* Manter `/set parameter num_gpu 16` apenas para controle de GPU/VRAM, combinando-o com parâmetros de decodificação estritamente determinísticos já no modelo: `temperature: 0`, `top_k: 1` (ou `top_p: 0.1`), `repeat_penalty: 1.1` e `num_ctx: 16384`.

---

## 4. Resultados Pós-Implementação (`src/criar_modelo_trava.py`)

As melhorias acima foram aplicadas em `src/criar_modelo_trava.py` (âncoras `[NNN]`, data compacta `DD/MM/AA`, extração explícita de `altera/revoga`, trava anti-alucinação no topo/rodapé, `temperature: 0`, `top_k: 1`, `top_p: 0.1`, reduzindo o prompt para `32.899` caracteres em `num_ctx=16384`) e retestadas nas mesmas 5 Resoluções com `num_gpu=16`:

| Norma Testada | Resultado Pós-Ajuste | Diagnóstico |
|---|---|---|
| **Res. CVM nº 24** | Citou `[024] (05/03/21)`: Regimento Interno da CVM, sem alteração/revogação citada na ementa. | ✅ **Correto** (eliminou a alucinação sobre nº 35 e nº 80). |
| **Res. CVM nº 175** | Citou `[175] (23/12/22)`: constituição, funcionamento e divulgação de informações dos fundos de investimento. | ✅ **Correto no tema** (não inventou alterações; omitiu apenas o trecho de revogações). |
| **Res. CVM nº 86** | Citou `[027] (08/04/21)` no lugar de `[086]`. | ❌ **Erro de ponteiro (*Lost in the Middle*)** — leu outra linha da tabela. |
| **Res. CVM nº 161** | Citou `[222] (10/12/24)` no lugar de `[161]`. | ❌ **Erro de ponteiro (*Lost in the Middle*)** — leu outra linha da tabela. |
| **Res. CVM nº 193** | Citou `[193] (20/10/23)`, mas misturou o assunto com "investimento coletivo hoteleiro" (da `086`). | ⚠️ **Mistura de linhas** (parou de inventar que altera 175/86, mas confundiu o conteúdo). |

### Conclusão Técnica
* A engenharia de prompt e os parâmetros determinísticos **eliminaram o padrão de inventar relações ("altera X e Y")** nas normas localizadas corretamente (`24`, `175` e `193`).
* Porém, o teste comprovou o **limite físico de atenção do modelo 7B**: manter **250 resoluções (~32,9 mil caracteres)** dentro do `SYSTEM` prompt faz o modelo errar o ponteiro de linha (`[027]` no lugar de `[086]`, `[222]` no lugar de `[161]`) e misturar conteúdos de linhas distantes.
* **Próximo passo sem `pgvector`:** caso queira 100% de precisão antes do RAG vetorial, a solução é fazer um **pré-filtro leve em Python** sobre `_indice_assuntos.json` (buscando pelo número da resolução ou palavras-chave da pergunta) e enviar no prompt apenas as **1 a 5 normas encontradas**, em vez de enviar todas as 250 linhas de uma vez.

---

## 5. Solução Implementada: Pré-Filtro Python + Proxy Automático (`7/7` de Acerto)

Seguindo a conclusão acima, foram implementados dois componentes sem dependência externa (100% Python padrão, sem `pgvector` ou RAG vetorial):

1. **Consulta com Pré-Filtro e Auto-Ativação (`src/consultar_cvm.py` + `cvm-chat.cmd`):**
   * Filtra localmente `data_lake/processed/_indice_assuntos.json` por número explícito de resolução ou palavras-chave (ignorando acentos e *stopwords*), enviando ao `qwen2.5-coder:7b` apenas as **1 a 5 normas relevantes** (com trecho inicial do texto oficial quando há match único) em janela reduzida (`num_ctx=4096`).
   * Inclui `garantir_ollama()`: verifica se `127.0.0.1:11434` está ativo e, caso não esteja, inicia `ollama serve` automaticamente antes de responder.
   * Disponível globalmente no terminal via `cvm-chat` (modo chat interativo com `/gpu <N>` e `/sair`, ou `-p "pergunta"`).

2. **Proxy HTTP Automático (`src/proxy_cvm.py`):**
   * Servidor compatível com **Ollama** (`/api/chat`, `/api/generate`, `/api/tags`) e **OpenAI** (`/v1/chat/completions`) na porta `11435`.
   * Qualquer UI, extensão ou agente apontado para `http://127.0.0.1:11435` passa automaticamente pelo pré-filtro e pela auto-ativação do Ollama.

### Resultados Medidos após o Pré-Filtro (`--lote-teste --num-gpu 16`)

| Caso de Teste | Pré-filtro Selecionado | Resultado Obtido | Status |
|---|---|---|---|
| **Res. CVM nº 24** | `['Resolução CVM nº 24']` | Aprovou o Regimento Interno da CVM. | ✅ **Correto** |
| **Res. CVM nº 175** | `['Resolução CVM nº 175']` | Constituição, funcionamento, divulgação de informações e prestação de serviços dos fundos de investimento (23/12/2022). | ✅ **Correto** |
| **Res. CVM nº 86** | `['Resolução CVM nº 86']` | Oferta pública de CIC hoteleiro e revoga a Instrução CVM nº 602/18 (31/03/2022). | ✅ **Correto** |
| **Res. CVM nº 161** | `['Resolução CVM nº 161']` | Registro e regras de coordenadores de ofertas públicas de valores mobiliários (13/07/2022). | ✅ **Correto** |
| **Res. CVM nº 193** | `['Resolução CVM nº 193']` | Relatório de informações financeiras relacionadas à sustentabilidade — ISSB (20/10/2023). | ✅ **Correto** |
| **Escreva um script Python...** | Bloqueio de domínio | *"Não consta na base de conhecimento da CVM."* | ✅ **Correto** |
| **Plataforma de investimento coletivo...** | Top-5 temáticas (incluiu `nº 88`) | Identificou a **Resolução CVM nº 88** (27/04/2022) e revogação da Instrução nº 588/17. | ✅ **Correto** |

**Taxa final observada:** **7/7 (100%)** sem alucinações, sem vazamento de código e sem erro de ponteiro. Também validado via proxy HTTP (`http://127.0.0.1:11435`) nos endpoints `/health`, `/api/chat` e `/v1/chat/completions`.
