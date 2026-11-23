import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.schemas_regulatorios import MetadadosExtraidosNorma, StatusVigencia, TipoNormaCVM
from src.worker_enrichment import (
    calcular_sha256,
    extrair_metadados_norma,
    persistir_documento,
)


def test_init_sql_possui_indices_hnsw_e_gin():
    sql = Path("db/init.sql").read_text(encoding="utf-8")
    assert "CREATE EXTENSION IF NOT EXISTS vector" in sql
    assert "CREATE EXTENSION IF NOT EXISTS unaccent" in sql
    assert "tsv_lexical tsvector" in sql
    assert "idx_chunks_embedding_hnsw" in sql
    assert "idx_chunks_tsv_gin" in sql


def test_calcular_sha256(tmp_path):
    arquivo = tmp_path / "norma.md"
    arquivo.write_text("Resolução CVM", encoding="utf-8")
    digest = calcular_sha256(arquivo)
    assert len(digest) == 64
    assert digest == calcular_sha256(arquivo)


def test_extrair_metadados_norma_mock_ollama():
    payload = {
        "orgao": "CVM",
        "tipo_norma": "Resolucao_CVM",
        "tipo_e_numero": "Resolução CVM 21/2021",
        "status_vigencia": "VIGENTE",
        "entidades_citadas": ["Administradores de Carteiras"],
        "normas_revogadas_ou_alteradas": ["Instrução CVM 558/2015"],
        "resumo_tecnico": "Dispõe sobre a administração profissional de carteiras.",
    }
    mock_resp = {"message": {"content": json.dumps(payload)}}
    with patch("src.worker_enrichment.ollama.chat", return_value=mock_resp):
        norma = extrair_metadados_norma("Resolução CVM nº 21...")
    assert norma.orgao == "CVM"
    assert norma.tipo_norma == TipoNormaCVM.RESOLUCAO
    assert norma.status_vigencia == StatusVigencia.VIGENTE


def test_persistir_documento_idempotente():
    norma = MetadadosExtraidosNorma(
        orgao="CVM",
        tipo_norma=TipoNormaCVM.RESOLUCAO,
        tipo_e_numero="Resolução CVM 21/2021",
        status_vigencia=StatusVigencia.VIGENTE,
        entidades_citadas=["Administradores de Carteiras"],
        normas_revogadas_ou_alteradas=[],
        resumo_tecnico="Dispõe sobre a administração profissional de carteiras.",
    )
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = (42,)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    doc_id = persistir_documento(mock_conn, norma, "a" * 64, "data_lake/processed/resol021.md")
    assert doc_id == 42
    mock_conn.commit.assert_called_once()
