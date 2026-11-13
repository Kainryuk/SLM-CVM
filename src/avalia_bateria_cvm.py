"""
UC01 Trilha B — Avaliação quantitativa da trava + tabela (sem RAG).

Varre uma amostra de números do acervo, pergunta "O que disciplina a Resolução
CVM nº N?" ao alias cvm-resolucoes (sem system prompt) e classifica cada
resposta comparando o SIGNIFICADO com a ementa autoritativa
(data_lake/processed/_indice_assuntos.json).

Classificações (pergunta neutra, dentro do domínio):
  ok           -> significado bate com a ementa (contenção de palavras >= 0.35)
  parcial      -> bate em parte (0.20..0.35)
  divergente   -> não bate (< 0.20) — ex.: pegou a linha errada / alucinou
  falso_neg    -> devolveu a trava "Não consta..." mesmo sendo in-domain
  over_trigger -> resposta a pergunta NEUTRA com o prefixo "premissa não confere"

Uso:
    .venv/Scripts/python.exe src/avalia_bateria_cvm.py [N]
    (N = tamanho da amostra; padrão 30. 0 = todos os números)
Saída:
    tests/avaliacao_cvm.json  +  resumo por classe no console
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
import unicodedata
import urllib.request

HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODELO = "cvm-resolucoes"
TRAVA = "Não consta na base de conhecimento da CVM."
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = os.path.join(RAIZ, "data_lake", "processed", "_indice_assuntos.json")
SAIDA = os.path.join(RAIZ, "tests", "avaliacao_cvm.json")

STOP = set("""sobre do da dos das de para com em no na uma um o a e que é ée se ao aos à às
e este esta isso esse essa esses essas dispoe regula regulamentar disciplina trata
trata-se estabelece esta sao ser tem por sua suas se nos nas nem ou mas por quando
como qual quais quanto ao menos mais cada todos todas tudo entre durante desde até
pelo pela pelos pelas sendo como nao tambem pois porque portanto assim então
valor valores mobiliario mobiliarios movel titulo titulos acao acoes operacao
operacoes atividade atividades ambito mercado publico publicos oferta ofertas
distribuicao emissao informacao informacoes companhia companhias sociedade
sociedades investidor investidores cfm dou""" .split())


def norm(s: str) -> str:
    s = s.lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return s


def palavras(texto: str) -> set:
    toks = re.findall(r"[a-z]{4,}", norm(texto))
    return {t for t in toks if t not in STOP}


def _ementa_por_numero() -> dict[str, str]:
    d = json.load(open(FONTE, encoding="utf-8"))
    out: dict[str, str] = {}
    for r in d:
        m = re.search(r"(\d+)", str(r.get("norma", "")))
        if m:
            out.setdefault(m.group(1), str(r.get("assunto", "")))
    return out


def perguntar(n: str) -> str:
    payload = {
        "model": MODELO,
        "messages": [{"role": "user", "content": f"O que disciplina a Resolução CVM nº {n}?"}],
        "temperature": 0,
        "stream": False,
    }
    req = urllib.request.Request(
        HOST + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=200) as r:
        d = json.loads(r.read().decode())
    return d["choices"][0]["message"]["content"].strip()


def classificar(resposta: str, ementa: str) -> tuple[str, float]:
    if resposta == TRAVA:
        return "falso_neg", 0.0
    over = "premissa não confere" in norm(resposta)
    exp = palavras(ementa)
    got = palavras(resposta)
    if not exp:
        return ("over_trigger" if over else "ok"), 1.0
    cont = len(exp & got) / len(exp)
    if over and cont < 0.35:
        return "over_trigger", round(cont, 2)
    if cont >= 0.35:
        return "ok", round(cont, 2)
    if cont >= 0.20:
        return "parcial", round(cont, 2)
    return "divergente", round(cont, 2)


def main() -> int:
    n_arg = sys.argv[1] if len(sys.argv) > 1 else "30"
    ementas = _ementa_por_numero()
    numeros = sorted(ementas, key=int)
    if n_arg.isdigit() and int(n_arg) > 0:
        k = int(n_arg)
        # amostra determinística: espalha pelos números + sempre os 8 da bateria manual
        step = max(1, len(numeros) // k)
        amostra = list(numeros[::step])[:k]
        for obrig in ["9", "11", "20", "21", "44", "78", "88", "182"]:
            if obrig not in amostra:
                amostra.append(obrig)
        amostra = amostra[: max(k, 8)]
    else:
        amostra = numeros

    casos = []
    contagem = {"ok": 0, "parcial": 0, "divergente": 0, "falso_neg": 0, "over_trigger": 0}
    for i, n in enumerate(amostra, 1):
        resp = perguntar(n)
        cls, cont = classificar(resp, ementas[n])
        contagem[cls] = contagem.get(cls, 0) + 1
        casos.append(
            {
                "n": n,
                "ementa": ementas[n][:160],
                "resposta": resp,
                "classe": cls,
                "conteudo": cont,
            }
        )
        print(f"[{i}/{len(amostra)}] nº{n:<4} -> {cls} (cont={cont})")

    total = len(amostra)
    resumo = {
        "modelo": MODELO,
        "total": total,
        **{k: v for k, v in contagem.items()},
        "taxa_ok": round(contagem.get("ok", 0) / total, 2),
        "taxa_aceitavel": round((contagem.get("ok", 0) + contagem.get("parcial", 0)) / total, 2),
        "falsos_negativos": contagem.get("falso_neg", 0),
        "over_triggers": contagem.get("over_trigger", 0),
    }
    json.dump({"resumo": resumo, "casos": casos}, open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n=== RESUMO ===")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    print("salvo:", SAIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
