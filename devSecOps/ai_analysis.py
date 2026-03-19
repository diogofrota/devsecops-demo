import os
import time
from pathlib import Path

from openai import OpenAI


def extract_response_text(response) -> str:
    if getattr(response, "output_text", None):
        return response.output_text

    chunks = []
    for item in response.output:
        for content in getattr(item, "content", []):
            text = getattr(getattr(content, "text", None), "value", None)
            if text:
                chunks.append(text)
            elif hasattr(content, "text") and isinstance(content.text, str):
                chunks.append(content.text)
    return "\n".join(chunks).strip()


def build_prompt(content: str) -> str:
    return f"""
Voce e um especialista em seguranca DevSecOps.

Analise o seguinte relatorio de vulnerabilidades:

{content}

Responda com:
1. Resumo executivo
2. Severidade
3. Explicacao do risco
4. Recomendacoes
5. Conclusao
"""


def extract_assistant_message(messages) -> str:
    for message in messages.data:
        if getattr(message, "role", "") != "assistant":
            continue
        parts = []
        for block in getattr(message, "content", []):
            if getattr(block, "type", "") == "text":
                block_text = getattr(getattr(block, "text", None), "value", None)
                if block_text:
                    parts.append(block_text)
        if parts:
            return "\n".join(parts).strip()
    return ""


def analyze_with_assistant(client: OpenAI, assistant_id: str, content: str) -> str:
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=build_prompt(content),
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )
    while run.status in {"queued", "in_progress"}:
        time.sleep(2)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    if run.status != "completed":
        raise RuntimeError(f"[ERRO] Execucao do assistant finalizou com status: {run.status}")

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    result = extract_assistant_message(messages)
    if not result:
        raise RuntimeError("[ERRO] O assistant nao retornou texto analisavel.")
    return result


def analyze_with_responses(client: OpenAI, content: str) -> str:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=build_prompt(content),
    )
    result = extract_response_text(response)
    if not result:
        raise RuntimeError("[ERRO] A API Responses nao retornou texto analisavel.")
    return result


def main() -> None:
    reports_dir = Path(os.getenv("REPORTS_DIR", "/tmp/security-reports"))
    input_path = reports_dir / "ai_input.txt"
    output_path = reports_dir / "final_report.txt"

    if not input_path.exists():
        raise FileNotFoundError(f"[ERRO] Arquivo {input_path} nao encontrado.")

    content = input_path.read_text(encoding="utf-8")
    assistant_id = os.getenv("DEVSECOPS_ASSISTANT_ID", "").strip()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    print("[INFO] Enviando dados para analise DevSecOps com IA...")
    if assistant_id:
        print("[INFO] Usando Assistant configurado via DEVSECOPS_ASSISTANT_ID.")
        try:
            result = analyze_with_assistant(client, assistant_id, content)
        except Exception as error:
            print(
                "[WARN] Falha ao usar Assistant. "
                f"Fallback para Responses API. Motivo: {error}"
            )
            result = analyze_with_responses(client, content)
    else:
        print("[INFO] DEVSECOPS_ASSISTANT_ID nao definido. Usando Responses API.")
        result = analyze_with_responses(client, content)

    reports_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8")

    print(f"[INFO] Analise DevSecOps concluida. Relatorio salvo em {output_path}")
    print(result)


if __name__ == "__main__":
    main()
