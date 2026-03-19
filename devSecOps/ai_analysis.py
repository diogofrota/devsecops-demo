import os
import time
import warnings
from pathlib import Path

from openai import OpenAI

warnings.filterwarnings(
    "ignore",
    message=r".*Assistants API is deprecated in favor of the Responses API.*",
    category=DeprecationWarning,
)


def log_step(message: str) -> None:
    print(f"[STEP] {message}")


def short_error_reason(error: Exception) -> str:
    message = str(error).replace("\n", " ")
    if "No assistant found" in message or "Error code: 404" in message:
        return "assistant nao encontrado para DEVSECOPS_ASSISTANT_ID"
    if isinstance(error, TimeoutError):
        return message or "assistant sem resposta"
    return error.__class__.__name__


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


def analyze_with_assistant(
    client: OpenAI,
    assistant_id: str,
    content: str,
    timeout_seconds: int = 120,
) -> str:
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
    started_at = time.time()
    while run.status in {"queued", "in_progress"}:
        if time.time() - started_at >= timeout_seconds:
            raise TimeoutError(
                f"assistant sem resposta apos {timeout_seconds}s"
            )
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
    assistant_timeout_seconds = int(
        os.getenv("DEVSECOPS_ASSISTANT_TIMEOUT_SECONDS", "120")
    )
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    log_step("Iniciando analise DevSecOps com IA")
    if assistant_id:
        log_step(
            "Tentando usar Assistant (DEVSECOPS_ASSISTANT_ID) "
            f"com timeout de {assistant_timeout_seconds}s"
        )
        try:
            result = analyze_with_assistant(
                client=client,
                assistant_id=assistant_id,
                content=content,
                timeout_seconds=assistant_timeout_seconds,
            )
            log_step("Analise concluida via Assistant")
        except Exception as error:
            log_step(
                "Assistant indisponivel; fallback para Responses API "
                f"({short_error_reason(error)})"
            )
            result = analyze_with_responses(client, content)
            log_step("Analise concluida via Responses API")
    else:
        log_step("DEVSECOPS_ASSISTANT_ID nao definido; usando Responses API")
        result = analyze_with_responses(client, content)
        log_step("Analise concluida via Responses API")

    reports_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8")
    log_step(f"Relatorio salvo em {output_path}")


if __name__ == "__main__":
    main()
