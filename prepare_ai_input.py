import json
from pathlib import Path

def main():
    report_path = Path("reports/credential_report.json")

    if not report_path.exists():
        print("[ERRO] O relatório reports/credential_report.json não foi encontrado.")
        return

    with open(report_path, "r", encoding="utf-8") as arquivo:
        relatorio = json.load(arquivo)

    total = relatorio.get("resumo", {}).get("total_achados", 0)
    status = relatorio.get("resumo", {}).get("status", "sem status")
    achados = relatorio.get("achados", [])

    linhas = []
    linhas.append("Você é um agente DevSecOps especializado em análise de vulnerabilidades.")
    linhas.append("Analise os achados abaixo e gere:")
    linhas.append("1. resumo executivo")
    linhas.append("2. classificação de severidade")
    linhas.append("3. explicação do risco")
    linhas.append("4. recomendação de correção")
    linhas.append("")
    linhas.append(f"Status da varredura: {status}")
    linhas.append(f"Total de achados: {total}")
    linhas.append("")

    for item in achados:
        linhas.append(
            f"- Tipo: {item['tipo']} | Arquivo: {item['arquivo']} | "
            f"Linha: {item['linha']} | Severidade: {item['severidade']}"
        )
        linhas.append(f"  Trecho encontrado: {item['trecho']}")
        linhas.append("")

    Path("reports").mkdir(exist_ok=True)

    with open("reports/ai_input.txt", "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas))

    print("[INFO] Arquivo de entrada para IA gerado com sucesso.")
    print("[INFO] Salvo em reports/ai_input.txt")

if __name__ == "__main__":
    main()