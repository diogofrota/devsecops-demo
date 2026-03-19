import os
from openai import OpenAI

def main():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    with open("reports/ai_input.txt", "r", encoding="utf-8") as f:
        content = f.read()

    prompt = f"""
Você é um especialista em segurança DevSecOps.

Analise o seguinte relatório de vulnerabilidades:

{content}

Responda com:
1. Resumo executivo
2. Severidade
3. Explicação do risco
4. Recomendações
5. Conclusão
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    result = response.output[0].content[0].text

    os.makedirs("reports", exist_ok=True)

    with open("reports/final_report.txt", "w", encoding="utf-8") as f:
        f.write(result)

    print("[INFO] Relatório final gerado com sucesso!")
    print(result)

if __name__ == "__main__":
    main()