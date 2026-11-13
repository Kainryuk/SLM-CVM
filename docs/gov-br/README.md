# gov.br CVM — espelho (3 páginas)

Três páginas temáticas do site novinho da CVM (Drupal), cada uma vira um `.md` autocontido com o texto principal, as subpáginas (1 nível) e os documentos linkados com PDFs embutidos.

## Páginas

- **Revisão e Consolidação de Normas** — [`revisao-e-consolidacao.md`](revisao-e-consolidacao.md)
- **Custo de Observância Regulatória** — [`custo-de-observancia.md`](custo-de-observancia.md)
- **Sandbox Regulatório** — [`sandbox-regulatorio.md`](sandbox-regulatorio.md)

## Estrutura

```
gov-br/
├── INDE.md                    # índice das 3 páginas
├── README.md                  # este arquivo
├── revisao-e-consolidacao.md
├── custo-de-observancia.md
├── sandbox-regulatorio.md
└── anexos/<slug>/           # docs baixados (PDFs/XLSX) + redações via espelho local
```

## Como funciona

- O spider (`_work/cvm_govbr.py`) baixa a página + subpáginas (mesmo prefixo de caminho, sem extensão).
- Baixa todo `.pdf/.docx/.doc/.xlsx` linkado para `anexos/<slug>/` e **embute o texto do PDF**.
- Documentos normativos que dão 404 no gov.br (ex. `instNNNconsolid.pdf`) são **resolvidos contra o espelho local** `instrucoes/`+`deliberacoes/` (`_work/cvm_govbr_fix.py`) e o binário é copiado + texto embutido.

## Reproduzir / atualizar

```bash
python C:\\Users\\aborr\\cvm_mirror\\_work\\cvm_govbr.py --which all      # re-espelha as 3 páginas
python C:\\Users\\aborr\\cvm_mirror\\_work\\cvm_govbr_fix.py                  # resolve docs normativos contra o espelho local
```

Método completo: veja [`INSTRUCAO.md`](../INSTRUCAO.md).