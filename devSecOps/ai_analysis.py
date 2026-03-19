import os
from pathlib import Path

from openai import OpenAI


def extract_text(response) -> str:
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


def main() -> None:
    reports_dir = Path(os.getenv("REPORTS_DIR", "/tmp/security-reports"))
    input_path = reports_dir / "ai_input.txt"
    output_path = reports_dir / "final_report.txt"

    if not input_path.exists():
        raise FileNotFoundError(f"[ERRO] Arquivo {input_path} nao encontrado.")

    content = input_path.read_text(encoding="utf-8")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=build_prompt(content),
    )

    result = extract_text(response)
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8")

    print(f"[INFO] Relatorio final gerado com sucesso em {output_path}!")
    print(result)


if __name__ == "__main__":
    main()
