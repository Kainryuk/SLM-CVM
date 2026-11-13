"""
UC01 Trilha B — Compreender o ASSUNTO das resoluções CVM com o SLM.

Usa os dados JÁ ORGANIZADOS em data_lake/processed/ (limpos, legíveis pelo
modelo) e força o SLM a responder SOMENTE:
    - em PORTUGUÊS
    - o ASSUNTO / objeto da norma (o que ela disciplina, a quem se aplica)
    - SEM código de programação, SEM história/cronologia
    - restrito a CVM / resoluções

O objetivo é uma "compreensão do assunto" do acervo regulatório, em linguagem
clara, pronta para uso em consulta/RAG.

Uso:
    .venv/Scripts/python.exe src/compreender_resolucoes.py --limite 5
    .venv/Scripts/python.exe src/compreender_resolucoes.py
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import ollama
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
PROCESSADO = ROOT / "data_lake" / "processed"
SLICE = 8000  # chars do documento limpo enviados ao modelo


class CompreensaoAssunto(BaseModel):
    norma: str = Field(description="Identificação da norma (ex.: Resolução CVM nº 31)")
    assunto: str = Field(
        description="Explicação em português claro (1 a 4 frases) do que a norma disciplina. "
        "Somente o assunto/objeto. Sem código. Sem história."
    )
    se_aplica_a: str = Field(description="Em português: a quem / a que situação a norma se aplica")
    tem_prazo_ou_multa: bool = Field(description="True se a norma estabelece prazo ou sanção/multa")

SCHEMA = CompreensaoAssunto.model_json_schema()

# Prompt de sistema: a trava exigida (PT-BR, só assunto, sem código, sem história, só CVM/resoluções)
SISTEMA = (
    "Você é um analista de normas da CVM (Comissão de Valores Mobiliários). "
    "Recebe um trecho de uma RESOLUÇÃO CVM já organizada e deve explicar APENAS O ASSUNTO da norma.\n"
    "Regras obrigatórias:\n"
    "1. Responda SOMENTE em português (pt-BR), linguagem clara.\n"
    "2. Descreva apenas o que a norma DISCIPLINA e a quem se aplica (o objeto).\n"
    "3. NÃO escreva código de programação.\n"
    "4. NÃO relate a história, cronologia, origens ou evolução da norma.\n"
    "5. Se o assunto envolver prazo ou multa, informe em se_aplica_a e marque tem_prazo_ou_multa.\n"
    "6. Fale somente de CVM e de resoluções. Não invente normas de outros órgãos.\n"
    "Siga exatamente o esquema de campos fornecido."
)


def _modelo(cliente, host: str, preferido: str = "qwen2.5-coder:7b") -> str:
    nomes: list[str] = []
    try:
        for it in cliente.list():
            nomes.append(str(it[0]) if isinstance(it, tuple) else (getattr(it, "name", None) or str(it)))
    except Exception:
        pass
    if not nomes:
        import urllib.request
        with urllib.request.urlopen(host + "/api/tags", timeout=20) as r:
            nomes = [m["name"] for m in json.loads(r.read().decode()).get("models", [])]
    for n in nomes:
        if n == preferido or (n.startswith("qwen2.5") and n.endswith(":7b")):
            return n
    return preferido


def compreender(cliente, modelo: str, doc: str) -> dict:
    resposta = cliente.chat(
        model=modelo,
        messages=[
            {"role": "system", "content": SISTEMA},
            {"role": "user", "content": doc[:SLICE]},
        ],
        format=SCHEMA,
        options={"num_predict": 400, "temperature": 0},
        keep_alive="15m",
    )
    msg = resposta["message"] if isinstance(resposta, dict) else resposta.message
    conteudo = (msg["content"] if isinstance(msg, dict) else msg.content).strip()
    return CompreensaoAssunto(**json.loads(conteudo)).model_dump()


def main() -> int:
    ap = argparse.ArgumentParser(description="Compreende o assunto das resoluções CVM via SLM")
    ap.add_argument("--limite", type=int, default=0, help="processar apenas N arquivos (0 = todos)")
    ap.add_argument("--limitar", default=None, help="restreinar a uma subpasta (ex.: 'Normas_Contabeis')")
    ap.add_argument("--host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    ap.add_argument("--out", default=str(ROOT / "tests" / "compreensao_resolucoes.json"))
    args = ap.parse_args()

    if not PROCESSADO.exists():
        print("[erro] rode antes: python src/organizar_resolucoes.py", file=sys.stderr)
        return 2

    arquivos = sorted(PROCESSADO.rglob("resol*.md"))
    arquivos = [a for a in arquivos if "anexos" not in a.parts]
    if args.limitar:
        arquivos = [a for a in arquivos if a.parent.name == args.limitar]
    if args.limite:
        arquivos = arquivos[: args.limite]

    cliente = ollama.Client(host=args.host)
    modelo = _modelo(cliente, args.host)
    print(f"[backend] {args.host} | modelo: {modelo} | {len(arquivos)} documento(s) organizado(s)")

    resultados, erros = [], []
    t0 = time.time()
    for i, f in enumerate(arquivos, 1):
        doc = f.read_text(encoding="utf-8")
        try:
            c = compreender(cliente, modelo, doc)
            c["caminho"] = f.relative_to(PROCESSADO).as_posix()
            resultados.append(c)
            print(f"  [{i}/{len(arquivos)}] {f.name} -> {c['assunto'][:55]}")
        except Exception as e:  # noqa: BLE001
            erros.append({"caminho": f.name, "erro": f"{type(e).__name__}: {e}"})
            print(f"  [{i}/{len(arquivos)}] {f.name} -> ERRO {type(e).__name__}")

    resumo = {
        "escopo": "CVM — resoluções (dados organizados em data_lake/processed/)",
        "linguagem": "pt-BR",
        "restricoes": ["sem código de programação", "sem história/cronologia", "apenas assunto/objeto"],
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
    print(f"\n[ok] {len(resultados)} | {len(erros)} erro(s) | {resumo['tempo_segundos']}s")
    print(f"[evidencia] {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
