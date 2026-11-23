"""
UC01 Sem03 — Kelvin (Trilha B: IA & Worker) — CVM
Worker de enriquecimento em lote via Ollama + Pydantic com persistência no PostgreSQL.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import ollama
import psycopg2

try:
    from src.schemas_regulatorios import MetadadosExtraidosNorma
except ModuleNotFoundError:
    from schemas_regulatorios import MetadadosExtraidosNorma

PROCESSED_DIR = Path("data_lake/processed")
OUTPUT_JSON = PROCESSED_DIR / "lote_processado_sem03.json"


def calcular_sha256(caminho: Path) -> str:
    """Calcula o hash SHA-256 do arquivo para garantir idempotência no banco."""
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def listar_normas_cvm(limite: int = 5) -> list[Path]:
    """Lista arquivos .md de normas da CVM em data_lake/processed."""
    return [
        p
        for p in sorted(PROCESSED_DIR.rglob("*.md"))
        if p.name != "_indice.md"
    ][:limite]


def extrair_metadados_norma(
    trecho: str,
    modelo: str = "qwen2.5:3b",
) -> MetadadosExtraidosNorma:
    """Extrai metadados estruturados via Ollama validados com Pydantic v2."""
    prompt = (
        "Extraia os metadados regulatórios desta norma da CVM seguindo o schema JSON. "
        "Use orgao='CVM'.\n\n"
        f"{trecho}"
    )
    resposta = ollama.chat(
        model=modelo,
        messages=[{"role": "user", "content": prompt}],
        format=MetadadosExtraidosNorma.model_json_schema(),
        options={
            "num_gpu": 16,
            "num_thread": 4,
            "num_ctx": 2048,
            "num_predict": 800,
        },
    )
    msg = resposta["message"] if isinstance(resposta, dict) else resposta.message
    conteudo = msg["content"] if isinstance(msg, dict) else msg.content
    dados = json.loads(conteudo.strip())
    return MetadadosExtraidosNorma(**dados)


def conectar_postgres():
    """Abre conexão com o PostgreSQL + pgvector configurado no docker-compose.yml."""
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        dbname=os.getenv("PGDATABASE", "regulatory_db"),
        user=os.getenv("PGUSER", "rag_admin"),
        password=os.getenv("PGPASSWORD", "rag_password"),
    )


def persistir_documento(
    conn,
    norma: MetadadosExtraidosNorma,
    hash_sha256: str,
    caminho_arquivo: str,
) -> int | None:
    """Insere o documento na tabela documentos_regulatorios de forma idempotente."""
    sql = """
        INSERT INTO documentos_regulatorios (
            orgao, tipo_norma, numero_norma, status_vigencia, hash_sha256, caminho_arquivo
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (hash_sha256) DO NOTHING
        RETURNING id;
    """
    with conn.cursor() as cur:
        cur.execute(
            sql,
            (
                norma.orgao[:10],
                norma.tipo_norma.value,
                norma.tipo_e_numero[:50],
                norma.status_vigencia.value,
                hash_sha256,
                caminho_arquivo,
            ),
        )
        row = cur.fetchone()
    conn.commit()
    return row[0] if row else None


def processar_lote_documentos(
    modelo: str = "qwen2.5:3b",
    limite: int = 5,
    salvar_no_banco: bool = True,
) -> list[dict]:
    """Processa normas da CVM via Ollama, salva JSON e persiste no PostgreSQL."""
    arquivos = listar_normas_cvm(limite=limite)
    if not arquivos:
        raise FileNotFoundError(f"Nenhuma norma .md encontrada em {PROCESSED_DIR}")

    conn = conectar_postgres() if salvar_no_banco else None
    resultados: list[dict] = []
    try:
        for arquivo in arquivos:
            trecho = arquivo.read_text(encoding="utf-8", errors="ignore")[:1200]
            file_hash = calcular_sha256(arquivo)
            caminho_rel = str(arquivo).replace("\\", "/")
            print(f"[WORKER] Processando {caminho_rel}...")

            norma = extrair_metadados_norma(trecho, modelo=modelo)
            doc_id = None
            if conn is not None:
                doc_id = persistir_documento(conn, norma, file_hash, caminho_rel)

            item = norma.model_dump(mode="json")
            item["hash_sha256"] = file_hash
            item["caminho_arquivo"] = caminho_rel
            item["documento_id"] = doc_id
            resultados.append(item)
    finally:
        if conn is not None:
            conn.close()

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[SUCESSO] {len(resultados)} documentos processados e salvos em: {OUTPUT_JSON}")
    return resultados


def main() -> int:
    ap = argparse.ArgumentParser(description="Worker de enriquecimento CVM (Sem03)")
    ap.add_argument("--modelo", default="qwen2.5:3b", help="Modelo Ollama (padrão: qwen2.5:3b)")
    ap.add_argument("--limite", type=int, default=5, help="Quantidade de normas (padrão: 5)")
    ap.add_argument("--sem-banco", action="store_true", help="Não grava no PostgreSQL")
    args = ap.parse_args()

    try:
        processar_lote_documentos(
            modelo=args.modelo,
            limite=args.limite,
            salvar_no_banco=not args.sem_banco,
        )
    except (
        OSError,
        ConnectionError,
        json.JSONDecodeError,
        ValueError,
        ollama.ResponseError,
        psycopg2.Error,
    ) as exc:
        print(f"[ERRO] Falha no worker Sem03: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
