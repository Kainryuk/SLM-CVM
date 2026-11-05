"""
UC01 Sem01 — Kelvin (Trilha B: IA & SLM) — CVM
Script de extração de metadados normativos com Ollama + Pydantic.

Requisitos:
    - Ollama rodando em Docker (ver docker-compose.yml) — passo: docker compose up -d
    - Modelo baixado: docker exec -it ollama ollama pull qwen2.5:3b
    - Dependências: pip install -r requirements.txt

Uso:
    python src/teste_extracao_slm.py
    python src/teste_extracao_slm.py --texto-arquivo path/para/trecho_cvm.txt

O texto de exemplo padrão é CVM (agência do Kelvin). Troque pelo trecho da
sua norma (Resoluções / Ofícios do portal: conteudo.cvm.gov.br/legislacao).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import ollama
from pydantic import BaseModel, Field

# 1. A "ficha" rígida que o SLM tem que preencher (JSON Schema via Pydantic)
class FichaNormativa(BaseModel):
    orgao: str = Field(description="Sigla da agência: ANS, CVM ou ANVISA")
    numero_norma: str = Field(description="Número e ano da resolução ou RDC")
    assunto_principal: str = Field(description="Resumo em 1 frase do que trata o trecho")
    possui_prazo_ou_multa: bool = Field(description="True se mencionar prazo ou penalidade")


# 2. Trecho real de uma norma — substitua por um trecho da CVM (ex.: Resolução do CMN/CVM)
TEXT_PADRAO = """
Resolução CVM nº 88, de 28 de março de 2022.
Art. 1º Esta Resolução disciplina as informações que as companhias abertas
devem divulgar aos seus acionistas e ao mercado.
Parágrafo único. O descumprimento das obrigações de divulgação sujeita a
companhia às sanções previstas no art. 18 da Lei nº 6.385/1976, aplicáveis
no prazo de 30 dias.
"""

SAIDA_EVIDENCIA = Path(__file__).resolve().parent.parent / "tests" / "evidencia_extracao.json"


def _extrair(trecho: str) -> dict:
    """Manda o trecho para o SLM e força a saída a seguir a FichaNormativa."""
    resposta = ollama.chat(
        model="qwen2.5:3b",
        messages=[
            {"role": "user", "content": f"Extraia os dados deste texto:\n{trecho}"}
        ],
        format=FichaNormativa.model_json_schema(),
    )

    # Compat com API antiga (dict) e nova (objeto com .message.content)
    msg = resposta["message"] if isinstance(resposta, dict) else resposta.message
    conteudo = msg["content"] if isinstance(msg, dict) else msg.content
    conteudo = conteudo.strip()

    # Ollama já devolve JSON quando `format` é um schema; valida de novo no Pydantic
    dados = json.loads(conteudo)
    ficha = FichaNormativa(**dados)
    return ficha.model_dump()


def main() -> int:
    ap = argparse.ArgumentParser(description="Extrai metadados normativos via Ollama+Pydantic")
    ap.add_argument("--texto-arquivo", help="Path de um .txt com o trecho normativo (CVM)")
    args = ap.parse_args()

    trecho = TEXT_PADRAO
    if args.texto_arquivo:
        p = Path(args.texto_arquivo)
        if not p.exists():
            print(f"[erro] arquivo não encontrado: {p}", file=sys.stderr)
            return 2
        trecho = p.read_text(encoding="utf-8")

    try:
        dados = _extrair(trecho)
    except ConnectionError as e:
        print("[erro] Ollama não respondeu. Suba com: docker compose up -d", file=sys.stderr)
        print(f"       detalhe: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"[erro] saída do modelo não é JSON válido: {e}", file=sys.stderr)
        return 1

    print("JSON extraído com sucesso pelo SLM (Trilha B — Kelvin / CVM):")
    print(json.dumps(dados, ensure_ascii=False, indent=2))

    # Evidência de execução — checklist UC01_Sem01 (Trilha IA)
    SAIDA_EVIDENCIA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_EVIDENCIA.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[evidencia] salva em: {SAIDA_EVIDENCIA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
