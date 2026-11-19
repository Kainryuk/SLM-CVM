# Documento de Ontologia e Taxonomia de Entidades da CVM

**Projeto:** SLM-CVM (Estudo de Modelos de Linguagem Pequenos para Normativos da CVM)  
**Etapa / Semana:** Etapa 1 — S03 (Definição da ontologia e taxonomia de entidades da CVM)  
**Base Empírica:** Análise do acervo espelhado em [`docs/`](./docs) e das 253 fichas extraídas das Resoluções em [`tests/compreensao_resolucoes.json`](./tests/compreensao_resolucoes.json) e [`data_lake/processed/_indice_assuntos.json`](./data_lake/processed/_indice_assuntos.json).

---

## 1. Objetivo e Motivação

Na etapa anterior (S02), a extração livre com o modelo local (`qwen2.5-coder:7b`) sobre as 253 Resoluções gerou **0 erros de formato**, mas evidenciou **dispersão terminológica** nos nomes de entidades. Por exemplo, o mesmo sujeito regulado apareceu grafado de formas distintas:
* `"Companhias abertas"` (79 ocorrências), `"companhias abertas"` (18), `"Empresas de capital aberto"` (4) e `"Empresas listadas na B3"` (2).
* `"Todos os órgãos e entidades sujeitos à regulamentação da CVM"` (2) vs `"Todos os órgãos e entidades sujeitas à regulamentação da CVM"` (2).

Esta ontologia define um **vocabulário controlado (taxonomia)** e um **modelo formal de entidades, atributos e relacionamentos** para padronizar futuras extrações de NLP/LLM, filtros de busca em banco vetorial (`pgvector`) e grafos normativos.

---

## 2. Taxonomia de Atos Normativos (`TipoNorma`)

Hierarquia baseada nas categorias oficiais coletadas do portal da CVM:

1. **Norma Vinculante / Regulamentar**
   * **Resolução CVM** (`resolucoes` — 292 arquivos no espelho bruto; 253 limpos em `data_lake/processed/`): principal ato normativo vigente pós-Decreto nº 10.139/2019 (consolidação normativa).
   * **Instrução CVM** (`instrucoes` — 661 arquivos): atos normativos históricos anteriores às Resoluções (muitas revogadas ou consolidadas por Resoluções).
   * **Deliberação CVM** (`deliberacoes` — 922 arquivos): decisões do Colegiado, aprovações de pronunciamentos contábeis (CPC) e atos específicos.
2. **Ato Orientador / Interpretativo**
   * **Ofício Circular** (`oficios-circulares` — 600 arquivos): orientações anuais ou temáticas das áreas técnicas (SEP, SIN, SSE, SMI, SNC, SRE) sobre procedimentos e prazos.
   * **Parecer de Orientação** (`pareceres-orientacao` — 87 arquivos): interpretação oficial da CVM sobre dispositivos legais e regulamentares.
   * **Nota Explicativa** (`notas-explicativas` — 83 arquivos): justificativa técnica e contextualização de normas editadas.
3. **Ato Administrativo / Consulta**
   * **Portaria** (`portarias` — 69 arquivos): atos administrativos e delegações internas.
   * **Audiência Pública / Consulta** (`audiencias-publicas` — 12 arquivos): minutas normativas submetidas a comentários do mercado.
   * **Documentos Institucionais `gov.br`** (`gov-br` — 5 arquivos): páginas temáticas de Revisão e Consolidação, Custo de Observância e Sandbox Regulatório.

### Ciclo de Vida da Norma (`StatusNorma`)
* `Vigente`: norma em pleno vigor.
* `Alterada`: norma vigente que sofreu modificação pontual por norma posterior.
* `Revogada`: norma expressamente revogada por outra Resolução ou Instrução.
* `Consolidada`: norma incorporada a um novo marco regulatório.

---

## 3. Taxonomia de Participantes Regulados (`Participante`)

Padronização dos sujeitos encontrados nas 253 Resoluções (normalizando variações de maiúsculas/minúsculas e sinônimos):

