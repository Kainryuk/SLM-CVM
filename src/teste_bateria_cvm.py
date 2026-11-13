"""
UC01 Trilha B — Bateria de teste de verificação da trava de domínio CVM.

Roda perguntas contra o alias `cvm-resolucoes` SEM passar system prompt
(a trava está queimada no modelo) e, para as perguntas de CVM, busca a
fonte em data_lake/processed/ (ementa + início do texto normativo) para
comparar o SIGNIFICADO da resposta (não a literalidade).

Categorias:
- cvm   -> deve responder em pt-BR o assunto da norma (significado equivalente à ementa/texto)
- errado-> premissa errada (norma X sobre assunto Y que a X não regula) -> trava
- fora  -> assunto fora do domínio -> trava exata "Não consta na base de conhecimento da CVM."

Uso:
    .venv/Scripts/python src/teste_bateria_cvm.py
Saída:
    tests/bateria_cvm.json   (respostas + fontes + sinal de correspondência)
    (o veredeto final de significado é leitura humana sobre a saída)
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
import urllib.error

HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODELO = "cvm-resolucoes"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DL = os.path.join(RAIZ, "data_lake", "processed")
SAIDA = os.path.join(RAIZ, "tests", "bateria_cvm.json")
TRAVA = "Não consta na base de conhecimento da CVM."

# ── Bateria ─────────────────────────────────────────────────────────
# categoria: 'cvm' | 'errado' | 'fora'
# norma + caminho: fonte em data_lake/processed/ (para cvm/errado)
BATERIA = [
    dict(id="CVM-01", categoria="cvm",
         pergunta="O que disciplina a Resolução CVM nº 21?",
         norma="Resolução CVM nº 21",
         caminho="Administradores_de_Carteiras/resol021.md"),
    dict(id="CVM-02", categoria="cvm",
         pergunta="O que são BDRs segundo a Resolução CVM nº 182?",
         norma="Resolução CVM nº 182",
         caminho="BDR/resol182.md"),
    dict(id="CVM-03", categoria="cvm",
         pergunta="O que disciplina a Resolução CVM nº 9 sobre classificação de risco de crédito?",
         norma="Resolução CVM nº 9",
         caminho="Agencias_de_Classificacao_de_Risco_de_Credito/resol009.md"),
    dict(id="CVM-04", categoria="cvm",
         pergunta="Quais são as obrigações de divulgação de fato relevante da Resolução CVM nº 44?",
         norma="Resolução CVM nº 44",
         caminho="Companhia/resol044.md"),
    dict(id="CVM-05", categoria="cvm",
         pergunta="O que disciplina a Resolução CVM nº 11 sobre clubes de investimento?",
         norma="Resolução CVM nº 11",
         caminho="Clubes_de_Investimento/resol011.md"),
    dict(id="CVM-06", categoria="cvm",
         pergunta="O que disciplina a Resolução CVM nº 88?",
         norma="Resolução CVM nº 88",
         caminho="Ofertas_Publicas/resol088.md"),
    dict(id="CVM-07", categoria="cvm",
         pergunta="O que disciplina a Resolução CVM nº 20 sobre analistas de valores mobiliários?",
         norma="Resolução CVM nº 20",
         caminho="Analistas_de_Valores_Mobiliarios/resol020.md"),
    dict(id="CVM-08", categoria="cvm",
         pergunta="O que trata a Resolução CVM nº 78 sobre fusões e aquisições?",
         norma="Resolução CVM nº 78",
         caminho="Companhia/resol078.md"),
    dict(id="CVM-09", categoria="errado",
         pergunta="O que disciplina a Resolução CVM nº 88 sobre os direitos e deveres dos administradores de carteiras de valores mobiliários?",
         norma="Resolução CVM nº 88",
         caminho="Ofertas_Publicas/resol088.md"),
    dict(id="FORA-01", categoria="fora",
         pergunta="Me ensina a fazer macarrão à carbonara?"),
    dict(id="FORA-02", categoria="fora",
         pergunta="Escreva uma função Python para ordenar uma lista de números."),
    dict(id="FORA-03", categoria="fora",
         pergunta="Quem venceu a Copa do Mundo de 1998?"),
]


def fonte(caminho: str) -> dict:
    """Extrai ementa + início do texto normativo de um arquivo do data_lake."""
    p = os.path.join(BASE_DL, caminho)
    out = {"caminho": caminho, "ementa": None, "excerto": None}
    if not os.path.isfile(p):
        out["erro"] = f"fonte não encontrada: {p}"
        return out
    txt = open(p, encoding="utf-8").read()
    m = re.search(r"Assunto \(ementa\):\s*(.+)", txt)
    if m:
        out["ementa"] = m.group(1).strip()
    # início do texto normativo (depois do separador), até ~1200 chars
    i = txt.find("--- TEXTO NORMATIVO ---")
    out["excerto"] = txt[i + len("--- TEXTO NORMATIVO ---"):][:1200].strip() if i >= 0 else txt[:1200]
    return out


def pergunta_modelo(pergunta: str) -> tuple[str, dict]:
    """Chama /v1/chat/completions sem system prompt; retorna (resposta, meta)."""
    payload = {
        "model": MODELO,
        "messages": [{"role": "user", "content": pergunta}],
        "temperature": 0,
        "stream": False,
    }
    req = urllib.request.Request(
        HOST + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read().decode())
    resp = d["choices"][0]["message"]["content"].strip()
    return resp, d


def sinal_correspondencia(resposta: str, f: dict) -> float:
    """Sinal auxiliar: % de palavras-chave da ementa que aparecem na resposta."""
    em = (f.get("ementa") or "").lower()
    # palavras significativas (filtra stop-words pt simples)
    stop = set("""sobre do da dos das de para com em no na um uma o a que é e ou não se ao aos à às
    este essa esse essa esses essas dispoe regula regulamentar disciplinar respeito nos nas""".split())
    tokens = set(re.findall(r"[a-zà-ú]{5,}", em)) - stop
    if not tokens:
        return 0.0
    resp = resposta.lower()
    hit = sum(1 for t in tokens if t in resp)
    return round(hit / len(tokens), 2)


def main() -> int:
    results = []
    for caso in BATERIA:
        f = fonte(caso["caminho"]) if caso.get("caminho") else None
        resp, meta = pergunta_modelo(caso["pergunta"])
        rec = {
            "id": caso["id"],
            "categoria": caso["categoria"],
            "pergunta": caso["pergunta"],
            "norma": caso.get("norma"),
            "resposta_modelo": resp,
            "uso_tokens": meta.get("usage"),
            "trava_disparada": resp == TRAVA,
        }
        if f:
            rec["fonte"] = f
            if caso["categoria"] in ("cvm", "errado"):
                rec["sinal_correspondencia_ementa"] = sinal_correspondencia(resp, f)
        results.append(rec)
        print(f"[{caso['id']}] {caso['categoria']:<6} trava={rec['trava_disparada']} "
              f"resp={resp[:60]!r}")

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    json.dump({"modelo": MODELO, "cases": results},
              open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nsalvo: {SAIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
