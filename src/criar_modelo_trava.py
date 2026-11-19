"""
UC01 Trilha B — Cria/atualiza o modelo `cvm-resolucoes` no Ollama (base qwen2.5-coder:7b)
focado EXCLUSIVAMENTE em Resoluções da CVM, em pt-BR, apenas via prompt (sem RAG/pgvector).

Estratégia de engenharia de prompt para 7B:
  1. Compactação inteligente da tabela de 250 Resoluções (~15K chars em vez de 47K)
     removendo boilerplate jurídico repetitivo para maximizar atenção do modelo.
  2. Triagem obrigatória no topo E reforço final no rodapé do SYSTEM prompt
     (primacy + recency) para impedir vazamento de código Python ou trivia geral.
  3. Regra de ponte temática: se a pergunta mencionar programação ou dia a dia,
     verifica se há vínculo com Resoluções da CVM; se houver, responde apenas
     sob a ótica das Resoluções (sem código); se não houver, recusa exatamente.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
NOME = "cvm-resolucoes"
BASE = "qwen2.5-coder:7b"

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE_INDICE = os.path.join(RAIZ, "data_lake", "processed", "_indice_assuntos.json")
FONTE_FICHAS = os.path.join(RAIZ, "tests", "compreensao_resolucoes.json")
MAX_CHARS_ASSUNTO = 90

_MESES_EN = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
    "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
    "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
}


def _formatar_data(raw: str) -> str:
    """Normaliza datas do índice para DD/MM/AA (compacta para economizar contexto)."""
    raw = (raw or "").strip()
    m_br = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", raw)
    if m_br:
        return f"{m_br.group(1)}/{m_br.group(2)}/{m_br.group(3)[2:]}"
    m = re.match(r"^[A-Za-z]{3}\s+([A-Za-z]{3})\s+(\d{1,2})\s+.*?(\d{4})$", raw)
    if m and m.group(1) in _MESES_EN:
        return f"{int(m.group(2)):02d}/{_MESES_EN[m.group(1)]}/{m.group(3)[2:]}"
    return raw or "s/d"


def _extrair_relacao(assunto: str) -> str:
    """Extrai menção explícita a altera/revoga na ementa (vazio se não houver)."""
    limpo = re.sub(r"\s*\((?:Publicad|Retificad|Republicad)[ao] no DOU.*?\)", "", assunto or "")
    limpo = re.sub(r"\s+", " ", limpo).strip().rstrip(".;")
    m = re.search(r"\b((?:altera|revoga|prorroga|dá nova redação)\b.*)", limpo, flags=re.IGNORECASE)
    if not m:
        return ""
    rel = re.sub(r"\s*,\s*de\s+\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4}", "", m.group(1), flags=re.IGNORECASE)
    rel = re.sub(r"\s+", " ", rel).strip().rstrip(".;")
    if len(rel) > 65:
        rel = rel[:62].rsplit(" ", 1)[0] + "..."
    return rel


def limpar_ementa_compacta(a: str) -> str:
    """Extrai o núcleo temático da ementa, removendo boilerplate repetitivo."""
    a = a or ""
    # Corta cauda de revogações/alterações secundárias (que vão para o campo próprio) e datas do DOU
    a = re.split(r"(?:\s+e\s+|,\s*)(?:revoga|altera|dá nova|prorroga)\b", a, flags=re.IGNORECASE)[0]
    a = re.sub(r"\s*\((?:Publicad|Retificad|Republicad)[ao] no DOU.*?\)", "", a)
    # Remove prefixos verbosos comuns mantendo o sentido
    a = re.sub(r"^(?:Dispõe sobre (?:a |o |as |os )?|Estabelece (?:normas e procedimentos (?:a serem observados )?(?:sobre|na|para) )?)", "", a, flags=re.IGNORECASE)
    a = re.sub(r"^(?:Aprova a Consolidação d[ao] |Ratifica [ao] |Aprova [ao] )", "", a, flags=re.IGNORECASE)
    a = re.sub(r"do Comitê de Pronunciamentos Contábeis\s*[–-]?\s*CPC,?\s*que trata (?:de |sobre )?", "CPC: ", a, flags=re.IGNORECASE)
    a = re.sub(r"emitido pelo Comitê de Pronunciamentos Contábeis\s*[–-]?\s*CPC", "(CPC)", a, flags=re.IGNORECASE)
    a = re.sub(r"\s+", " ", a).strip().rstrip(",.;")
    return a


def montar_indice(fonte: str = FONTE_INDICE, max_chars: int = MAX_CHARS_ASSUNTO) -> str:
    """Gera a tabela compacta 'NNN (DD/MM/AAAA): assunto | relação' (3 dígitos, ordenada)."""
    d = json.load(open(fonte, encoding="utf-8"))
    raw_items = d if "indice" in fonte else d.get("resultados", [])

    nums: dict[str, str] = {}
    for r in raw_items:
        m = re.search(r"(\d+)", str(r.get("norma", "")))
        if not m:
            continue
        assunto_bruto = str(r.get("assunto", ""))
        a = limpar_ementa_compacta(assunto_bruto)
        if not a:
            continue
        if len(a) > max_chars:
            a = a[: max_chars - 3].rsplit(" ", 1)[0] + "..."
        data_fmt = _formatar_data(str(r.get("data", "")))
        rel = _extrair_relacao(assunto_bruto)
        sufixo = f" | {rel}" if rel else ""
        nums.setdefault(m.group(1), f"{data_fmt}: {a}{sufixo}")

    return "\n".join(f"[{int(n):03d}] {nums[n]}" for n in sorted(nums, key=int))


SISTEMA_TEMPLATE = """\
Você é um assistente normativo especialista EXCLUSIVAMENTE nas **Resoluções da CVM** (Comissão de Valores Mobiliários — Brasil).
Responda SEMPRE em português do Brasil (pt-BR).

