-- 1. Ativa as extensões necessárias no PostgreSQL
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Wrapper IMMUTABLE para permitir uso de unaccent em coluna GENERATED STORED
CREATE OR REPLACE FUNCTION f_unaccent(text)
RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT AS
$$ SELECT public.unaccent('public.unaccent', $1) $$;

-- 2. Tabela principal de Documentos Normativos
CREATE TABLE IF NOT EXISTS documentos_regulatorios (
    id SERIAL PRIMARY KEY,
    orgao VARCHAR(10) NOT NULL,
    tipo_norma VARCHAR(50) NOT NULL,
    numero_norma VARCHAR(50) NOT NULL,
    status_vigencia VARCHAR(20) DEFAULT 'VIGENTE',
    hash_sha256 VARCHAR(64) UNIQUE NOT NULL,
    caminho_arquivo TEXT NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabela de Chunks / Fragmentos com suporte a Vetor e Busca Lexical
CREATE TABLE IF NOT EXISTS chunks_regulatorios (
    id SERIAL PRIMARY KEY,
    documento_id INT REFERENCES documentos_regulatorios(id) ON DELETE CASCADE,
    hierarquia_normativa TEXT,
    texto_chunk TEXT NOT NULL,
    tsv_lexical tsvector GENERATED ALWAYS AS (to_tsvector('portuguese', f_unaccent(texto_chunk))) STORED,
    embedding vector(1024)
);

-- 4. Índice HNSW para Busca Vetorial ultrarrápida
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
ON chunks_regulatorios USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 5. Índice GIN para Busca Lexical exata
CREATE INDEX IF NOT EXISTS idx_chunks_tsv_gin
ON chunks_regulatorios USING gin (tsv_lexical);
