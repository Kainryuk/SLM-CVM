# Portarias CVM/PTE — espelho textual

Espelho self-contained de **65** portarias cvm/pte da CVM. Cada `.md` carrega o **texto integral dos PDFs** embutido (sem depender do site), organizado por **tag** em subpastas. Os binários originais ficam em `anexos/`.

## Estrutura

```
portarias/
├── INDE.md            # catálogo completo (todos os 65 docs, por tag+data)
├── RELATORIO.md       # estatísticas e falhas deste espelho
├── README.md          # este arquivo
├── (Sem Tag)/         # tag → .md + _indice.md local
│    └── _indice.md
└── anexos/<id>/       # binários originais (PDF/DOCX/XLSX)
```

## Como ler

1. Comece em [`INDE.md`](INDE.md) — tabela de todos os docs, ordenada por data, com link pra pasta da tag.
2. Cada pasta de tag tem um `_indice.md` local (só os docs daquela tag).
3. Cada `.md` de norma traz: metadados → lista de anexos → **texto completo por parte** → referências/situação normativa.
4. Links `../anexos/<id>/…` apontam pra binário local (autocontido, funciona offline).

## Reproduzir / atualizar

```bash
python C:\\Users\\aborr\\cvm_mirror\\_work\\cvm_multi.py --cat portarias --workers 4   # re-crawlea só o que faltou
python C:\\Users\\aborr\\cvm_mirror\\_work\\cvm_multi.py --cat portarias --org            # reorganiza por tag
python C:\\Users\\aborr\\cvm_mirror\\_work\\cvm_report.py                        # regenera estes índices
```

Método completo: veja [`INSTRUCAO.md`](../INSTRUCAO.md).
