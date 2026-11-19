"""
Proxy automático compatível com Ollama (incluindo streaming / `ollama run`) e OpenAI.

Ao receber qualquer mensagem em /api/chat, /api/generate ou /v1/chat/completions:
1. Verifica se o Ollama real (OLLAMA_REAL_HOST, padrão 127.0.0.1:11434) está ativo;
   se não estiver, inicia `ollama serve` automaticamente.
2. Executa o pré-filtro determinístico em Python (`_indice_assuntos.json`).
3. Se nenhuma norma for encontrada, responde imediatamente com a trava padrão.
4. Se houver normas, injeta apenas as 1 a 5 relevantes e encaminha ao Ollama (com
   suporte completo a `stream: true` e `stream: false`).

Nota importante:
- Este proxy usa `OLLAMA_REAL_HOST` (padrão `http://127.0.0.1:11434`) para falar
  com o motor Ollama real. Assim, você pode definir `OLLAMA_HOST=http://127.0.0.1:11435`
  no Windows/terminal sem causar loop infinito.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import consultar_cvm  # noqa: E402

OLLAMA_REAL_HOST = os.environ.get("OLLAMA_REAL_HOST", "http://127.0.0.1:11434").rstrip("/")
consultar_cvm.HOST = OLLAMA_REAL_HOST

NUM_GPU_PADRAO = 16
BLOQUEIO_MSG = "Não consta na base de conhecimento da CVM."


def _responder_json(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _proxy_get(handler: BaseHTTPRequestHandler, path: str) -> None:
    consultar_cvm.garantir_ollama()
    with urllib.request.urlopen(f"{OLLAMA_REAL_HOST}{path}", timeout=15) as r:
        raw = r.read()
        ctype = r.headers.get("Content-Type", "application/json; charset=utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _proxy_post_passthrough(handler: BaseHTTPRequestHandler, path: str, raw_body: bytes) -> None:
    consultar_cvm.garantir_ollama()
    req = urllib.request.Request(
        f"{OLLAMA_REAL_HOST}{path}",
        data=raw_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            ctype = r.headers.get("Content-Type", "application/json; charset=utf-8")
            status = r.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        ctype = "application/json; charset=utf-8"
        status = e.code
    handler.send_response(status)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _preparar_payload_ollama(pergunta: str, modelo: str, num_gpu: int, stream: bool) -> tuple[bool, bytes]:
    """Retorna (encontrou_norma, payload_bytes)."""
    consultar_cvm.garantir_ollama()
    indice = consultar_cvm._carregar_indice()
    itens = consultar_cvm.buscar_normas(pergunta, indice, top_k=5)
    if not itens:
        return False, b""

    contexto = consultar_cvm.montar_contexto(itens)
    prompt_usuario = (
        f"CONTEXTO OFICIAL (CVM):\n{contexto}\n\n"
        f"PERGUNTA: {pergunta}\n\n"
        "Responda de forma direta e fiel apenas ao CONTEXTO OFICIAL acima."
    )
    payload = json.dumps({
        "model": modelo,
        "system": consultar_cvm.SISTEMA_ESTRITO,
        "prompt": prompt_usuario,
        "stream": stream,
        "options": {
            "temperature": 0,
            "top_k": 1,
            "top_p": 0.1,
            "repeat_penalty": 1.1,
            "num_ctx": 4096,
            "num_gpu": num_gpu,
        },
    }).encode("utf-8")
    return True, payload


def _stream_ndjson_ollama(handler: BaseHTTPRequestHandler, payload: bytes, modelo_saida: str, modo_chat: bool) -> None:
    handler.send_response(200)
    handler.send_header("Content-Type", "application/x-ndjson")
    handler.send_header("Connection", "close")
    handler.end_headers()

    req = urllib.request.Request(
        f"{OLLAMA_REAL_HOST}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        for line in r:
            if not line.strip():
                continue
            chunk = json.loads(line.decode("utf-8"))
            if modo_chat:
                out = {
                    "model": modelo_saida,
                    "created_at": chunk.get("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
                    "message": {"role": "assistant", "content": chunk.get("response", "")},
                    "done": chunk.get("done", False),
                }
                if chunk.get("done"):
                    for k in ("done_reason", "total_duration", "load_duration", "prompt_eval_count", "eval_count"):
                        if k in chunk:
                            out[k] = chunk[k]
            else:
                chunk["model"] = modelo_saida
                out = chunk
            handler.wfile.write((json.dumps(out, ensure_ascii=False) + "\n").encode("utf-8"))
            handler.wfile.flush()


def _stream_ndjson_bloqueio(handler: BaseHTTPRequestHandler, modelo_saida: str, modo_chat: bool) -> None:
    handler.send_response(200)
    handler.send_header("Content-Type", "application/x-ndjson")
    handler.send_header("Connection", "close")
    handler.end_headers()
    agora = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if modo_chat:
        c1 = {"model": modelo_saida, "created_at": agora, "message": {"role": "assistant", "content": BLOQUEIO_MSG}, "done": False}
        c2 = {"model": modelo_saida, "created_at": agora, "message": {"role": "assistant", "content": ""}, "done": True, "done_reason": "stop"}
    else:
        c1 = {"model": modelo_saida, "created_at": agora, "response": BLOQUEIO_MSG, "done": False}
        c2 = {"model": modelo_saida, "created_at": agora, "response": "", "done": True, "done_reason": "stop"}
    for c in (c1, c2):
        handler.wfile.write((json.dumps(c, ensure_ascii=False) + "\n").encode("utf-8"))
        handler.wfile.flush()


class CVMProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    modelo = consultar_cvm.MODELO_PADRAO
    num_gpu = NUM_GPU_PADRAO

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return

    def do_HEAD(self) -> None:
        self.send_response(200)
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Ollama is running (CVM proxy)")
            return
        if self.path.startswith("/health"):
            _responder_json(self, 200, {"status": "ok", "modelo": self.modelo, "num_gpu": self.num_gpu})
            return
        if self.path.startswith("/api/tags") or self.path.startswith("/api/version") or self.path.startswith("/api/ps"):
            _proxy_get(self, self.path)
            return
        _responder_json(self, 404, {"error": "endpoint não suportado"})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        body = json.loads(raw_body.decode("utf-8") or "{}")
        num_gpu = int((body.get("options") or {}).get("num_gpu", self.num_gpu))
        modelo_req = str(body.get("model", "cvm-resolucoes"))

        if self.path.startswith("/api/show"):
            _proxy_post_passthrough(self, "/api/show", raw_body)
            return

        if self.path.startswith("/api/generate"):
            stream = bool(body.get("stream", True))
            pergunta = str(body.get("prompt", "")).strip()
            ok, payload = _preparar_payload_ollama(pergunta, self.modelo, num_gpu, stream)
            if not ok:
                if stream:
                    _stream_ndjson_bloqueio(self, modelo_req, modo_chat=False)
                else:
                    _responder_json(self, 200, {
                        "model": modelo_req,
                        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "response": BLOQUEIO_MSG,
                        "done": True,
                    })
                return
            if stream:
                _stream_ndjson_ollama(self, payload, modelo_req, modo_chat=False)
            else:
                req = urllib.request.Request(f"{OLLAMA_REAL_HOST}/api/generate", data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=180) as r:
                    resp = json.loads(r.read().decode("utf-8")).get("response", "").strip()
                _responder_json(self, 200, {
                    "model": modelo_req,
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "response": resp,
                    "done": True,
                })
            return

        if self.path.startswith("/api/chat"):
            stream = bool(body.get("stream", True))
            msgs = body.get("messages", [])
            pergunta = next((str(m.get("content", "")).strip() for m in reversed(msgs) if m.get("role") == "user"), "")
            ok, payload = _preparar_payload_ollama(pergunta, self.modelo, num_gpu, stream)
            if not ok:
                if stream:
                    _stream_ndjson_bloqueio(self, modelo_req, modo_chat=True)
                else:
                    _responder_json(self, 200, {
                        "model": modelo_req,
                        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "message": {"role": "assistant", "content": BLOQUEIO_MSG},
                        "done": True,
                    })
                return
            if stream:
                _stream_ndjson_ollama(self, payload, modelo_req, modo_chat=True)
            else:
                req = urllib.request.Request(f"{OLLAMA_REAL_HOST}/api/generate", data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=180) as r:
                    resp = json.loads(r.read().decode("utf-8")).get("response", "").strip()
                _responder_json(self, 200, {
                    "model": modelo_req,
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "message": {"role": "assistant", "content": resp},
                    "done": True,
                })
            return

        if self.path.startswith("/v1/chat/completions"):
            stream = bool(body.get("stream", False))
            msgs = body.get("messages", [])
            pergunta = next((str(m.get("content", "")).strip() for m in reversed(msgs) if m.get("role") == "user"), "")
            ok, payload = _preparar_payload_ollama(pergunta, self.modelo, num_gpu, stream=False)
            if not ok:
                resp = BLOQUEIO_MSG
            else:
                req = urllib.request.Request(f"{OLLAMA_REAL_HOST}/api/generate", data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=180) as r:
                    resp = json.loads(r.read().decode("utf-8")).get("response", "").strip()
            if stream:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                cid = f"chatcmpl-{int(time.time())}"
                ev1 = {"id": cid, "object": "chat.completion.chunk", "created": int(time.time()), "model": modelo_req, "choices": [{"index": 0, "delta": {"role": "assistant", "content": resp}, "finish_reason": None}]}
                ev2 = {"id": cid, "object": "chat.completion.chunk", "created": int(time.time()), "model": modelo_req, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
                self.wfile.write(f"data: {json.dumps(ev1, ensure_ascii=False)}\n\n".encode("utf-8"))
                self.wfile.write(f"data: {json.dumps(ev2, ensure_ascii=False)}\n\n".encode("utf-8"))
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            else:
                _responder_json(self, 200, {
                    "id": f"chatcmpl-{int(time.time())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": modelo_req,
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": resp}, "finish_reason": "stop"}],
                })
            return

        _responder_json(self, 404, {"error": "endpoint não suportado"})


def main() -> int:
    ap = argparse.ArgumentParser(description="Proxy automático CVM compatível com Ollama (streaming) e OpenAI.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=11435)
    ap.add_argument("--modelo", default=consultar_cvm.MODELO_PADRAO)
    ap.add_argument("--num-gpu", type=int, default=NUM_GPU_PADRAO)
    args = ap.parse_args()

    CVMProxyHandler.modelo = args.modelo
    CVMProxyHandler.num_gpu = args.num_gpu
    server = ThreadingHTTPServer((args.host, args.port), CVMProxyHandler)
    print(f"[proxy-cvm] ativo em http://{args.host}:{args.port} -> Ollama real {OLLAMA_REAL_HOST} (modelo={args.modelo}, num_gpu={args.num_gpu})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[proxy-cvm] encerrado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
