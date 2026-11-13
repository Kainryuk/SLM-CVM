# Especificações de Hardware e Desempenho (`cvm-resolucoes`)

Este documento reúne os benchmarks reais medidos e os requisitos de hardware para executar o modelo **`cvm-resolucoes:latest`** (baseado em `qwen2.5-coder:7b`) localmente via **Ollama**, no modo atual **somente por prompt (sem RAG / pgvector)**.

---

## ⚙️ Especificações do Modelo Atual

| Parâmetro | Valor Configurado |
|---|---|
| **Modelo base** | `qwen2.5-coder:7b` (~4,7 GB em disco, quantização padrão) |
| **Janela de contexto (`num_ctx`)** | `16384` tokens |
| **Tamanho do `SYSTEM` prompt** | `23.724` caracteres (`8.671` tokens medidos com a biblioteca de 250 Resoluções) |
| **Parâmetros de inferência** | `temperature: 0`, `repeat_penalty: 1.1` |
| **Escopo** | Exclusivamente **Resoluções da CVM** em português (`pt-BR`), com triagem temática |

---

## 📊 Benchmarks Medidos (Testes Reais)

Todos os testes abaixo foram executados localmente via API `/api/chat` do Ollama (`cvm-resolucoes:latest`), medindo o processamento completo do prompt de sistema (`8.671` tokens) e a geração da resposta:

| Cenário Simulado | Config Ollama (`options`) | Memória (`ollama ps`) | Leitura do Prompt (`8.671` tok) | Velocidade de Geração | Tempo Total *(c/ reload)* | Avaliação Prática |
|---|---|---|---|---|---|---|
| **100% CPU + RAM (sem GPU)** | `num_gpu: 0` | `6,0 GB` (`100% CPU`) | **> 300 s** *(Timeout)* | — | **> 300 s** | Inviável para prompt de ~8,6K tokens na CPU |
| **Híbrido ~4 GB GPU (threads padrão)** | `num_gpu: 16` | `4,2 GB` (`81% GPU / 19% CPU`) | `18,2 s` (`476,5 tok/s`) | **5,0 tok/s** *(63 tok em 12,7 s)* | `56,9 s` | Bom e estável |
| **Híbrido ~4 GB GPU + 4 núcleos** | `num_gpu: 16`, `num_thread: 4` | `4,2 GB` (`81% GPU / 19% CPU`) | `17,8 s` (`485,8 tok/s`) | **3,2 tok/s** *(49 tok em 15,1 s)* | `59,6 s` | **Limite mínimo confortável** |
| **Híbrido ~4 GB GPU + 2 núcleos** | `num_gpu: 16`, `num_thread: 2` | `4,2 GB` (`81% GPU / 19% CPU`) | `17,8 s` (`487,8 tok/s`) | **2,1 tok/s** *(49 tok em 23,3 s)* | `67,8 s` | **Limite extremo** (apenas respostas curtas) |

> **Observações sobre os números:**
> - O **Tempo Total** inclui o recarregamento do modelo na troca de configuração. Com o modelo já carregado em memória (`keep_alive`), o tempo por pergunta cai para `tempo de prompt + geração` (ou apenas geração quando o histórico/prefixo está em cache).
> - **Atenção ao comparar com GPU Integrada (iGPU) real:** na simulação acima com `num_gpu: 16`, os `~3,4 GB` alocados na GPU rodaram em VRAM dedicada (largura de banda alta). Em notebooks com **iGPU de 4 GB compartilhados** (Intel Iris Xe / AMD Radeon integrada), a iGPU compartilha a banda da RAM (DDR4/DDR5), portanto a leitura inicial dos `8.671` tokens tende a ser mais lenta (na faixa de ~1 a 3 minutos na 1ª pergunta), mantendo geração próxima de `~3 a 7 tok/s`.

---

## 💻 Requisitos Recomendados por Perfil de Máquina

### 1. Recomendado (Uso fluido, 100% GPU)
* **GPU:** Dedicada com **6 GB a 8 GB de VRAM** ou superior (`num_gpu` padrão — todas as camadas na GPU).
* **RAM:** 16 GB.
* **CPU:** 4+ núcleos.

### 2. Mínimo Viável para 7B (Modo Híbrido — Notebooks c/ 4 GB de GPU/iGPU)
* **GPU / iGPU:** ~4 GB disponíveis (`num_gpu: 16` aloca ~3,4 GB na GPU e ~0,8 GB na RAM).
* **CPU:** **Mínimo 4 núcleos** (`num_thread: 4` → `~3,2 tok/s`). Abaixo disso (2 núcleos → `~2,1 tok/s`), respostas longas passam de 1 minuto só gerando texto.
* **RAM:** 16 GB recomendados (para comportar o SO + ~4,2 GB do modelo + folga para o restante do sistema).

### 3. Máquinas Modestas sem GPU (8 GB de RAM / Dual-Core)
* O modelo **7B** com prompt de `~8,6K` tokens **não é recomendado** sem GPU (consome `6,0 GB` só na RAM e excede 5 minutos na primeira leitura).
* **Alternativas:**
  1. Usar um modelo menor como **`qwen2.5:3b`** (~2 GB) ou **`qwen2.5:1.5b`** (~1 GB) via `--base`.
  2. Aguardar a integração da etapa **RAG (`pgvector`)**, que reduz o prompt de `~8.600` tokens para `~500–800` tokens e permite respostas em poucos segundos mesmo em CPU.

---

## 🛠️ Como Ajustar e Monitorar na Prática

### Limitar GPU e Núcleos no Chat do Ollama
```text
/set parameter num_gpu 16
/set parameter num_thread 4
```

### Limitar via API (`/api/chat`)
```json
{
  "model": "cvm-resolucoes",
  "messages": [{"role": "user", "content": "O que regula a Resolução CVM nº 11?"}],
  "stream": false,
  "options": {
    "num_gpu": 16,
    "num_thread": 4,
    "temperature": 0
  }
}
```

### Verificar alocação real de memória e % CPU/GPU
```powershell
ollama ps
```