| Categoria Canônica | Subtipos / Exemplos | Sinônimos a Normalizar |
|---|---|---|
| **Emissor / Companhia Aberta** | Companhia aberta, Companhia de menor porte, Emissor de valores mobiliários | `companhias abertas`, `Empresas de capital aberto`, `Empresas listadas na B3` |
| **Companhia Securitizadora** | Securitizadora de créditos imobiliários/agronegócio/financeiros | `Securitizadoras` |
| **Fundo de Investimento** | FIF, FII, FIDC, FIP, FIA, Fundo de Índice (ETF) | `Fundos de investimento`, `Clubes de Investimento` |
| **Administrador e Gestor** | Administrador fiduciário, Gestor de recursos, Administrador de carteira | `Administradores de carteiras de valores mobiliários` |
| **Intermediário e Distribuidor** | Corretora, DTVM, Banco de investimento, Agente autônomo / Assessor de investimento | `Intermediários`, `Assessores de Investimento` |
| **Infraestrutura de Mercado** | Bolsa de valores, Mercado de balcão organizado, Depositária central, Câmara de compensação | `Mercados Organizados`, `Entidades administradoras` |
| **Prestador de Serviço Regulado** | Auditor independente, Agência de classificação de risco de crédito, Consultor de valores mobiliários, Escriturador, Custodiante | `Agências de rating`, `Auditores` |
| **Público Geral / Regulador** | Investidores, Colegiado da CVM, Áreas técnicas da CVM | `Participantes do mercado de valores mobiliários` |

---

## 4. Taxonomia de Temas Regulatórios (`TemaCVM`)

Baseada nas etiquetas oficiais presentes no índice das Resoluções (`_indice_assuntos.json`):

* **Normas Contábeis e Auditoria** (98 ocorrências — maior volume das Resoluções, incluindo aprovações de CPCs)
* **Companhias e Governança** (`Companhia`, `Companhias Securitizadoras`)
* **Ofertas Públicas** (`Ofertas Publicas`)
* **Fundos e Gestão de Recursos** (`Fundos de Investimento`, `Administradores de Carteiras`, `Clubes de Investimento`)
* **Mercados e Infraestrutura** (`Mercados Organizados`, `Infraestrutura do Mercado`, `Intermediários`, `Assessores de Investimento`)
* **Processo Sancionador e Taxas** (`Ritos Processuais`, `Ritos CVM`, `Taxas/Débitos/Restituições`)
* **Cadastro e Agentes Auxiliares** (`Cadastro de Participantes Regulados`, `Agências de Classificação de Risco de Crédito`)
* **Sem Classificação Prévia** (`(Sem Tag)` — 78 Resoluções que exigem classificação automática por NLP/LLM)

---

## 5. Taxonomia de Obrigações, Prazos e Penalidades

Das 253 Resoluções analisadas, **34 normas** foram sinalizadas com presença explícita de prazo ou penalidade/multa (`tem_prazo_ou_multa: true`). Para modelar essas regras com precisão:

### A. Tipo de Obrigação (`TipoObrigacao`)
* `Registro / Autorização`: obtenção ou manutenção de registro na CVM.
* `Informação Periódica`: envio de DFP, ITR, Formulário de Referência, informes mensais/trimestrais.
* `Informação Eventual`: divulgação de Fato Relevante, comunicados ao mercado, alterações cadastrais.
* `Governança / Conduta`: regras de atuação, segregação de funções, controles internos, limites de exposição.
* `Recolhimento de Taxa`: pagamento de Taxa de Fiscalização.

### B. Natureza do Prazo (`TipoPrazo`)
* `Recorrente / Periódico`: mensal, trimestral, anual (ex.: até X dias após o encerramento do exercício).
* `Pontual / Eventual`: dias úteis ou corridos após ocorrência de evento.
* `Excepcional / Prorrogação`: extensão temporária de prazos (ex.: calamidade climática no RS).

### C. Tipo de Penalidade (`TipoPenalidade`)
* `Multa Cominatória`: multa diária automática pelo atraso na entrega de informações periódicas ou eventuais.
* `Multa Pecuniária (PAS)`: penalidade financeira aplicada em Processo Administrativo Sancionador.
* `Advertência`: sanção formal sem multa pecuniária.
* `Suspensão ou Cancelamento de Registro`: impedimento temporário ou definitivo de atuação.
* `Inabilitação Temporária`: proibição de exercer cargos de administração em companhias abertas ou entidades reguladas.

---

## 6. Modelo Ontológico (Entidades e Relacionamentos)

Nas ementas das 253 Resoluções, os verbos estruturais dominantes observados foram: **`aprova`** (75), **`altera`** (73), **`dispõe`** (67) e **`revoga`** (60). Isso define diretamente as arestas do grafo normativo:

