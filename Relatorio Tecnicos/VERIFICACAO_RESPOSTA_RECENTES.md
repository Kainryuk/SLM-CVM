# Relatório de Verificação — Resposta sobre "Principais e Mais Recentes Resoluções"

**Data da verificação:** 18/11/2026  
**Pergunta testada:** `me fala as principais e mais recente resolução`  
**Base de confronto:** `data_lake/processed/_indice_assuntos.json` e textos oficiais em `docs/resolucoes/`.

---

## 1. Veredito Geral: **Resposta Reprovada (Alucinação + Loop)**

A resposta obtida **não é confiável**: além de **omitir todas as resoluções mais recentes (de 2026)**, ela apresenta **auto-contradições** (*"Resolução X altera a Resolução X"*), **ementas trocadas/inventadas** e **repetição em loop** dos itens 1–4 nos itens 7–10.

---

## 2. Conferência Item a Item

| Item na Resposta | O que o Modelo Disse | O que Consta Oficialmente no Acervo | Veredito |
|---|---|---|---|
| **1 e 7 — Res. CVM nº 24** (`05/03/2021`) | *"Altera a Resolução CVM nº 24, estabelecendo novas diretrizes para a divulgação de informações financeiras e operacionais dos investidores."* | **Aprova o Regimento Interno da Comissão de Valores Mobiliários.** Não altera a si mesma nem trata de divulgação financeira de investidores. | ❌ **Falso** |
| **2 e 8 — Res. CVM nº 175** (`23/12/2022`) | *"Constitui, o funcionamento e a divulgação de informações dos fundos de investimento em português e espanhol."* | Dispõe sobre constituição, funcionamento, divulgação de informações e prestação de serviços dos fundos de investimento. **Não existe menção a "espanhol".** | ❌ **Impreciso / Alucinado** |
| **3 e 9 — Res. CVM nº 86** (`31/03/2022`) | *"Altera a Resolução CVM nº 86, estabelecendo novas diretrizes para a oferta pública de distribuição de valores mobiliários de emissão de sociedade aberta."* | Dispõe sobre oferta pública de **contratos de investimento coletivo (CIC) hoteleiro** e revoga a Instrução CVM nº 602/18. | ❌ **Falso** |
| **4 e 10 — Res. CVM nº 160** (`13/07/2022`) | *"Altera a Resolução CVM nº 160, estabelecendo novas diretrizes para o registro e a prestação de informações periódicas dos emissores de valores mobiliários."* | Dispõe sobre **ofertas públicas de distribuição primária ou secundária** de valores mobiliários e negociação dos valores ofertados (quem trata de informações periódicas de emissores é a **nº 80**). | ❌ **Falso** |
| **5 — Res. CVM nº 80** (`29/03/2022`) | *"Altera a Resolução CVM nº 80, estabelecendo novas diretrizes para o registro e a prestação de informações periódicas..."* | Dispõe sobre registro e prestação de informações periódicas e eventuais dos emissores. **Não altera a si mesma.** | ❌ **Alucinação de auto-alteração** |
| **6 — Res. CVM nº 193** (`20/10/2023`) | *"Altera a Resolução CVM nº 193, estabelecendo novas diretrizes para a divulgação de informações financeiras dos investidores."* | Dispõe sobre elaboração e divulgação do **relatório de informações financeiras relacionadas à sustentabilidade (padrão ISSB)**. | ❌ **Falso** |

### Resoluções realmente mais recentes no acervo (omitidas na resposta)
* **Resolução CVM nº 251 (`05/11/2026`):** Altera a Resolução CVM nº 9, de 27 de outubro de 2020.
* **Resolução CVM nº 250 (`05/11/2026`):** Altera a Resolução CVM nº 19, de 25 de fevereiro de 2021.
* **Resolução CVM nº 249 (`13/10/2026`):** Institui, em caráter experimental, o Programa Piloto DLT CVM.

---

## 3. Padrões de Erro Identificados

1. **Alucinação de auto-alteração:** Em 8 dos 10 itens, o modelo escreveu *"Resolução X altera a Resolução X"*.
2. **Mistura de temas e idioma:** Trocou o conteúdo da nº 160 pelo da nº 80, da nº 86 pelo de companhias abertas, da nº 193 (ISSB) por investidores, e inventou *"em português e espanhol"* na nº 175.
3. **Loop de repetição:** Os itens 7, 8, 9 e 10 são cópias literais dos itens 1, 2, 3 e 4.
4. **Causa raiz (bypass do proxy):** Essa resposta foi gerada diretamente pelo modelo `cvm-resolucoes` na porta padrão `11434` **sem passar pelo pré-filtro** (`proxy_cvm.py` na porta `11435`), pois quando passa pelo pré-filtro a mesma pergunta retorna as **Resoluções nº 251, nº 250 e nº 249 (de 2026)**.

---

## 4. Como Garantir que Está Passando pelo Pré-Filtro

* **No terminal:** confirme que `OLLAMA_HOST` está apontando para `http://127.0.0.1:11435` (abra um **novo** terminal após a instalação) antes de rodar `ollama run cvm-resolucoes`, ou execute direto:
  ```powershell
  cvm-chat
  ```
* **No aplicativo Desktop do Ollama:** a janela gráfica do Ollama costuma ignorar `OLLAMA_HOST` e falar direto com a porta `11434`; para ter 100% de precisão com pré-filtro, use o terminal (`cvm-chat` ou `ollama run` com `OLLAMA_HOST=http://127.0.0.1:11435`).

---

## 5. Reteste Confirmado com o Pré-Filtro Ativo (`100% Correto`)

Após executar a mesma pergunta passando pelo pré-filtro (`[Pré-filtro]: ['Resolução CVM nº 251', 'Resolução CVM nº 250', 'Resolução CVM nº 249', 'Resolução CVM nº 248', 'Resolução CVM nº 247', 'Resolução CVM nº 246', 'Resolução CVM nº 245', 'Resolução CVM nº 244']`), a resposta obtida foi **100% fiel** aos arquivos oficiais em `data_lake/processed/_indice_assuntos.json`:

| Norma na Resposta | Data Retornada | Ementa Retornada | Conferência Oficial |
|---|---|---|---|
| **Resolução CVM nº 251** | `5/11/2026` | Altera a Resolução CVM nº 9, de 27 de outubro de 2020. | ✅ **100% Exato** |
| **Resolução CVM nº 250** | `5/11/2026` | Altera a Resolução CVM nº 19, de 25 de fevereiro de 2021. | ✅ **100% Exato** |
| **Resolução CVM nº 249** | `13/10/2026` | Institui, em caráter experimental, o Programa Piloto DLT CVM destinado à realização de testes no mercado de valores mobiliários por meio de redes de tecnologia de registro distribuído, compreendendo operações experimentais de emissão, oferta, negociação, liquidação e pós-negociação de valores mobiliários em redes admitidas para participação no Programa. | ✅ **100% Exato** |

### Comparativo Final (Mesma Pergunta, Mesmo Modelo 7B)
* **Sem pré-filtro (porta `11434` direta):** 0/10 confiáveis, alucinações de auto-alteração, troca de ementas, idioma inventado, loop de repetição e omissão das normas de 2026.
* **Com pré-filtro (`cvm-chat` / proxy `11435`):** **3/3 (100%) exatas** em número, data e ementa literal, sem alucinações e sem repetição.
