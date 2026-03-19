import json
import os
from pathlib import Path


def evaluate_resource(resource: dict) -> list[dict]:
    findings = []
    resource_type = resource.get("type")
    name = resource.get("name", "sem-nome")

    if resource_type == "s3_bucket":
        if resource.get("public_read") is True:
            findings.append(
                {
                    "resource": name,
                    "type": resource_type,
                    "issue": "Bucket com leitura publica habilitada",
                    "severity": "high",
                }
            )
        if resource.get("encryption_enabled") is False:
            findings.append(
                {
                    "resource": name,
                    "type": resource_type,
                    "issue": "Bucket sem criptografia habilitada",
                    "severity": "high",
                }
            )
        if resource.get("logging_enabled") is False:
            findings.append(
                {
                    "resource": name,
                    "type": resource_type,
                    "issue": "Bucket sem logging habilitado",
                    "severity": "medium",
                }
            )

    elif resource_type == "security_group":
        for rule in resource.get("inbound_rules", []):
            if rule.get("port") == 22 and rule.get("source") == "0.0.0.0/0":
                findings.append(
                    {
                        "resource": name,
                        "type": resource_type,
                        "issue": "SSH exposto para toda a internet",
                        "severity": "critical",
                    }
                )

    elif resource_type == "rds_instance":
        if resource.get("storage_encrypted") is False:
            findings.append(
                {
                    "resource": name,
                    "type": resource_type,
                    "issue": "Banco sem criptografia em repouso",
                    "severity": "high",
                }
            )
        if resource.get("public_access") is True:
            findings.append(
                {
                    "resource": name,
                    "type": resource_type,
                    "issue": "Banco com acesso publico habilitado",
                    "severity": "critical",
                }
            )
        if resource.get("backup_enabled") is False:
            findings.append(
                {
                    "resource": name,
                    "type": resource_type,
                    "issue": "Banco sem backup habilitado",
                    "severity": "medium",
                }
            )

    elif resource_type == "iam_user":
        if resource.get("mfa_enabled") is False:
            findings.append(
                {
                    "resource": name,
                    "type": resource_type,
                    "issue": "Usuario IAM sem MFA habilitado",
                    "severity": "high",
                }
            )
        if resource.get("admin_access") is True:
            findings.append(
                {
                    "resource": name,
                    "type": resource_type,
                    "issue": "Usuario IAM com privilegio administrativo",
                    "severity": "medium",
                }
            )
    return findings


def load_cloud_data(cloud_path: Path) -> dict:
    if not cloud_path.exists():
        raise FileNotFoundError(f"[ERRO] Arquivo {cloud_path} nao encontrado.")
    return json.loads(cloud_path.read_text(encoding="utf-8"))


def build_report(provider: str, findings: list[dict]) -> dict:
    return {
        "provider": provider,
        "summary": {
            "total_findings": len(findings),
            "status": "misconfigurations found" if findings else "no findings",
        },
        "findings": findings,
    }


def write_report(report: dict) -> None:
    reports_dir = Path(os.getenv("REPORTS_DIR", "/tmp/security-reports"))
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_path = reports_dir / "cloud_report.json"
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[INFO] Relatorio salvo em {output_path}")


def main() -> None:
    cloud_file = Path(os.getenv("CLOUD_CONFIG_FILE", "cloud/aws_mock.json"))
    data = load_cloud_data(cloud_file)

    provider = data.get("provider", "unknown")
    resources = data.get("resources", [])
    findings = []

    print(f"[INFO] Iniciando varredura CSPM no ambiente: {provider}")
    for resource in resources:
        findings.extend(evaluate_resource(resource))

    report = build_report(provider, findings)
    write_report(report)

    print(f"[INFO] Varredura CSPM finalizada. Total de achados: {len(findings)}")
    for item in findings:
        print(
            f"[ALERTA] Recurso: {item['resource']} | "
            f"Tipo: {item['type']} | Severidade: {item['severity']} | "
            f"Problema: {item['issue']}"
        )


if __name__ == "__main__":
    main()