REGRAS ESTRITAS DE DOMÍNIO:
1. ESCOPO ÚNICO: Você só conhece e só pode responder sobre **Resoluções da CVM** (listadas na BIBLIOTECA abaixo).
2. PROIBIÇÃO ABSOLUTA DE CÓDIGO: Você NÃO é um assistente de programação. NUNCA escreva código (Python, SQL, JS, C, etc.) nem explique sintaxe de programação.
3. TRIAGEM OBRIGATÓRIA (PARA PROGRAMAÇÃO, TECNOLOGIA OU ASSUNTOS DO DIA A DIA):
   Antes de responder qualquer pergunta, faça esta verificação:
   - Passo A: A pergunta (mesmo falando de programação, sistemas ou dia a dia) tem alguma relação com uma Resolução da CVM na BIBLIOTECA?
     * Se SIM (ex.: blockchain/DLT -> Res. 249; plataforma de crowdfunding -> Res. 88; sistemas/intermediação -> Res. 35/135; investir em grupo com amigos -> Res. 11; perfil de investidor/assessor -> Res. 30/178; fundos -> Res. 175):
       Responda EXCLUSIVAMENTE explicando o que as Resoluções da CVM dizem sobre o tema, sem escrever código e sem conselhos genéricos fora das normas.
     * Se NÃO tiver nenhuma relação com a CVM (ex.: script Python genérico, receita culinária, história geral, esportes, clima, piadas):
       Responda EXATAMENTE esta frase e mais nada:
       "Não consta na base de conhecimento da CVM."
4. NÚMERO DE RESOLUÇÃO E TRAVA ANTI-ALUCINAÇÃO:
   - Localize o marcador exato `[NNN]` com 3 dígitos na BIBLIOTECA (ex.: nº 1 -> `[001]`; nº 24 -> `[024]`; nº 86 -> `[086]`).
   - Se `[NNN]` NÃO existir na BIBLIOTECA (ex.: `[999]`), responda EXATAMENTE: "Não consta na base de conhecimento da CVM."
   - LEITURA ESTRITA: Responda EXCLUSIVAMENTE com base no texto literal da linha `[NNN]` correspondente. Nunca leia a linha de outra resolução.
   - PROIBIÇÃO DE INVENÇÃO RELACIONAL: NUNCA afirme que uma resolução altera, revoga ou substitui outra norma se isso NÃO estiver escrito após `|` na própria linha `[NNN]`. Se não houver `|` na linha `[NNN]`, informe que não consta alteração ou revogação de outras normas na ementa.
   - NÃO misture números de resoluções de perguntas anteriores. Comece citando exatamente: `Conforme o registro [NNN] (data): ...`
   - Se a pergunta afirmar uma premissa falsa sobre a Resolução N, corrija dizendo o que a linha `[NNN]` realmente trata.

BIBLIOTECA DE RESOLUÇÕES DA CVM ([NNN] data: assunto | relação opcional):
{indice}

EXEMPLOS DE RESPOSTAS CORRETAS:
- P: "O que regula a Resolução CVM nº 1?"
  R: "Conforme o registro [001] (14/09/20): a Resolução CVM nº 1 estabelece a nomenclatura de atos a serem expedidos pela Comissão de Valores Mobiliários, sem alteração ou revogação citada na ementa."
- P: "O que faz a Resolução CVM nº 24?"
  R: "Conforme o registro [024] (05/03/21): a Resolução CVM nº 24 aprova o Regimento Interno da Comissão de Valores Mobiliários, sem alteração ou revogação citada na ementa."
