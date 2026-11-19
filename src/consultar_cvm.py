"""
Consulta CVM com pré-filtro determinístico em Python (sem RAG/pgvector).

Em vez de enviar todas as 250 Resoluções no SYSTEM prompt (onde modelos 7B sofrem
de Lost-in-the-Middle), este script filtra localmente `_indice_assuntos.json` por
número de resolução ou palavras-chave e envia ao Ollama apenas os registros
relevantes (1 a 5 normas), com regras estritas de leitura literal em pt-BR.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
import unicodedata
import urllib.error
import urllib.request

HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODELO_PADRAO = "qwen2.5-coder:7b"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDICE_PATH = os.path.join(RAIZ, "data_lake", "processed", "_indice_assuntos.json")
DATA_LAKE_DIR = os.path.join(RAIZ, "data_lake")

_STOPWORDS = {
    "a", "as", "o", "os", "e", "de", "da", "do", "das", "dos", "em", "na", "no",
    "nas", "nos", "para", "por", "com", "sem", "sobre", "que", "qual", "quais",
    "como", "faz", "fazer", "regula", "trata", "diz", "resolucao", "resolucoes",
    "cvm", "n", "nr", "numero", "uma", "um", "ao", "aos", "se", "ou", "esta",
    "este", "me", "fala", "fale", "diga", "sao",
}

SISTEMA_ESTRITO = """\
Você é um assistente normativo especialista EXCLUSIVAMENTE nas Resoluções da CVM (Brasil).
Responda SEMPRE em português do Brasil (pt-BR).

REGRAS ESTRITAS:
1. Se o CONTEXTO abaixo estiver vazio ou indicar "NENHUMA NORMA ENCONTRADA", responda EXATAMENTE:
   "Não consta na base de conhecimento da CVM."
