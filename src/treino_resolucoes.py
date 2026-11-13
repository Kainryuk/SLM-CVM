"""
UC01 Trilha B (Kelvin / CVM) — Batch runner: treina/aplica o SLM no acervo
regulatório CVM, limitado à pasta docs/resolucoes/.

Lê cada norma .md sob docs/resolucoes/**/resol*.md, extrai a ficha normativa
rigida (FichaNormativa) via Ollama + JSON Schema + Pydantic e consolida os
resultados em JSON.

Uso:
    .venv/Scripts/python.exe src/treino_resolucoes.py --limite 5        # amostra
    .venv/Scripts/python.exe src/treino_resolucoes.py --limitar "Normas Contabeis"
    .venv/Scripts/python.exe src/treino_resolucoes.py                   # tudo
O backend Ollama pode ser nativo ou Docker; defina OLLAMA_HOST se necessário
(padrão http://127.0.0.1:11434).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import ollama
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
ACERVO = ROOT / "docs" / "resolucoes"

# Slice de prompt: mantém cabeçalho de metadados + início do texto, sem estourar o contexto
SLICE_CHARS = 6000


class FichaNormativa(BaseModel):
    orgao: str = Field(description="Sigla da agência reguladora (ex.: CVM, ANS, ANVISA)")
    numero_norma: str = Field(description="Número e ano da norma (ex.: 31/2021)")
    assunto_principal: str = Field(description="Resumo em 1 frase do que a norma disciplina")
    possui_prazo_ou_multa: bool = Field(description="True se menciona prazo, sanção ou multa")

SCHEMA = FichaNormativa.model_json_schema()


def _modelo(disponivel: list[str], preferido: str = "qwen2.5-coder:7b") -> str:
    if preferido in disponivel:
        return preferido
    # qualquer qwen2.5 com completion
    for cand in disponivel:
        if cand.startswith("qwen2.5") and cand.endswith(":7b"):
            return cand
    return preferido


def _resol(files: list[Path]) -> list[Path]:
    out = []
    for f in files:
        if f.name.startswith("_indice"):
            continue
        out.append(f)
    return out


def extraer(cliente, modelo: str, texto: str) -> dict:
    resposta = cliente.chat(
        model=modelo,
        messages=[{"role": "user", "content": f"Extraia os dados deste trecho normativo CVM:\n{texto}"}],
        format=SCHEMA,
        options={"num_predict": 400, "temperature": 0},
        keep_alive="15m",
    )
    msg = resposta["message"] if isinstance(resposta, dict) else resposta.message
    conteudo = (msg["content"] if isinstance(msg, dict) else msg.content).strip()
    dados = json.loads(conteudo)
    return FichaNormativa(**dados).model_dump()


def main() -> int:
    ap = argparse.ArgumentParser(description="Treina/aplica o SLM no acervo docs/resolucoes/")
    ap.add_argument("--limite", type=int, default=0, help="processar apenas N arquivos (0 = todos)")
    ap.add_argument("--limitar", default=None, help="restreinar a uma subpasta do acervo (ex.: 'Normas Contabeis')")
    ap.add_argument("--host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    ap.add_argument("--out", default=str(ROOT / "tests" / "treino_resolucoes_evidencia.json"))
    args = ap.parse_args()

    if not ACERVO.exists():
        print(f"[erro] acervo não encontrado: {ACERVO}", file=sys.stderr)
        return 2

    # descobre modelo instalado (tolerante à shape do client 0.6.x + fallback REST)
    probe = ollama.Client(host=args.host)
    modelos: list[str] = []
    try:
        for item in probe.list():
            if isinstance(item, tuple):
                modelos.append(str(item[0]))
            elif hasattr(item, "name"):
                modelos.append(item.name)
    except Exception:
        pass
    if not modelos:
        import urllib.request
        with urllib.request.urlopen(args.host + "/api/tags", timeout=20) as r:
            modelos = [m["name"] for m in json.loads(r.read().decode()).get("models", [])]
    modelo = _modelo(modelos)
    print(f"[backend] {args.host} | modelo: {modelo} | acervo: {ACERVO.name}/")

    arquivos = _resol(sorted(ACERVO.rglob("resol*.md")))
    if args.limitar:
        arquivos = [a for a in arquivos if a.parent.name == args.limitar]
        print(f"[escopo] subpasta: {args.limitar} -> {len(arquivos)} arquivos")
    if args.limite:
        arquivos = arquivos[: args.limite]

    print(f"[batch] processando {len(arquivos)} norma(s)...")

    resultados, erros = [], []
    t0 = time.time()
    for i, f in enumerate(arquivos, 1):
        rel = f.relative_to(ACERVO).as_posix()
        tag = f.parent.name
        try:
            texto = f.read_text(encoding="utf-8")[:SLICE_CHARS]
            ficha = extraer(probe, modelo, texto)
            reg = {
                "norma": f.name,
                "pasta": tag,
                "caminho": rel,
                "modelo": modelo,
                **ficha,
            }
            resultados.append(reg)
            print(f"  [{i}/{len(arquivos)}] {rel} -> {ficha['assunto_principal'][:50]}")
        except Exception as e:  # noqa: BLE001
            erros.append({"caminho": rel, "erro": f"{type(e).__name__}: {e}"})
            print(f"  [{i}/{len(arquivos)}] {rel} -> ERRO {type(e).__name__}: {e}")

    resumo = {
        "escopo": str(ACERVO.relative_to(ROOT)),
        "modelo": modelo,
        "processados": len(resultados),
        "erros": len(erros),
        "tempo_segundos": round(time.time() - t0, 1),
        "resultados": resultados,
        "falhas": erros,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[ok] {len(resultados)} ficha(s) | {len(erros)} erro(s) | {resumo['tempo_segundos']}s")
    print(f"[evidencia] {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
