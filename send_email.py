import html
import json
import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path


def bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def add_attachment_if_exists(message: EmailMessage, path: Path) -> None:
    if not path.exists():
        return
    message.add_attachment(
        path.read_bytes(),
        maintype="application",
        subtype="octet-stream",
        filename=path.name,
    )


def build_overview(reports_dir: Path) -> dict:
    credential_report = load_json(reports_dir / "credential_report.json")
    cloud_report = load_json(reports_dir / "cloud_report.json")

    dev_findings = credential_report.get("resumo", {}).get("total_achados", 0)
    cloud_findings = cloud_report.get("summary", {}).get("total_findings", 0)
    cloud_status = cloud_report.get("summary", {}).get("status", "sem status")

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for item in cloud_report.get("findings", []):
        severity = str(item.get("severity", "")).lower()
        if severity in severity_counts:
            severity_counts[severity] += 1

    return {
        "dev_findings": dev_findings,
        "cloud_findings": cloud_findings,
        "total_findings": dev_findings + cloud_findings,
        "cloud_status": cloud_status,
        "severity_counts": severity_counts,
    }


def build_subject(overview: dict) -> str:
    default_subject = (
        f"Relatorio do Agente IA de Seguranca | "
        f"DevSecOps + Cloud ({overview['total_findings']} achados)"
    )
    custom_subject = os.getenv("EMAIL_SUBJECT", "").strip()
    return custom_subject or default_subject


def build_plain_body(reports_dir: Path, overview: dict) -> str:
    dev_report = read_text(reports_dir / "final_report.txt") or "Relatorio nao encontrado."
    cloud_report = read_text(reports_dir / "cloud_final_report.txt") or "Relatorio nao encontrado."

    return (
        "Relatorio consolidado da pipeline de seguranca\n\n"
        "Resumo Executivo\n"
        f"- Total de achados: {overview['total_findings']}\n"
        f"- DevSecOps: {overview['dev_findings']}\n"
        f"- Cloud Security: {overview['cloud_findings']}\n"
        f"- Cloud status: {overview['cloud_status']}\n"
        "- Severidade Cloud: "
        f"critical={overview['severity_counts']['critical']}, "
        f"high={overview['severity_counts']['high']}, "
        f"medium={overview['severity_counts']['medium']}, "
        f"low={overview['severity_counts']['low']}\n\n"
        "===== RELATORIO DEVSECOPS =====\n"
        f"{dev_report}\n\n"
        "===== RELATORIO CLOUD SECURITY =====\n"
        f"{cloud_report}\n"
    )


def severity_badges_html(severity_counts: dict) -> str:
    styles = {
        "critical": ("#7f1d1d", "#fecaca", "CRITICO"),
        "high": ("#78350f", "#fde68a", "ALTO"),
        "medium": ("#1e3a8a", "#bfdbfe", "MEDIO"),
        "low": ("#14532d", "#bbf7d0", "BAIXO"),
    }
    parts = []
    for key in ("critical", "high", "medium", "low"):
        bg, fg, label = styles[key]
        parts.append(
            f"<span style='display:inline-block;padding:6px 10px;border-radius:999px;"
            f"background:{bg};color:{fg};font-size:12px;font-weight:700;margin:2px;'>"
            f"{label}: {severity_counts[key]}</span>"
        )
    return "".join(parts)


def to_pre_html(content: str) -> str:
    if not content:
        return (
            "<div style='padding:10px;background:#0b1220;border:1px solid #23324a;"
            "border-radius:10px;color:#cbd5e1;'>Relatorio nao encontrado.</div>"
        )
    return (
        "<div style='padding:12px;background:#0b1220;border:1px solid #23324a;"
        "border-radius:10px;color:#cbd5e1;white-space:pre-wrap;line-height:1.55;'>"
        f"{html.escape(content)}"
        "</div>"
    )


