# Espelho CVM — Resoluções (Markdown)
> **Instrução completa do processo (scraping, download e organização):** veja `INSTRUCAO.md` na raiz do projeto (`cvm_mirror/INSTRUCAO.md`).

> **Fonte:** https://conteudo.cvm.gov.br/legislacao/resolucoes.html
> **Gerado em:** 09/11/2026
> **Total:** 251 resoluções + 562 anexos binários (326 MB)

## Estrutura

```

├── INDE.md              # catálogo ordenado + agrupamento por tag temática
├── RELATORIO.md         # estatísticas e falhas do espelhamento
├── resol001.md … resol251.md   # um .md autocontido por resolução
└── anexos/resolNNN/     # binários baixados (PDF/DOCX/DOC/XLSX)
```

## O que cada `.md` contém

Cada arquivo é uma **copia textual visual** da página da CVM, ampliada:

1. **Metadados** — título, data, epígrafe/ementa, tags temáticas
2. **Documentos / Anexos** — lista de cada binário, com caminho local relativo
3. **Texto completo** — o texto integral extraído dos PDFs:
   - resoluções com partes separadas: índice + cada `Anexo Normativo` embutido
   - resoluções simples: o consolidado/original + justificativas (AIR) embutidos
4. **Referências / Situação normativa** — "ALTERADA pelas Resoluções …", "REVOGADA por …", audiências públicas, retificações DOU

## Nota de uso

- O texto foi extraído dos PDFs oficiais (pypdf). Verifique sempre no DOU/original
  para uso normativo (extração automática pode ter pequenos artefatos de layout).
- As pastas `anexos/` guardam os binários originais (PDF/DOCX/XLSX) como backup.
- Regenerar índices: `python _work/cvm_index.py`. Re-crawlear: `python _work/cvm_crawl.py`.
