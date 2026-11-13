"""
UC01 Trilha B — Organizar o acervo docs/resolucoes/ para o SLM.

Lê cada norma .md bruta (cabeçalho de espelho + metadados + texto completo) e
escreve em data_lake/processed/ uma versão LIMPA e legível pelo modelo:

    - bloco curto de metadados (órgão, norma, data, tag, assunto/ementa)
    - apenas o TEXTO NORMATIVO, sem ruído:
        * linhas "Fonte/Espelhado em/Status no site"
        * seção "Documentos / Anexos" (aponta PDFs/docs, inútil ao assunto)
        * marcações <sub>Fonte: ...</sub>
        * rodapé "_Espelho textual gerado automaticamente..._"
        * bloco de assinatura (Assinado eletronicamente / nome / cargo)

Emissão:
    data_lake/processed/<tag>/<norma>.md      (limpo, 1 arquivo por norma)
    data_lake/processed/_indice_assuntos.json (índice para RAG: norma, tag, assunto, arquivo)

Uso:
    .venv/Scripts/python.exe src/organizar_resolucoes.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACERVO = ROOT / "docs" / "resolucoes"
SAIDA = ROOT / "data_lake" / "processed"

# regexes para puxar os campos do cabeçalho "## Metadados"
RE_EMENTA = re.compile(r"\*\*Epígrafe\s*/\s*Ementa:\*\*\s*(.+)")
RE_DATA = re.compile(r"\*\*Data \(sistema do site\):\*\*\s*(.+)")
RE_TAG = re.compile(r"\*\*Tag\(s\):\*\*\s*(.+)")
RE_TITULO = re.compile(r"^#\s*(.+)$", re.M)

# ruído a remover do corpo
RE_SUB_FONTE = re.compile(r"<sub>Fonte:.*?</sub>", re.I)
FOOTER = "_Espelho textual gerado automaticamente"
ASSINA = "Assinado eletronicamente"


def _data_bruta(m: re.Match | None, texto: str) -> str:
    """Converte '18 DE NOVEMBRO DE 2020' (no título) em 18/11/2020; senão usa Data do site."""
    if m:
        return m.group(1).strip()
    md = re.search(r"\*\*Data \(sistema do site\):\*\*\s*(.+)", texto)
    return md.group(1).strip() if md else ""


def _data_norma(texto: str) -> str:
    m = re.search(r"DE\s+(\d{1,2})\s+(DE\s+)?([A-Z]{3,9})\s+DE\s+(\d{4})", texto)
    if m:
        g = m.group(3).upper()
        mes_map = {
            "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4, "MAI": 5, "JUN": 6,
            "JUL": 7, "AGO": 8, "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12,
            "JANEIRO": 1, "FEVEREIRO": 2, "MARCO": 3, "MARÇO": 3, "ABRIL": 4,
            "MAIO": 5, "JUNHO": 6, "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9,
            "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12,
        }
        mes = mes_map.get(g, 1)
        return f"{m.group(1)}/{mes:02d}/{m.group(4)}"
    return _data_bruta(None, texto)


def _numerar_norma(titulo: str) -> str:
    """'Resolução CVM 12' -> 'Resolução CVM nº 12'."""
    m = re.search(r"(Resolução|Instrução|Deliberação|Portaria|Parecer)\s+CVM\s+(\d+)", titulo)
    if m:
        return f"{m.group(1)} CVM nº {m.group(2)}"
    return titulo


def limpar_arquivo(src: Path) -> dict | None:
    texto = src.read_text(encoding="utf-8")

    # corte: do "## Texto completo" até antes do rodapé de assinatura/espelho
    m = re.search(r"##\s*Texto completo.*?\n", texto, re.M)
    corpo = texto[m.end():] if m else texto

    # remove a marcação de sub-fonte do PDF
    corpo = RE_SUB_FONTE.sub("", corpo)

    # corta no rodapé de espelho ou no bloco de assinatura (o que vier antes)
    idx = len(corpo)
    for marcador in (FOOTER, ASSINA, "\n## Referências", "\n---\n"):
        pos = corpo.find(marcador)
        if pos != -1 and pos < idx:
            idx = pos
    corpo = corpo[:idx].strip()

    if not corpo:
        return None

    # limpeza de branco no corpo
    corpo = re.sub(r"\n{3,}", "\n\n", corpo).strip()

    # campos do cabeçalho
    titulo_m = RE_TITULO.search(texto)
    titulo = titulo_m.group(1).strip() if titulo_m else src.stem
    ementa_m = RE_EMENTA.search(texto)
    ementa = ementa_m.group(1).strip() if ementa_m else ""
    tag_m = RE_TAG.search(texto)
    tag = tag_m.group(1).strip() if tag_m else src.parent.name
    tag_limpo = (tag or src.parent.name).replace("(", "").replace(")", "").strip() or "sem_tag"
    # Pasta de saída = subpasta de origem do acervo (única; evita colisão entre
    # normas com tags múltiplas que compartilham número, ex. resol202 em duas pastas).
    # A tag (pode ser múltipla, separada por vírgula) fica só no cabeçalho.
    folder = re.sub(r"\s+", "_", src.parent.name).replace("(", "").replace(")", "").strip() or "sem_tag"
    reg_out = SAIDA / folder / f"{src.stem}.md"
    reg_out.parent.mkdir(parents=True, exist_ok=True)

    reg = {
        "orgao": "CVM",
        "norma": _numerar_norma(titulo),
        "data": _data_norma(texto),
        "tag": tag,
        "assunto": ementa,
    }

    doc = (
        f"# {reg['norma']} — {reg['tag']}\n"
        f"- Órgão: {reg['orgao']}\n"
        f"- Norma: {reg['norma']}\n"
        f"- Data: {reg['data']}\n"
        f"- Categoria (tag): {reg['tag']}\n"
        f"- Assunto (ementa): {reg['assunto'] if reg['assunto'] else '(ementa não localizada; ver texto)'}\n"
        f"\n--- TEXTO NORMATIVO ---\n\n{corpo}\n"
    )

    reg_out.write_text(doc, encoding="utf-8")
    reg["arquivo_limpo"] = f"processed/{folder}/{src.stem}.md"
    return reg


def main() -> int:
    if not ACERVO.exists():
        print(f"[erro] acervo não encontrado: {ACERVO}")
        return 2

    arquivos = sorted(ACERVO.rglob("resol*.md"))
    arquivos = [a for a in arquivos if "anexos" not in a.parts and a.name != "_indice.md"]
    print(f"[organizar] {len(arquivos)} norma(s) sob {ACERVO.relative_to(ROOT)}/")

    indice, erros = [], []
    for f in arquivos:
        reg = limpar_arquivo(f)
        if reg:
            indice.append(reg)
        else:
            erros.append(str(f.relative_to(ACERVO)))
    indice.sort(key=lambda r: (r["norma"], r["tag"]))

    (SAIDA / "_indice_assuntos.json").write_text(
        json.dumps(indice, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[ok] {len(indice)} norma(s) limpa(s) -> {SAIDA.relative_to(ROOT)}/")
    print(f"[ok] índice de assuntos -> {SAIDA.relative_to(ROOT)}/_indice_assuntos.json")
    if erros:
        print(f"[aviso] {len(erros)} sem corpo: {erros[:5]}")
    # amostra
    if indice:
        a = indice[0]
        print(f"[amostra] {a['norma']} | {a['assunto'][:60]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