def build_html_body(reports_dir: Path, overview: dict) -> str:
    dev_report = read_text(reports_dir / "final_report.txt")
    cloud_report = read_text(reports_dir / "cloud_final_report.txt")
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    badges = severity_badges_html(overview["severity_counts"])

    return f"""\
<!DOCTYPE html>
<html lang="pt-BR">
  <body style="margin:0;padding:24px;background:#0f172a;font-family:Arial,Helvetica,sans-serif;color:#e2e8f0;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:900px;margin:0 auto;">
      <tr>
        <td style="background:#111827;border:1px solid #23324a;border-radius:14px;padding:20px;">
          <h1 style="margin:0 0 8px;font-size:24px;color:#f8fafc;">Relatorio do Agente IA de Seguranca</h1>
          <p style="margin:0;color:#94a3b8;font-size:13px;">Pipeline DevSecOps + Cloud Security | {created_at}</p>
        </td>
      </tr>
      <tr><td style="height:12px;"></td></tr>
      <tr>
        <td style="background:#111827;border:1px solid #23324a;border-radius:14px;padding:18px;">
          <h2 style="margin:0 0 10px;font-size:18px;color:#f8fafc;">Resumo Executivo</h2>
          <p style="margin:0 0 8px;color:#cbd5e1;">
            Total de achados: <strong>{overview['total_findings']}</strong> |
            DevSecOps: <strong>{overview['dev_findings']}</strong> |
            Cloud Security: <strong>{overview['cloud_findings']}</strong>
          </p>
          <p style="margin:0 0 12px;color:#cbd5e1;">Status cloud: <strong>{html.escape(str(overview['cloud_status']))}</strong></p>
          <div>{badges}</div>
        </td>
      </tr>
      <tr><td style="height:12px;"></td></tr>
      <tr>
        <td style="background:#111827;border:1px solid #23324a;border-radius:14px;padding:18px;">
          <h2 style="margin:0 0 10px;font-size:18px;color:#f8fafc;">Analise IA - DevSecOps</h2>
          {to_pre_html(dev_report)}
        </td>
      </tr>
      <tr><td style="height:12px;"></td></tr>
      <tr>
        <td style="background:#111827;border:1px solid #23324a;border-radius:14px;padding:18px;">
          <h2 style="margin:0 0 10px;font-size:18px;color:#f8fafc;">Analise IA - Cloud Security</h2>
          {to_pre_html(cloud_report)}
        </td>
      </tr>
      <tr><td style="height:12px;"></td></tr>
      <tr>
        <td style="color:#94a3b8;font-size:12px;text-align:center;">
          Mensagem automatica da pipeline de seguranca.
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def main() -> None:
    email_user = os.getenv("EMAIL_USER", "").strip()
    email_password = os.getenv("EMAIL_PASSWORD", "").strip()
    email_to = os.getenv("EMAIL_TO", "").strip()

    if not all([email_user, email_password, email_to]):
        raise ValueError("[ERRO] EMAIL_USER, EMAIL_PASSWORD e EMAIL_TO sao obrigatorios.")

    reports_dir = Path(os.getenv("REPORTS_DIR", "/tmp/security-reports"))
    attach_reports = bool_env("EMAIL_ATTACH_REPORTS", default=False)
    overview = build_overview(reports_dir)

    msg = EmailMessage()
    msg["Subject"] = build_subject(overview)
    msg["From"] = email_user
    msg["To"] = email_to

    plain_body = build_plain_body(reports_dir, overview)
    html_body = build_html_body(reports_dir, overview)
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")

    if attach_reports:
        add_attachment_if_exists(msg, reports_dir / "final_report.txt")
        add_attachment_if_exists(msg, reports_dir / "cloud_final_report.txt")
        add_attachment_if_exists(msg, reports_dir / "credential_report.json")
        add_attachment_if_exists(msg, reports_dir / "cloud_report.json")
        print("[INFO] Anexos habilitados (EMAIL_ATTACH_REPORTS=true).")
    else:
        print("[INFO] Envio sem anexos (padrao).")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_user, email_password)
        smtp.send_message(msg)

    print(f"[INFO] E-mail enviado com sucesso! Assunto: {msg['Subject']}")


if __name__ == "__main__":
    main()