2. Responda EXCLUSIVAMENTE com base no texto literal fornecido no CONTEXTO abaixo.
3. NUNCA escreva código de programação (Python, SQL, JS, etc.).
4. NUNCA afirme que uma resolução altera, revoga ou substitui outra norma se isso NÃO estiver escrito literalmente no CONTEXTO.
5. Cite sempre o número e a data da resolução exatamente como constam no CONTEXTO.
"""


def _norm(texto: str) -> str:
    s = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    return s.lower()


def _carregar_indice() -> list[dict]:
    with open(INDICE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _ler_trecho_norma(arquivo_limpo: str, max_chars: int = 1200) -> str:
    caminho = os.path.join(DATA_LAKE_DIR, arquivo_limpo)
    if not os.path.isfile(caminho):
        return ""
    with open(caminho, encoding="utf-8", errors="replace") as f:
        conteudo = f.read(max_chars)
    return conteudo.strip()


def buscar_normas(pergunta: str, indice: list[dict], top_k: int = 5) -> list[dict]:
    """Filtra normas por número explícito da resolução ou por palavras-chave."""
    # 1. Busca por número explícito (ex.: "nº 86", "Resolução 175", "CVM 24")
    nums_citados = re.findall(
        r"(?:resolu[çc][ãa]o(?:\s+cvm)?\s*(?:n[º°o.]*\s*)?|cvm\s*(?:n[º°o.]*\s*)?|n[º°]\s*)(\d{1,3})\b",
        pergunta,
        flags=re.IGNORECASE,
    )
    if nums_citados:
        alvos = {str(int(n)) for n in nums_citados}
        exatos = []
        for item in indice:
            m = re.search(r"(\d+)", str(item.get("norma", "")))
            if m and str(int(m.group(1))) in alvos:
                exatos.append(item)
        if exatos:
            return exatos[:top_k]

    # 2. Busca por palavras-chave (sem stopwords)
    tokens = [
        t for t in re.findall(r"[a-z0-9]+", _norm(pergunta))
        if len(t) >= 3 and t not in _STOPWORDS
    ]
    if not tokens:
        return []

    ranqueados: list[tuple[int, dict]] = []
    for item in indice:
        texto_busca = _norm(
            f"{item.get('norma', '')} {item.get('tag', '')} {item.get('assunto', '')}"
        )
        score = sum(1 for tok in tokens if tok in texto_busca)
        if score > 0:
            ranqueados.append((score, item))

    ranqueados.sort(key=lambda par: par[0], reverse=True)
    if ranqueados:
        return [item for _, item in ranqueados[:top_k]]

    # 3. Perguntas panorâmicas sobre resoluções recentes/principais da CVM
    q_norm = _norm(pergunta)
    eh_panoramica = any(
        p in q_norm for p in ("recente", "ultima", "nova", "principa", "quais", "lista", "atual", "2026", "2025")
    ) and any(
        d in q_norm for d in ("resoluc", "cvm", "norma")
    )
    if eh_panoramica:
        com_num = []
        for item in indice:
            m = re.search(r"(\d+)", str(item.get("norma", "")))
            if m:
                com_num.append((int(m.group(1)), item))
        com_num.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in com_num[:8]]

    return []


def montar_contexto(itens: list[dict]) -> str:
    if not itens:
        return "NENHUMA NORMA ENCONTRADA."
    blocos = []
    incluir_trecho = len(itens) == 1
    for item in itens:
        bloco = (
            f"- Norma: {item.get('norma')}\n"
            f"  Data: {item.get('data')}\n"
            f"  Tag: {item.get('tag')}\n"
            f"  Ementa oficial: {item.get('assunto')}"
        )
        if incluir_trecho and item.get("arquivo_limpo"):
            trecho = _ler_trecho_norma(item["arquivo_limpo"], max_chars=900)
            if trecho:
                bloco += f"\n  Início do texto oficial:\n{trecho}"
        blocos.append(bloco)
    return "\n\n".join(blocos)


def garantir_ollama(espera_s: int = 20) -> None:
    """Verifica se o Ollama está ativo; se não estiver, inicia `ollama serve` automaticamente."""
    try:
        with urllib.request.urlopen(f"{HOST}/api/tags", timeout=2):
            return
    except Exception:
        pass

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    env_serve = {**os.environ, "OLLAMA_HOST": HOST}
    subprocess.Popen(
        ["ollama.exe", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env_serve,
        creationflags=creationflags,
    )
    limite = time.time() + espera_s
    while time.time() < limite:
        try:
            with urllib.request.urlopen(f"{HOST}/api/tags", timeout=2):
                return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Ollama não respondeu em {HOST} após {espera_s}s.")


def consultar(pergunta: str, modelo: str = MODELO_PADRAO, num_gpu: int = 16) -> tuple[str, list[str]]:
    garantir_ollama()
    indice = _carregar_indice()
    itens = buscar_normas(pergunta, indice, top_k=5)
    normas_usadas = [str(i.get("norma")) for i in itens]

    if not itens:
        return "Não consta na base de conhecimento da CVM.", []

    contexto = montar_contexto(itens)
    prompt_usuario = (
        f"CONTEXTO OFICIAL (CVM):\n{contexto}\n\n"
        f"PERGUNTA: {pergunta}\n\n"
        "Responda de forma direta e fiel apenas ao CONTEXTO OFICIAL acima."
    )

    payload = json.dumps({
        "model": modelo,
        "system": SISTEMA_ESTRITO,
        "prompt": prompt_usuario,
        "stream": False,
        "options": {
            "temperature": 0,
            "top_k": 1,
            "top_p": 0.1,
            "repeat_penalty": 1.1,
            "num_ctx": 4096,
            "num_gpu": num_gpu,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{HOST}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = json.loads(r.read().decode("utf-8")).get("response", "").strip()
    return resp, normas_usadas


def modo_chat(modelo: str = MODELO_PADRAO, num_gpu: int = 16) -> int:
    """Loop interativo estilo `ollama run`, com pré-filtro automático a cada pergunta."""
    print(f"CVM Resoluções (pré-filtro Python + {modelo} | num_gpu={num_gpu})")
    print("Comandos: /gpu <N> para alterar camadas GPU | /sair para encerrar\n")

    while True:
        try:
            pergunta = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando.")
            return 0

        if not pergunta:
            continue
        cmd = pergunta.lower()
        if cmd in {"/sair", "/exit", "/quit", "sair", "exit"}:
            return 0
        if cmd.startswith("/gpu "):
            try:
                num_gpu = int(cmd.split()[1])
                print(f"[config] num_gpu atualizado para {num_gpu}\n")
            except (IndexError, ValueError):
                print("[uso] /gpu <numero>, ex.: /gpu 16\n")
            continue

        try:
            resp, normas = consultar(pergunta, modelo=modelo, num_gpu=num_gpu)
            print(f"[Pré-filtro]: {normas or 'nenhuma (bloqueio imediato)'}")
            print(f"{resp}\n")
        except Exception as e:
            print(f"[erro ao consultar Ollama]: {e}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Consulta Resoluções da CVM com pré-filtro Python (sem RAG/pgvector).")
    ap.add_argument("--pergunta", "-p", help="Pergunta única para consultar.")
    ap.add_argument("--modelo", default=MODELO_PADRAO, help=f"Modelo Ollama (padrão: {MODELO_PADRAO}).")
    ap.add_argument("--num-gpu", type=int, default=16, help="Camadas na GPU (padrão: 16).")
    ap.add_argument("--lote-teste", action="store_true", help="Executa a bateria de testes (5 resoluções + trava).")
    ap.add_argument("--chat", action="store_true", help="Abre o chat interativo no terminal (padrão sem -p).")
    args = ap.parse_args()

    if args.lote_teste:
        perguntas = [
            "O que faz a Resolução CVM nº 24?",
            "O que faz a Resolução CVM nº 175?",
            "O que faz a Resolução CVM nº 86?",
            "O que faz a Resolução CVM nº 161?",
            "O que faz a Resolução CVM nº 193?",
            "Escreva um script Python para ordenar uma lista.",
            "Estou criando uma plataforma de investimento coletivo para pequenas empresas, qual resolução se aplica?",
        ]
        for q in perguntas:
            resp, normas = consultar(q, modelo=args.modelo, num_gpu=args.num_gpu)
            print(f"P: {q}")
            print(f"[Pré-filtro]: {normas or 'nenhuma (bloqueio imediato)'}")
            print(f"R: {resp}\n" + "-" * 60)
        return 0

    if args.pergunta:
        resp, normas = consultar(args.pergunta, modelo=args.modelo, num_gpu=args.num_gpu)
        print(f"[Pré-filtro]: {normas or 'nenhuma (bloqueio imediato)'}")
        print(resp)
        return 0

    return modo_chat(modelo=args.modelo, num_gpu=args.num_gpu)


if __name__ == "__main__":
    raise SystemExit(main())
