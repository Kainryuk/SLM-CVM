"""
UC01 Sem02 — Kelvin (Trilha B: IA & Ontologia) — CVM
Lê 5 normas reais da CVM, extrai metadados estruturados via Ollama + Pydantic
e salva o resultado em data_lake/processed/amostra_enriquecida.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import ollama

try:
    from src.schemas_regulatorios import MetadadosExtraidosNorma
except ModuleNotFoundError:
    from schemas_regulatorios import MetadadosExtraidosNorma

PROCESSED_DIR = Path("data_lake/processed")
SAIDA_AMOSTRA = PROCESSED_DIR / "amostra_enriquecida.json"


def listar_normas_piloto(limite: int = 5) -> list[Path]:
    """Seleciona até `limite` arquivos .md de normas reais da CVM."""
    arquivos = [
        p
        for p in sorted(PROCESSED_DIR.rglob("*.md"))
        if p.name != "_indice.md"
    ]
    return arquivos[:limite]


def extrair_metadados(trecho: str, modelo: str = "qwen2.5:3b") -> MetadadosExtraidosNorma:
    """Envia o trecho para o SLM no Ollama e valida a saída com Pydantic."""
    prompt = (
        "Extraia os metadados regulatórios desta norma da CVM seguindo o schema JSON. "
        "Use orgao='CVM'.\n\n"
        f"{trecho}"
    )
    resposta = ollama.chat(
        model=modelo,
        messages=[{"role": "user", "content": prompt}],
        format=MetadadosExtraidosNorma.model_json_schema(),
        options={"num_gpu": 16, "num_thread": 4},
    )
    msg = resposta["message"] if isinstance(resposta, dict) else resposta.message
    conteudo = msg["content"] if isinstance(msg, dict) else msg.content
    dados = json.loads(conteudo.strip())
    return MetadadosExtraidosNorma(**dados)


def executar_lote_piloto(modelo: str = "qwen2.5:3b", limite: int = 5) -> list[dict]:
    """Processa o lote piloto de normas CVM e salva a amostra enriquecida."""
    normas = listar_normas_piloto(limite=limite)
    if not normas:
        raise FileNotFoundError(f"Nenhuma norma .md encontrada em {PROCESSED_DIR}")

    resultados: list[dict] = []
    for caminho in normas:
        trecho = caminho.read_text(encoding="utf-8", errors="ignore")[:3000]
        print(f"[SLM] Extraindo metadados de: {caminho}")
        metadados = extrair_metadados(trecho, modelo=modelo)
        item = metadados.model_dump(mode="json")
        item["arquivo_origem"] = str(caminho).replace("\\", "/")
        resultados.append(item)

    SAIDA_AMOSTRA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_AMOSTRA.write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] {len(resultados)} extrações salvas em: {SAIDA_AMOSTRA}")
    return resultados


def main() -> int:
    ap = argparse.ArgumentParser(description="Extração de lote piloto CVM (Sem02)")
    ap.add_argument("--modelo", default="qwen2.5:3b", help="Modelo Ollama (padrão: qwen2.5:3b)")
    ap.add_argument("--limite", type=int, default=5, help="Quantidade de normas (padrão: 5)")
    args = ap.parse_args()

    try:
        executar_lote_piloto(modelo=args.modelo, limite=args.limite)
    except (OSError, ConnectionError, json.JSONDecodeError, ValueError, ollama.ResponseError) as exc:
        print(f"[ERRO] Falha ao executar lote piloto: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
