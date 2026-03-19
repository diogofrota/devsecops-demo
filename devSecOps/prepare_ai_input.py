import json
import os
from pathlib import Path


def load_report(report_path: Path) -> dict:
    if not report_path.exists():
        raise FileNotFoundError(f"[ERRO] O relatorio {report_path} nao foi encontrado.")
    return json.loads(report_path.read_text(encoding="utf-8"))


def build_ai_input(report: dict) -> str:
    total = report.get("resumo", {}).get("total_achados", 0)
    status = report.get("resumo", {}).get("status", "sem status")
    findings = report.get("achados", [])

    lines = [
        "Voce e um agente DevSecOps especializado em analise de vulnerabilidades.",
        "Analise os achados abaixo e gere:",
        "1. resumo executivo",
        "2. classificacao de severidade",
        "3. explicacao do risco",
        "4. recomendacao de correcao",
        "5. conclusao final",
        "",
        f"Status da varredura: {status}",
        f"Total de achados: {total}",
        "",
    ]

    for item in findings:
        lines.append(
            f"- Tipo: {item['tipo']} | Arquivo: {item['arquivo']} | "
            f"Linha: {item['linha']} | Severidade: {item['severidade']}"
        )
        lines.append(f"  Trecho encontrado: {item['trecho']}")
        lines.append("")

    return "\n".join(lines)


def write_ai_input(content: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"[INFO] Entrada da IA salva em {output_path}")


def main() -> None:
    reports_dir = Path(os.getenv("REPORTS_DIR", "/tmp/security-reports"))
    report = load_report(reports_dir / "credential_report.json")
    ai_input = build_ai_input(report)
    write_ai_input(ai_input, reports_dir / "ai_input.txt")


if __name__ == "__main__":
    main()