```text
                    +-------------------------------+
                    |  NORMA (Resolução, Instrução, |
                    |  Deliberação, Ofício, etc.)   |
                    +---------------+---------------+
                       |   ^   |    |    |    |
  altera / revoga -----+---+   |    |    |    +----- emitida / fiscalizada por
  ou aprova                    |    |    |           +----------------------+
                               |    |    |           | ORGAO / AREA TECNICA |
                               |    |    |           +----------------------+
                               |    |    |
          +--------------------+    |    +--------------------+
          | aplica_se_a             | pertence_a              | estabelece
          v                         v                         v
+-------------------+      +-----------------+      +--------------------+
|   PARTICIPANTE    |      |    TEMA CVM     |      | OBRIGACAO / REGRA  |
|     REGULADO      |      +-----------------+      +---------+----------+
+-------------------+                                    |          |
                                            possui_prazo |          | sujeita_a
                                                         v          v
                                            +----------------+  +------------------+
                                            |     PRAZO /    |  |   PENALIDADE /   |
                                            | PERIODICIDADE  |  |      SANCAO      |
                                            +----------------+  +------------------+
```

### Dicionário de Relacionamentos
* `altera(Norma_Nova, Norma_Alvo)`: modificação parcial de artigos ou anexos.
* `revoga(Norma_Nova, Norma_Alvo)`: retirada total ou parcial de vigência.
* `aprova(Norma, Documento_Tecnico)`: ex.: aprovação de Pronunciamento Técnico CPC.
* `aplica_se_a(Norma, Participante)`: define quem deve cumprir a norma.
* `estabelece(Norma, Obrigacao)`: cria dever regulatório ou vedação.
* `possui_prazo(Obrigacao, Prazo)`: vincula janela temporal de cumprimento.
* `sujeita_a(Obrigacao, Penalidade)`: define sanção por descumprimento.

---

## 7. Contrato Estruturado Alvo para NLP/LLM (Schema de Extração)

Para as próximas etapas de extração automatizada (evoluindo o schema simples da S02), cada norma processada deverá gerar uma estrutura compatível com o seguinte contrato JSON:

```json
{
  "norma": {
    "identificador": "Resolução CVM nº 80",
    "tipo": "Resolução CVM",
    "numero": 80,
    "data_publicacao": "2022-03-29",
    "status": "Vigente"
  },
  "tema_canonico": "Companhias e Governança",
  "participantes_alvo": [
    "Emissor / Companhia Aberta"
  ],
  "relacoes_normativas": [
    {
      "tipo": "revoga",
      "alvo": "Instrução CVM nº 480"
    }
  ],
  "obrigacoes": [
    {
      "tipo": "Informação Periódica",
      "descricao": "Prestação de informações periódicas e eventuais de emissores admitidos à negociação.",
      "prazo": "Conforme calendário periódico/eventual da norma",
      "penalidade_associada": "Multa Cominatória"
    }
  ]
}
```

---

## 8. Exemplos Reais Anotados do Acervo

1. **Resolução CVM nº 21** (`Administradores_de_Carteiras/resol021.md`)
   * **Participante:** Administrador e Gestor (`Administradores de carteiras de valores mobiliários`).
   * **Tema:** Fundos e Gestão de Recursos.
   * **Obrigação:** Regras de exercício profissional de administração de carteiras.
   * **Prazo/Multa explícito na ficha:** Não (`false`).

2. **Resolução CVM nº 51** (`Cadastro_de_Participantes_Regulados/resol051.md`)
   * **Participante:** Todos os participantes regulados sujeitos a cadastro na CVM.
   * **Relação Normativa:** `revoga` → `Instrução CVM nº 510, de 5 de dezembro de 2011`.
   * **Obrigação:** Registro e atualização cadastral (`Registro / Autorização`).
   * **Prazo/Multa:** Sim (`true` — possui prazos de atualização cadastral e cominação de multa).

3. **Resolução CVM nº 80** (`Companhia/resol080.md`)
   * **Participante:** Emissor / Companhia Aberta (`Emissores de valores mobiliários`).
   * **Obrigação:** Envio de informações periódicas e eventuais (`Informação Periódica`, `Informação Eventual`).
   * **Prazo/Multa:** Sim (`true`).

4. **Resolução CVM nº 202** (`Companhia/resol202.md`)
   * **Participante:** Emissor / Companhia Aberta (recorte geográfico: sede ou domicílio no Estado do Rio Grande do Sul).
   * **Obrigação:** Entrega de informações regulatórias.
   * **Prazo:** `Excepcional / Prorrogação` (prorrogação de prazos por calamidade climática).