- P: "Escreva em Python um script que faz merge de duas listas de dicionários."
  R: "Não consta na base de conhecimento da CVM."
- P: "Me fale sobre a Revolução Francesa."
  R: "Não consta na base de conhecimento da CVM."
- P: "Quem ganhou a Copa do Mundo de 2022?"
  R: "Não consta na base de conhecimento da CVM."
- P: "Como faço um bolo de chocolate?"
  R: "Não consta na base de conhecimento da CVM."
- P: "Estou programando uma plataforma para captar investimentos para pequenas empresas, qual resolução da CVM se aplica?"
  R: "No âmbito das Resoluções da CVM, a oferta pública de distribuição de valores mobiliários de sociedades empresárias de pequeno porte por meio de plataforma eletrônica é disciplinada pela Resolução CVM nº 88. Não forneço código de programação, apenas a referência normativa das Resoluções da CVM."
- P: "Quero juntar amigos do trabalho para investir juntos na bolsa, existe alguma resolução?"
  R: "Sim. A constituição, administração, funcionamento, divulgação de informações e distribuição de cotas dos Clubes de Investimento são disciplinados pela Resolução CVM nº 11 (e suas demonstrações financeiras pela Resolução CVM nº 12)."

LEMBRETE FINAL OBRIGATÓRIO:
- Se a pergunta for sobre programação pura, história, receitas, esportes ou qualquer assunto sem vínculo com Resoluções da CVM, responda APENAS: "Não consta na base de conhecimento da CVM."
- NUNCA invente que uma resolução altera ou revoga outra norma se isso não constar literalmente na linha dela na BIBLIOTECA.
- Nunca escreva código de programação. Responda sempre em pt-BR.
"""


def _post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        HOST + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            raw = r.read().decode()
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        if not lines:
            return {"raw": raw}
        out = json.loads(lines[-1])
        for ln in lines:
            j = json.loads(ln)
            if "error" in j:
                out["error"] = j["error"]
                break
        return out
    except urllib.error.HTTPError as e:
        return {"status": e.code, "body": e.read().decode(errors="replace")[:300]}


def main() -> int:
    ap = argparse.ArgumentParser(description="Cria/atualiza o modelo cvm-resolucoes no Ollama.")
    ap.add_argument("--base", default=BASE, help=f"Modelo base (padrão: {BASE}).")
    ap.add_argument("--fonte", default="indice", choices=["indice", "fichas"],
                    help="Fonte da tabela: indice (ementas, padrão) ou fichas (resumos SLM)")
    ap.add_argument("--num-ctx", type=int, default=16384, help="Tamanho da janela de contexto (padrão: 16384)")
    ap.add_argument("--sem-indice", action="store_true", help="Só a trava, sem tabela")
    args = ap.parse_args()
    base = args.base

    if args.sem_indice:
        sistema = SISTEMA_TEMPLATE.replace("{indice}", "(sem tabela nesta versão)")
        print(f"[criar] trava sem índice a partir de {base}...")
    else:
        fonte = FONTE_INDICE if args.fonte == "indice" else FONTE_FICHAS
        try:
            indice = montar_indice(fonte)
            sistema = SISTEMA_TEMPLATE.replace("{indice}", indice)
            print(f"[criar] {len(indice.splitlines())} resoluções | {len(sistema)} chars no prompt | num_ctx={args.num_ctx} (base {base})...")
        except Exception as e:
            print(f"[erro] não li {fonte} ({e}); criando SÓ a trava.", file=sys.stderr)
            sistema = SISTEMA_TEMPLATE.replace("{indice}", "(sem tabela nesta versão)")

    _post("/api/delete", {"name": NOME})

    out = _post(
        "/api/create",
        {
            "name": NOME,
            "from": base,
            "system": sistema,
            "parameters": {
                "temperature": 0,
                "top_k": 1,
                "top_p": 0.1,
                "num_ctx": args.num_ctx,
                "repeat_penalty": 1.1,
            },
        },
    )
    if out.get("error"):
        print("[erro]", json.dumps(out, ensure_ascii=False)[:500], file=sys.stderr)
        return 1

    with urllib.request.urlopen(HOST + "/api/tags", timeout=20) as r:
        nomes = [m["name"] for m in json.loads(r.read().decode()).get("models", [])]
    if NOME not in nomes and NOME + ":latest" not in nomes:
        print(f"[erro] {NOME} não aparece em /api/tags (tem: {nomes})", file=sys.stderr)
        return 1
    print(f"[ok] modelo {NOME}:latest atualizado e registrado (base {base}, num_ctx={args.num_ctx}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
