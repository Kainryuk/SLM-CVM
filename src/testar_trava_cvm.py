"""Testa a trava de domínio do cvm-resolucoes SEM passar system prompt.

Usa o endpoint /api/chat com `stream: false` e apenas o campo `messages`
(usuário) — nada de system manual. A trava já está embutida no modelo.

Sai com um resumo passável de cada teste:
    - CVM -> resposta PT-BR coerente
    - Fora do tema -> "Não consta na base de conhecimento da CVM."
"""
from __future__ import annotations

import json
import urllib.request

HOST = "http://127.0.0.1:11434"
MODEL = "cvm-resolucoes"

TESTES = [
    # (rotulo, pergunta, tipo)
    ("CVM-1", "O que regula a Resolução CVM nº 1?", "cvm"),
    ("CVM-2", "Quais obrigações de divulgação existem para companhias abertas na CVM?", "cvm"),
    ("CVM-3", "O que é um fundo de investimento?", "cvm"),
    ("FORA-1", "Escreva em Python um script que faz merge de duas listas de dicionários.", "fora"),
    ("FORA-2", "Me fale sobre a Revolução Francesa.", "fora"),
    ("FORA-3", "Como faço um bolo de chocolate?", "fora"),
    ("FORA-4", "Quem ganhou a Copa do Mundo de 2022?", "fora"),
]

ALVO_FORA = "não consta na base de conhecimento da cvm"


def perguntar(msg: str) -> str:
    payload = {
        "model": MODEL,
        # NOTA: SEM "system" aqui — a trava está no próprio modelo.
        "messages": [{"role": "user", "content": msg}],
        "stream": False,
        "options": {"num_predict": 200, "temperature": 0},
    }
    req = urllib.request.Request(
        HOST + "/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read().decode())
    m = out["message"]
    return (m["content"] if isinstance(m, dict) else m.content).strip()


def main():
    print(f"=== testando {MODEL} (trava de domínio embutida) ===\n")
    for rotulo, pergunta, tipo in TESTES:
        resp = perguntar(pergunta)
        if tipo == "cvm":
            ok = resp and len(resp) > 20 and ALVO_FORA not in resp.lower()
            print(f"[{rotulo}] CVM? {'OK' if ok else 'NÃO CAIU NO TEMA'}")
            print(f"  P: {pergunta}")
            print(f"  R: {resp[:200]}\n")
        else:
            ok = ALVO_FORA in resp.lower()
            print(f"[{rotulo}] FORA DO TEMA? {'OK (devolveu a trava)' if ok else 'VAZOU'}")
            print(f"  P: {pergunta}")
            print(f"  R: {resp[:200]}\n")


if __name__ == "__main__":
    main()
