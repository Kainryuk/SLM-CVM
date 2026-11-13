# Relatório — Scraping, Limpeza e Organização dos Dados da CVM para LLMs

## 1. Resultado Geral

Sim, foi possível concluir com sucesso todas as etapas de **scraping**, **limpeza** e **organização** do acervo regulatório da CVM para leitura e consumo por modelos de linguagem (LLMs).

* **Scraping do acervo:** Foram coletadas e espelhadas **2.575 normas** distribuídas nas 8 categorias do portal principal da CVM (`resolucoes`, `instrucoes`, `deliberacoes`, `notas-explicativas`, `pareceres-orientacao`, `portarias`, `oficios-circulares` e `audiencias-publicas`), além de **3 páginas** do portal `gov.br/cvm`. Não houve nenhuma falha de download no portal principal e nenhuma falha de extração de texto nos PDFs das Resoluções.
* **Limpeza dos dados:** Todos os **253 arquivos** de Resoluções foram limpos para manter apenas os metadados essenciais e o texto normativo puro, acompanhados de um índice estruturado por assunto.
* **Organização e leitura por LLM:** O modelo de linguagem local conseguiu ler e extrair informações estruturadas de **100% das 253 Resoluções** sem erros, além de incorporar em sua memória de contexto uma biblioteca compactada com **250 Resoluções** para responder sobre a CVM mesmo sem uso de banco vetorial (RAG) nesta etapa.

---

## 2. Como os Dados Foram Obtidos

Para construir a base de documentos utilizada pelo projeto, foi empregada uma ferramenta própria de espelhamento desenvolvida externamente para varrer os portais da CVM. Essa ferramenta automatizou a consulta aos catálogos internos do site, o download dos documentos originais (incluindo anexos em PDF, Word e planilhas) com controle de retomada, a extração automática do texto integral dos PDFs com remoção de cabeçalhos e rodapés repetitivos, a organização temática em pastas e a recuperação de links quebrados do portal `gov.br` por meio do cruzamento com os arquivos já coletados.

---

## 3. Como Foi Feita a Limpeza e Organização para LLMs

Os documentos brutos vindos do espelhamento preservavam fielmente a estrutura do site, mas continham elementos que prejudicam a janela de contexto e a atenção dos LLMs, como links internos de navegação, listagens de arquivos anexos e rodapés institucionais. Para viabilizar a leitura pelos modelos, o pipeline realizou três ações:

1. **Limpeza estrutural:** Remoção de ruídos de espelhamento, seções de download e rodapés, preservando exclusivamente o cabeçalho de metadados e o conteúdo normativo limpo, além da geração de um índice unificado de assuntos.
2. **Validação de leitura por LLM:** Submissão de todas as normas limpas ao modelo local para extração estruturada de assunto, público-alvo e existência de prazos ou multas, confirmando leitura válida integral sem falhas.
3. **Compactação em memória de contexto:** Redução de prefixos jurídicos repetitivos nas ementas de 250 Resoluções para caberem de forma enxuta dentro da janela de contexto do modelo especializado, permitindo consultas diretas sem RAG.

---

## 4. Dificuldades Encontradas

### Durante o Scraping
* **Catálogo oculto por carregamento dinâmico:** As páginas iniciais exibiam apenas os 10 itens mais recentes ou em destaque. Foi necessário descobrir e simular os parâmetros de consulta direta do servidor (incluindo o identificador de categoria e paginação para categorias com mais de 500 itens, como Instruções e Deliberações).
* **Dois layouts diferentes no mesmo portal:** Resoluções mais antigas listam seus anexos em formato de tabela, enquanto as mais recentes usam links soltos no corpo da página, exigindo adaptação da coleta para tratar os dois padrões.
* **Conteúdo integral preso em PDFs:** As páginas web traziam apenas resumos curtos; o texto completo das normas ficava dentro de PDFs anexos, cujos cabeçalhos e endereços institucionais repetiam em todas as páginas e precisavam ser filtrados na extração.
* **Diferenças entre portais e links quebrados:** A seção de Audiências Públicas não possui catálogo dinâmico e mantém apenas edições recentes (2025–2026), enquanto páginas do `gov.br` apresentavam links antigos com erro 404 que precisaram ser resolvidos localmente.
* **Ausência de classificação temática em parte do acervo:** O próprio portal da CVM deixa dezenas de Resoluções e a maior parte das Deliberações e Portarias sem etiqueta de assunto.

### No Armazenamento e Versionamento (Windows e Git)
* **Nomes de caminhos muito longos:** Em ofícios circulares com múltiplas etiquetas temáticas combinadas, o comprimento dos diretórios ultrapassou o limite padrão de 260 caracteres do Windows, impedindo a indexação no Git até a habilitação do suporte a caminhos longos.
* **Volume elevado de arquivos binários:** Os anexos originais somam centenas de megabytes (326 MB apenas em Resoluções), exigindo exclusão desses binários do controle de versão para manter o repositório leve.

### Na Leitura e Resposta pelos LLMs
* **Perda de atenção e truncamento em prompts extensos:** Na primeira versão embutida no modelo de 7 bilhões de parâmetros, o excesso de texto (~47 mil caracteres) combinado ao limite padrão de contexto fazia o modelo ignorar regras, confundir normas e misturar assuntos de programação. A solução exigiu compactar as ementas, corrigir cortes de texto, ampliar a janela de contexto para 16.384 tokens e reforçar as instruções no início e no fim do prompt.
* **Duplicidade de normas com múltiplas etiquetas:** Duas Resoluções com etiquetas compostas geravam colisão de nomes na etapa de organização, exigindo separação por subpastas para evitar sobrescrita.
* **Limitação de desempenho sem GPU:** Sem banco vetorial, enviar toda a biblioteca no prompt torna a execução exclusivamente em CPU e memória RAM lenta demais na primeira leitura (ultrapassando 300 segundos), exigindo ao menos aceleração híbrida em GPU até a implantação futura de RAG.
