import json
import os
import re
from pathlib import Path

ALLOWED_EXTENSIONS = {".html", ".js", ".py", ".json", ".env", ".txt"}
SKIPPED_DIRECTORIES = {".git", "__pycache__", "reports"}

PATTERNS = [
    ("API_KEY", r"API_KEY\s*=\s*[\"'][^\"']+[\"']"),
    ("SECRET_KEY", r"SECRET_KEY\s*=\s*[\"'][^\"']+[\"']"),
    ("ACCESS_TOKEN", r"ACCESS_TOKEN\s*=\s*[\"'][^\"']+[\"']"),
    ("PASSWORD", r"PASSWORD\s*=\s*[\"'][^\"']+[\"']"),
]


def should_scan(path: Path) -> bool:
    return path.suffix.lower() in ALLOWED_EXTENSIONS


def should_skip(path: Path) -> bool:
    return any(part in SKIPPED_DIRECTORIES for part in path.parts)


def scan_file(path: Path) -> list[dict]:
    findings = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as error:
        print(f"[ERRO] Nao foi possivel ler {path}: {error}")
        return findings

    for line_number, line in enumerate(content.splitlines(), start=1):
        for pattern_name, pattern in PATTERNS:
            if re.search(pattern, line):
                findings.append(
                    {
                        "arquivo": str(path),
                        "linha": line_number,
                        "tipo": pattern_name,
                        "trecho": line.strip(),
                        "severidade": "alta",
                    }
                )
    return findings


def build_report(findings: list[dict]) -> dict:
    return {
        "resumo": {
            "total_achados": len(findings),
            "status": (
                "credenciais expostas encontradas" if findings else "nenhum achado"
            ),
        },
        "achados": findings,
    }


def write_report(report: dict) -> None:
    reports_dir = Path(os.getenv("REPORTS_DIR", "/tmp/security-reports"))
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_path = reports_dir / "credential_report.json"
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[INFO] Relatorio salvo em {output_path}")


def main() -> None:
    print("[INFO] Iniciando varredura de credenciais expostas...")
    all_findings = []

    for path in Path(".").rglob("*"):
        if not path.is_file() or should_skip(path) or not should_scan(path):
            continue
        file_findings = scan_file(path)
        for item in file_findings:
            all_findings.append(item)
            print(
                f"[ALERTA] Tipo: {item['tipo']} | Arquivo: {item['arquivo']} | "
                f"Linha: {item['linha']}"
            )

    report = build_report(all_findings)
    write_report(report)
    print(f"[INFO] Varredura finalizada. Total de achados: {len(all_findings)}")


if __name__ == "__main__":
    main()
