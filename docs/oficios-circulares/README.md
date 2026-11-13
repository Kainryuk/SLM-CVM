# Ofícios Circulares CVM — espelho textual

Espelho self-contained de **598** ofícios circulares cvm da CVM. Cada `.md` carrega o **texto integral dos PDFs** embutido (sem depender do site), organizado por **tag** em subpastas. Os binários originais ficam em `anexos/`.

## Estrutura

```
oficios-circulares/
├── INDE.md            # catálogo completo (todos os 598 docs, por tag+data)
├── RELATORIO.md       # estatísticas e falhas deste espelho
├── README.md          # este arquivo
├── (Sem Tag)/         # tag → .md + _indice.md local
├── Administrador de Carteira - Administradores de Carteiras - Corretora - Fundo de Investimento - Fundos de Investimento - Fundos de Investimento em Participações - Intermediários - Ofício Circular/         # tag → .md + _indice.md local
├── Administradores de Carteiras - Auditor Independente - Fundos de Investimento - Normas Contabeis/         # tag → .md + _indice.md local
├── Administradores de Carteiras - Cadastro de Participantes Regulados - Ofício Circular/         # tag → .md + _indice.md local
├── Administradores de Carteiras - Consultores de Valores Mobiliarios - Fundos de Investimento em Direitos Creditórios - Ofício Circular - Taxas-Débitos-Restituições/         # tag → .md + _indice.md local
├── Administradores de Carteiras - Fundos de Investimento/         # tag → .md + _indice.md local
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
python C:\\Users\\aborr\\cvm_mirror\\_work\\cvm_multi.py --cat oficios-circulares --workers 4   # re-crawlea só o que faltou
python C:\\Users\\aborr\\cvm_mirror\\_work\\cvm_multi.py --cat oficios-circulares --org            # reorganiza por tag
python C:\\Users\\aborr\\cvm_mirror\\_work\\cvm_report.py                        # regenera estes índices
```

Método completo: veja [`INSTRUCAO.md`](../INSTRUCAO.md).
